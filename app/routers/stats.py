from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.image import Image
from app.models.tag import Tag
from app.schemas.image import ImageStatsResponse

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("", response_model=ImageStatsResponse)
async def get_storage_stats(db: AsyncSession = Depends(get_db)):
    """Retrieve aggregate compression metrics, space savings, and total records."""
    img_stmt = select(
        func.count(Image.id).label("total_images"),
        func.sum(Image.original_size_bytes).label("total_original"),
        func.sum(Image.compressed_size_bytes).label("total_compressed"),
        func.avg(Image.savings_percent).label("avg_savings")
    )
    img_res = (await db.execute(img_stmt)).first()
    
    total_images = img_res.total_images or 0
    total_original = img_res.total_original or 0
    total_compressed = img_res.total_compressed or 0
    total_saved = max(0, total_original - total_compressed)
    avg_savings = round(float(img_res.avg_savings or 0.0), 2)
    
    tag_count_stmt = select(func.count(Tag.id))
    tag_count = (await db.execute(tag_count_stmt)).scalar() or 0
    
    # Format distribution
    format_stmt = select(Image.format, func.count(Image.id)).group_by(Image.format)
    format_rows = (await db.execute(format_stmt)).all()
    formats_distribution = {row[0]: row[1] for row in format_rows}

    return ImageStatsResponse(
        total_images=total_images,
        total_original_bytes=total_original,
        total_compressed_bytes=total_compressed,
        total_bytes_saved=total_saved,
        average_savings_percent=avg_savings,
        total_tags=tag_count,
        formats_distribution=formats_distribution
    )
