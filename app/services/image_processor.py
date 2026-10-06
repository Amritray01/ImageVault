import io
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageOps, ExifTags
from app.config import settings

@dataclass(slots=True)
class ImageProcessingResult:
    jpeg_bytes: bytes
    thumbnail_bytes: bytes
    original_size: int
    compressed_size: int
    thumbnail_size: int
    width: int
    height: int
    aspect_ratio: float
    compression_ratio: float
    savings_percent: float
    jpeg_quality: int
    exif_stripped: bool
    metadata: Dict[str, Any]
    pil_image: Image.Image

def extract_exif_metadata(img: Image.Image) -> Tuple[Dict[str, Any], bool]:
    metadata: Dict[str, Any] = {
        "original_format": img.format or "UNKNOWN",
        "original_mode": img.mode,
        "color_space": "sRGB",
        "has_gps": False,
        "camera_make": None,
        "camera_model": None,
        "lens_model": None,
        "software": None,
        "date_time_original": None,
        "exposure_time": None,
        "f_number": None,
        "iso_speed": None,
        "focal_length": None,
        "sanitized_attributes": []
    }

    has_exif = False
    try:
        exif_data = img.getexif()
        if exif_data:
            has_exif = True
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if tag_name == "GPSInfo" or tag_id == 34853:
                    metadata["has_gps"] = True
                    metadata["sanitized_attributes"].append("GPS Geolocation (Lat/Lon/Alt)")
                elif tag_name == "Make":
                    metadata["camera_make"] = str(value).strip()
                elif tag_name == "Model":
                    metadata["camera_model"] = str(value).strip()
                elif tag_name == "Software":
                    metadata["software"] = str(value).strip()
                elif tag_name in ("DateTime", "DateTimeOriginal"):
                    metadata["date_time_original"] = str(value).strip()

            try:
                exif_ifd = exif_data.get_ifd(ExifTags.IFD.Exif)
                if exif_ifd:
                    if 33434 in exif_ifd:
                        exp = exif_ifd[33434]
                        metadata["exposure_time"] = f"{float(exp):.4f}s" if isinstance(exp, (int, float)) else str(exp)
                    if 33437 in exif_ifd:
                        fn = exif_ifd[33437]
                        metadata["f_number"] = f"f/{float(fn):.1f}" if isinstance(fn, (int, float)) else str(fn)
                    if 34855 in exif_ifd:
                        metadata["iso_speed"] = str(exif_ifd[34855])
                    if 37386 in exif_ifd:
                        fl = exif_ifd[37386]
                        metadata["focal_length"] = f"{float(fl):.1f}mm" if isinstance(fl, (int, float)) else str(fl)
                    if 42036 in exif_ifd:
                        metadata["lens_model"] = str(exif_ifd[42036]).strip()
                    if 36867 in exif_ifd and not metadata["date_time_original"]:
                        metadata["date_time_original"] = str(exif_ifd[36867]).strip()
            except Exception:
                pass

            try:
                gps_ifd = exif_data.get_ifd(ExifTags.IFD.GPSInfo)
                if gps_ifd:
                    metadata["has_gps"] = True
                    if "GPS Geolocation (Lat/Lon/Alt)" not in metadata["sanitized_attributes"]:
                        metadata["sanitized_attributes"].append("GPS Geolocation (Lat/Lon/Alt)")
            except Exception:
                pass
    except Exception:
        has_exif = False

    if has_exif:
        metadata["sanitized_attributes"].extend([
            "Device Serial Numbers", 
            "Owner/Author Info", 
            "Thumbnail Sub-streams",
            "Color Calibration Profiles"
        ])
        
    return metadata, has_exif

def process_and_compress_image(
    file_bytes: bytes,
    quality: Optional[int] = None,
    max_dimension: Optional[int] = None
) -> ImageProcessingResult:
    quality = quality or settings.DEFAULT_JPEG_QUALITY
    max_dimension = max_dimension or settings.MAX_IMAGE_DIMENSION
    original_size = len(file_bytes)

    img = Image.open(io.BytesIO(file_bytes))
    metadata, had_exif = extract_exif_metadata(img)
    img = ImageOps.exif_transpose(img)
    
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA"):
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    if width > max_dimension or height > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        width, height = img.size

    aspect_ratio = round(width / max(1, height), 4)

    jpeg_buffer = io.BytesIO()
    img.save(
        jpeg_buffer,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=settings.ENABLE_PROGRESSIVE_JPEG,
        subsampling=1
    )
    jpeg_bytes = jpeg_buffer.getvalue()
    compressed_size = len(jpeg_bytes)

    thumb_img = img.copy()
    thumb_img.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    thumb_buffer = io.BytesIO()
    thumb_img.save(
        thumb_buffer,
        format="JPEG",
        quality=75,
        optimize=True,
        progressive=False
    )
    thumb_bytes = thumb_buffer.getvalue()
    thumbnail_size = len(thumb_bytes)

    savings_bytes = max(0, original_size - compressed_size)
    savings_percent = round((savings_bytes / max(1, original_size)) * 100, 2)
    compression_ratio = round(original_size / max(1, compressed_size), 2)

    return ImageProcessingResult(
        jpeg_bytes=jpeg_bytes,
        thumbnail_bytes=thumb_bytes,
        original_size=original_size,
        compressed_size=compressed_size,
        thumbnail_size=thumbnail_size,
        width=width,
        height=height,
        aspect_ratio=aspect_ratio,
        compression_ratio=compression_ratio,
        savings_percent=savings_percent,
        jpeg_quality=quality,
        exif_stripped=had_exif,
        metadata=metadata,
        pil_image=img
    )
