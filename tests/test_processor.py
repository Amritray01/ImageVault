from app.services.image_processor import process_and_compress_image
from PIL import Image
import io

def test_process_rgb_image_compression(sample_rgb_image_bytes):
    result = process_and_compress_image(sample_rgb_image_bytes, quality=80)
    
    assert result.jpeg_bytes is not None
    assert len(result.jpeg_bytes) > 0
    assert result.width == 800
    assert result.height == 600
    assert result.compression_ratio > 0
    
    # Verify the output is valid JPEG
    out_img = Image.open(io.BytesIO(result.jpeg_bytes))
    assert out_img.format == "JPEG"

def test_process_rgba_transparency_handling(sample_rgba_image_bytes):
    # RGBA PNG should convert to JPEG smoothly without crashing
    result = process_and_compress_image(sample_rgba_image_bytes, quality=75)
    
    assert result.jpeg_bytes is not None
    assert result.width == 500
    assert result.height == 500
    
    out_img = Image.open(io.BytesIO(result.jpeg_bytes))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"

def test_thumbnail_generation(sample_rgb_image_bytes):
    result = process_and_compress_image(sample_rgb_image_bytes)
    
    thumb = Image.open(io.BytesIO(result.thumbnail_bytes))
    assert thumb.format == "JPEG"
    assert thumb.width <= 300
    assert thumb.height <= 300
