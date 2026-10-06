from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.tag import Tag, image_tags
from app.schemas.tag import TagResponse, TagCreate

router = APIRouter(prefix="/api/tags", tags=["Tags"])

@router.get("", response_model=List[dict])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """List all tags with associated image count."""
    stmt = (
        select(Tag.id, Tag.name, Tag.color, func.count(image_tags.c.image_id).label("image_count"))
        .outerjoin(image_tags, Tag.id == image_tags.c.tag_id)
        .group_by(Tag.id, Tag.name, Tag.color)
        .order_by(Tag.name)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {"id": row.id, "name": row.name, "color": row.color, "image_count": row.image_count}
        for row in rows
    ]

@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tag."""
    stmt = select(Tag).where(func.lower(Tag.name) == payload.name.lower())
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        return existing

    tag = Tag(name=payload.name.strip(), color=payload.color or "#6366f1")
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a tag."""
    stmt = select(Tag).where(Tag.id == tag_id)
    tag = (await db.execute(stmt)).scalars().first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found.")
    await db.delete(tag)
    await db.commit()
    return None
