# ImageVault — Image Storage & Processing Service

> **High-performance microservice built with FastAPI, Pillow, PostgreSQL, and AWS S3/MinIO for automated JPEG compression, EXIF metadata sanitization, and dual cryptographic & perceptual hashing.**

---

## Architecture Overview

```
                        ┌──────────────────────────────────────────────┐
                        │      Client (SPA Frontend / REST API)       │
                        └──────────────────────┬───────────────────────┘
                                               │ Multipart /api/images/upload
                                               ▼
                        ┌──────────────────────────────────────────────┐
                        │           FastAPI Gateway Router             │
                        │     (Schema Validation & Size Checks)        │
                        └──────────────────────┬───────────────────────┘
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               ▼                                                               ▼
┌─────────────────────────────┐                                 ┌─────────────────────────────┐
│    1. SHA-256 Digest        │                                 │   2. Pillow Engine          │
│ • Exact Duplicate Detection │                                 │ • Auto-orient (EXIF Transpose)│
│ • S3 ETag/Integrity Checks  │                                 │ • EXIF Privacy Sanitization │
└──────────────┬──────────────┘                                 │ • Progressive JPEG Encoding │
               │                                                │ • Thumbnail Generation      │
               │                                                └──────────────┬──────────────┘
               │                                                               │
               │                                                               ▼
               │                                                ┌─────────────────────────────┐
               │                                                │   3. 2D DCT pHash           │
               │                                                │ • 64-bit Perceptual Hash    │
               │                                                │ • Hamming Distance Matching │
               └───────────────────────────────┬────────────────┴─────────────────────────────┘
                                               │
                                               ▼
                        ┌──────────────────────────────────────────────┐
                        │            Persistence & Storage             │
                        ├──────────────────────────────┬───────────────┤
                        │ PostgreSQL Database (Async)  │ AWS S3 Bucket │
                        │ • Image Metadata & EXIF JSON │ • Stored JPEGs│
                        │ • Tags & Structured Queries  │ • Thumbnails  │
                        │ • SHA-256 & pHash Indexes    │               │
                        └──────────────────────────────┴───────────────┘
```

---

## Key Features

1. **Automated Pillow JPEG Pipeline**:
   - Converts any format (PNG, WebP, TIFF, BMP) into standardized, progressive **JPEG**.
   - Configurable quality slider (40%–95%) with Huffman table optimization and 4:2:0 chroma subsampling.
   - Generates crisp 300x300 thumbnails for fast gallery grid loading.

2. **Metadata Sanitization & Privacy Shield**:
   - Extracts technical camera settings (Make, Model, Lens, Capture Date, Exposure, ISO, Focal Length) into structured JSON.
   - Strips sensitive EXIF tags (GPS Geolocation Coordinates, Device Serial Numbers, Author details) before saving to S3.

3. **Dual Hashing Deduplication Engine**:
   - **SHA-256 (Cryptographic Digest)**: Instant $O(1)$ lookup for bit-for-bit duplicate files.
   - **pHash (2D DCT Perceptual Hash)**: 64-bit frequency hash to identify visually similar, re-compressed, or cropped images using **Hamming distance** ($\le 6$).

4. **Interactive Glassmorphic Web Dashboard**:
   - Live drag-and-drop uploader with real-time compression savings calculator.
   - Tag management, structured search, and multi-criteria sorting.
   - Deep EXIF and hash inspector modal.
   - Aggregate storage savings & bandwidth analytics.

5. **Production Dockerization & CI/CD**:
   - Multi-stage `Dockerfile` with optimized runtime size.
   - `docker-compose.yml` including FastAPI, PostgreSQL 16, and MinIO (local S3).
   - GitHub Actions CI workflow for test execution and container verification.

---

## Directory Structure

```
ImageVault/
├── app/
│   ├── main.py                  # FastAPI application entry point, CORS & lifespan
│   ├── config.py                # Pydantic BaseSettings (S3, DB, compression defaults)
│   ├── database.py              # Async SQLAlchemy engine, session maker & init_db
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── image.py             # Image model (hashes, savings, dimensions, EXIF JSON)
│   │   └── tag.py               # Tag model and Many-to-Many association
│   ├── schemas/                 # Pydantic v2 validation models (Request/Response)
│   │   ├── image.py
│   │   └── tag.py
│   ├── services/
│   │   ├── image_processor.py   # Pillow engine: JPEG conversion, EXIF extraction/stripping
│   │   ├── hasher.py            # SHA-256 cryptographic digest & 2D DCT pHash
│   │   └── storage.py           # Unified Storage provider (AWS S3, MinIO, Local filesystem)
│   ├── routers/
│   │   ├── images.py            # Upload, query, inspect, download, delete endpoints
│   │   ├── tags.py              # Tag management endpoints
│   │   └── stats.py             # Storage reduction analytics endpoint
│   └── static/                  # Glassmorphic Frontend Single Page App
│       ├── index.html           # Dashboard UI
│       ├── style.css            # Dark mode theme & animations
│       └── app.js               # Frontend controller & drag-drop logic
├── tests/
│   ├── conftest.py              # Fixtures for in-memory image generation
│   ├── test_processor.py        # Pillow compression tests
│   ├── test_hasher.py           # SHA-256 and pHash unit tests
│   └── test_api.py              # FastAPI endpoint integration tests
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow
├── Dockerfile                   # Multi-stage production container build
├── docker-compose.yml           # Multi-container orchestration (FastAPI + Postgres + MinIO)
├── requirements.txt             # Python dependencies
├── run.py                       # Local one-click runner
└── README.md                    # Project documentation
```

---

## Quick Start Guide

### 1. Local Run (Zero Setup SQLite & Local Storage)

```bash
# Clone & enter directory
cd ImageVault

# Create and activate virtual environment
# On Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# On macOS/Linux:
# python3 -m venv .venv
# source .venv/bin/activate

# Install dependencies into virtual environment
pip install -r requirements.txt

# Run the app
python run.py
```
- Open UI: **`http://localhost:8000`**
- Interactive Swagger API: **`http://localhost:8000/docs`**

---

### 2. Production Docker Deployment (AWS S3 + PostgreSQL)

Provide your AWS credentials in `.env`:
```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID= KEY_ID
AWS_SECRET_ACCESS_KEY=ACCESS_KEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=my-imagevault-bucket
```

Run the production containers:
```bash
docker compose up -d --build
```
- **FastAPI API & Web UI**: `http://localhost:8000`
- **PostgreSQL Database**: `localhost:5432`
- **Object Storage**: Stored directly into your **AWS S3 Bucket**

---

### 3. Run Test Suite

```bash
pytest -v
```
