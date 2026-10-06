import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.config import settings
from app.models.image import Image
from app.models.tag import Tag
from app.schemas.image import ImageResponse, ImageUploadResponse, ImageUpdate
from app.services.hasher import compute_sha256, compute_phash, hamming_distance
from app.services.image_processor import process_and_compress_image
from app.services.storage import storage_service

router = APIRouter(prefix="/api/images", tags=["Images"])

@router.post("/upload", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    quality: Optional[int] = Form(None),
    force_upload: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413, 
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    sha256 = compute_sha256(file_bytes)

    existing_exact = await db.execute(
        select(Image).options(selectinload(Image.tags)).where(Image.sha256_hash == sha256)
    )
    exact_match = existing_exact.scalars().first()

    if exact_match and not force_upload:
        return ImageUploadResponse(
            success=True,
            is_duplicate=True,
            duplicate_type="exact",
            message="Exact identical file already exists in ImageVault (SHA-256 match).",
            image=ImageResponse.model_validate(exact_match),
            similar_images=[]
        )

    try:
        proc_result = process_and_compress_image(
            file_bytes=file_bytes,
            quality=quality or settings.DEFAULT_JPEG_QUALITY
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process image with Pillow: {str(e)}")

    phash_val = compute_phash(proc_result.pil_image)

    all_images_stmt = select(Image).options(selectinload(Image.tags)).order_by(desc(Image.created_at)).limit(200)
    existing_all = (await db.execute(all_images_stmt)).scalars().all()
    
    similar_records = [
        ImageResponse.model_validate(past_img)
        for past_img in existing_all
        if hamming_distance(phash_val, past_img.phash) <= settings.PHASH_SIMILARITY_THRESHOLD
    ]

    storage_filename = f"{uuid.uuid4().hex}.jpg"
    img_key, thumb_key = await storage_service.save_image_and_thumbnail(
        storage_filename=storage_filename,
        jpeg_bytes=proc_result.jpeg_bytes,
        thumbnail_bytes=proc_result.thumbnail_bytes
    )

    tag_models = []
    if tags:
        tag_names = [t.strip() for t in tags.split(",") if t.strip()]
        for t_name in tag_names:
            tag_stmt = select(Tag).where(func.lower(Tag.name) == t_name.lower())
            existing_tag = (await db.execute(tag_stmt)).scalars().first()
            if not existing_tag:
                existing_tag = Tag(name=t_name)
                db.add(existing_tag)
                await db.flush()
            tag_models.append(existing_tag)

    new_image = Image(
        title=title or file.filename,
        description=description,
        original_filename=file.filename or "uploaded.jpg",
        storage_filename=storage_filename,
        mime_type="image/jpeg",
        format="JPEG",
        width=proc_result.width,
        height=proc_result.height,
        aspect_ratio=proc_result.aspect_ratio,
        original_size_bytes=proc_result.original_size,
        compressed_size_bytes=proc_result.compressed_size,
        compression_ratio=proc_result.compression_ratio,
        savings_percent=proc_result.savings_percent,
        jpeg_quality=proc_result.jpeg_quality,
        sha256_hash=sha256,
        phash=phash_val,
        storage_path=img_key,
        thumbnail_path=thumb_key,
        exif_stripped=proc_result.exif_stripped,
        metadata_json=proc_result.metadata,
        tags=tag_models
    )

    db.add(new_image)
    await db.commit()
    await db.refresh(new_image)

    is_visual_duplicate = len(similar_records) > 0
    msg = "Image successfully compressed to JPEG, sanitized, and stored."
    if is_visual_duplicate:
        msg += f" (Note: {len(similar_records)} visually similar images found)."

    return ImageUploadResponse(
        success=True,
        is_duplicate=is_visual_duplicate,
        duplicate_type="visual_similar" if is_visual_duplicate else None,
        message=msg,
        image=ImageResponse.model_validate(new_image),
        similar_images=similar_records
    )

@router.get("", response_model=List[ImageResponse])
async def list_images(
    q: Optional[str] = Query(None, description="Search by title, description, or filename"),
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    sort_by: str = Query("date_desc", pattern="^(date_desc|date_asc|size_desc|savings_desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Image).options(selectinload(Image.tags))

    if q:
        search_filter = or_(
            Image.title.ilike(f"%{q}%"),
            Image.description.ilike(f"%{q}%"),
            Image.original_filename.ilike(f"%{q}%")
        )
        stmt = stmt.where(search_filter)

    if tag:
        stmt = stmt.join(Image.tags).where(func.lower(Tag.name) == tag.lower())

    if sort_by == "date_desc":
        stmt = stmt.order_by(desc(Image.created_at))
    elif sort_by == "date_asc":
        stmt = stmt.order_by(asc(Image.created_at))
    elif sort_by == "size_desc":
        stmt = stmt.order_by(desc(Image.compressed_size_bytes))
    elif sort_by == "savings_desc":
        stmt = stmt.order_by(desc(Image.savings_percent))

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    images = result.scalars().all()
    return [ImageResponse.model_validate(img) for img in images]

@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Image).options(selectinload(Image.tags)).where(Image.id == image_id)
    img = (await db.execute(stmt)).scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found.")
    return ImageResponse.model_validate(img)

@router.get("/{image_id}/file")
async def get_image_file(image_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Image).where(Image.id == image_id)
    img = (await db.execute(stmt)).scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found.")

    file_bytes = await storage_service.get_file_bytes(img.storage_path)
    if not file_bytes:
        raise HTTPException(status_code=404, detail="Image file missing from storage.")

    return Response(
        content=file_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="{img.storage_filename}"'
        }
    )

@router.get("/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Image).where(Image.id == image_id)
    img = (await db.execute(stmt)).scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Thumbnail not found.")

    file_bytes = await storage_service.get_file_bytes(img.thumbnail_path)
    if not file_bytes:
        raise HTTPException(status_code=404, detail="Thumbnail missing from storage.")

    return Response(
        content=file_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="thumb_{img.storage_filename}"'
        }
    )

@router.get("/{image_id}/download")
async def download_image(image_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Image).where(Image.id == image_id)
    img = (await db.execute(stmt)).scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found.")

    file_bytes = await storage_service.get_file_bytes(img.storage_path)
    if not file_bytes:
        raise HTTPException(status_code=404, detail="Image file missing from storage.")

    base_name = img.original_filename.rsplit(".", 1)[0]
    download_name = f"{base_name}_optimized.jpg"

    return Response(
        content=file_bytes,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"'
        }
    )

@router.get("/{image_id}/similar", response_model=List[ImageResponse])
async def get_similar_images(
    image_id: int, 
    threshold: int = Query(settings.PHASH_SIMILARITY_THRESHOLD, ge=0, le=64),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Image).options(selectinload(Image.tags)).where(Image.id == image_id)
    target_img = (await db.execute(stmt)).scalars().first()
    if not target_img:
        raise HTTPException(status_code=404, detail="Target image not found.")

    all_stmt = select(Image).options(selectinload(Image.tags)).where(Image.id != image_id)
    all_images = (await db.execute(all_stmt)).scalars().all()

    return [
        ImageResponse.model_validate(other)
        for other in all_images
        if hamming_distance(target_img.phash, other.phash) <= threshold
    ]

@router.patch("/{image_id}", response_model=ImageResponse)
async def update_image(
    image_id: int,
    payload: ImageUpdate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Image).options(selectinload(Image.tags)).where(Image.id == image_id)
    img = (await db.execute(stmt)).scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found.")

    if payload.title is not None:
        img.title = payload.title
    if payload.description is not None:
        img.description = payload.description

    if payload.tags is not None:
        tag_models = []
        for t_name in payload.tags:
            t_name = t_name.strip()
            if not t_name:
                continue
            t_stmt = select(Tag).where(func.lower(Tag.name) == t_name.lower())
            tag_obj = (await db.execute(t_stmt)).scalars().first()
            if not tag_obj:
                tag_obj = Tag(name=t_name)
                db.add(tag_obj)
                await db.flush()
            tag_models.append(tag_obj)
        img.tags = tag_models

    await db.commit()
    await db.refresh(img)
    return ImageResponse.model_validate(img)

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Image).where(Image.id == image_id)
    img = (await db.execute(stmt)).scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found.")

    await storage_service.delete_file(img.storage_path)
    await storage_service.delete_file(img.thumbnail_path)

    await db.delete(img)
    await db.commit()
    return None
