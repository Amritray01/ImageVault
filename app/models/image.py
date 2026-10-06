import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.tag import image_tags

def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    original_filename = Column(String(255), nullable=False)
    storage_filename = Column(String(255), unique=True, index=True, nullable=False)
    mime_type = Column(String(50), default="image/jpeg", nullable=False)
    format = Column(String(20), default="JPEG", nullable=False)
    
    # Dimensions
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    aspect_ratio = Column(Float, nullable=False)
    
    # Compression and Storage Metrics
    original_size_bytes = Column(Integer, nullable=False)
    compressed_size_bytes = Column(Integer, nullable=False)
    compression_ratio = Column(Float, nullable=False)
    savings_percent = Column(Float, nullable=False)
    jpeg_quality = Column(Integer, default=80, nullable=False)
    
    # Hashes & Deduplication
    sha256_hash = Column(String(64), index=True, nullable=False)
    phash = Column(String(32), index=True, nullable=False)
    
    # Storage Paths / S3 Keys
    storage_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=False)
    
    # Metadata & EXIF
    exif_stripped = Column(Boolean, default=True, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    
    # Timestamps (Naive UTC for asyncpg & PostgreSQL compatibility)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    
    # Relationships
    tags = relationship("Tag", secondary=image_tags, back_populates="images", lazy="selectin")
