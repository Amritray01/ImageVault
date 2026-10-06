import pytest
import io
import os
from PIL import Image
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base, get_db
from app.main import app

from app.services.storage import storage_service

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(autouse=True)
async def prepare_environment():
    # Force local storage during tests
    prev_backend = storage_service.backend
    prev_client = storage_service.s3_client
    storage_service.backend = "local"
    storage_service.s3_client = None
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
            
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    storage_service.backend = prev_backend
    storage_service.s3_client = prev_client

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
