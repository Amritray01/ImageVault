import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ImageVault"

@pytest.mark.asyncio
async def test_upload_and_retrieve_flow(sample_rgb_image_bytes):
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Upload image
        files = {"file": ("test_banner.png", sample_rgb_image_bytes, "image/png")}
        data = {
            "title": "Test Banner",
            "description": "Integration test image",
            "tags": "test, automated, unit",
            "quality": 80
        }
        res = await ac.post("/api/images/upload", files=files, data=data)
        assert res.status_code == 201
        upload_data = res.json()
        assert upload_data["success"] is True
        image_id = upload_data["image"]["id"]

        # 2. Retrieve image details
        get_res = await ac.get(f"/api/images/{image_id}")
        assert get_res.status_code == 200
        img_info = get_res.json()
        assert img_info["title"] == "Test Banner"
        assert img_info["format"] == "JPEG"
        assert len(img_info["tags"]) == 3

        # 3. Retrieve stats
        stats_res = await ac.get("/api/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_images"] >= 1
