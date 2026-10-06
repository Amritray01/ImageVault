import pytest
import io
from PIL import Image
import os

@pytest.fixture(autouse=True)
def clean_test_env():
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["STORAGE_BACKEND"] = "local"
    yield

@pytest.fixture
def sample_rgb_image_bytes() -> bytes:
    img = Image.new("RGB", (800, 600), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@pytest.fixture
def sample_rgba_image_bytes() -> bytes:
    img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
