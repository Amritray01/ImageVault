from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.tag import TagResponse

class ImageBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class ImageUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class ImageResponse(ImageBase):
    id: int
    original_filename: str
    storage_filename: str
    mime_type: str
    format: str
    width: int
    height: int
    aspect_ratio: float
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    savings_percent: float
    jpeg_quality: int
    sha256_hash: str
    phash: str
    storage_path: str
    thumbnail_path: str
    exif_stripped: bool
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def image_url(self) -> str:
        return f"/api/images/{self.id}/file"

    @computed_field
    @property
    def thumbnail_url(self) -> str:
        return f"/api/images/{self.id}/thumbnail"

class ImageUploadResponse(BaseModel):
    success: bool
    is_duplicate: bool
    duplicate_type: Optional[str] = None
    message: str
    image: ImageResponse
    similar_images: Optional[List[ImageResponse]] = None

class ImageStatsResponse(BaseModel):
    total_images: int
    total_original_bytes: int
    total_compressed_bytes: int
    total_bytes_saved: int
    average_savings_percent: float
    total_tags: int
    formats_distribution: Dict[str, int]
