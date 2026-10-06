import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "ImageVault"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Storage Configuration (AWS S3 / MinIO / Local Fallback)
    STORAGE_BACKEND: str = "local"  # "s3" or "local"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "imagevault-prod-storage"
    S3_ENDPOINT_URL: Optional[str] = None  # e.g. for MinIO: http://localhost:9000
    
    # Local Storage Directory (used when STORAGE_BACKEND is "local")
    LOCAL_STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage_data")
    
    # Database Configuration (PostgreSQL in production/Docker, SQLite default for zero-config local dev)
    DATABASE_URL: str = "sqlite+aiosqlite:///./imagevault.db"
    
    # Image Compression & Processing Defaults
    DEFAULT_JPEG_QUALITY: int = 80
    ENABLE_PROGRESSIVE_JPEG: bool = True
    MAX_IMAGE_DIMENSION: int = 2560
    THUMBNAIL_SIZE: tuple[int, int] = (300, 300)
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # Security / Duplicate detection threshold
    PHASH_SIMILARITY_THRESHOLD: int = 6  # Hamming distance <= 6 is considered near-duplicate
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
