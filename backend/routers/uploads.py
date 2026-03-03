"""Photo and file upload router.

Endpoints:
  POST /api/v1/uploads/photos            – Upload a photo or file
  GET  /api/v1/uploads/photos            – List uploaded photos
  GET  /api/v1/uploads/photos/{id}       – Get photo metadata
  GET  /api/v1/uploads/photos/{id}/file  – Download the file
  DELETE /api/v1/uploads/photos/{id}     – Delete a photo and its file
"""

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import UploadedPhoto
from backend.schemas.intel import UploadedPhotoRead

logger = logging.getLogger("contractghost.uploads")

router = APIRouter(prefix="/uploads", tags=["Uploads"])

# Storage directory – use /tmp in CI/test, configurable via env
_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
_MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
_ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "image/svg+xml",
}


def _safe_filename(original: str) -> str:
    """Generate a safe, unique filename preserving the original extension."""
    ext = Path(original).suffix.lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".svg"}
    if ext not in allowed_exts:
        ext = ".bin"
    return f"{uuid.uuid4().hex}{ext}"


@router.post(
    "/photos",
    response_model=UploadedPhotoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a photo or document",
)
async def upload_photo(
    file: UploadFile = File(...),
    alt_text: str | None = Form(None),
    company_intel_id: int | None = Form(None),
    bid_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a photo, project image, or PDF document.

    Files are stored locally under the UPLOAD_DIR path.
    In production, replace local storage with S3-signed URL upload.
    """
    if file.content_type and file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(_ALLOWED_TYPES)}",
        )

    content = await file.read()
    if len(content) > _MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {_MAX_SIZE_BYTES // (1024*1024)} MB",
        )

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_filename(file.filename or "upload.bin")
    dest = _UPLOAD_DIR / safe_name

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    photo = UploadedPhoto(
        filename=safe_name,
        original_filename=file.filename or safe_name,
        storage_path=str(dest),
        content_type=file.content_type,
        size_bytes=len(content),
        alt_text=alt_text,
        company_intel_id=company_intel_id,
        bid_id=bid_id,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    logger.info("Uploaded file %s (%d bytes)", safe_name, len(content))
    return photo


@router.get("/photos", response_model=list[UploadedPhotoRead], summary="List uploaded photos")
def list_photos(
    company_intel_id: int | None = None,
    bid_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(UploadedPhoto).order_by(UploadedPhoto.uploaded_at.desc())
    if company_intel_id is not None:
        q = q.filter(UploadedPhoto.company_intel_id == company_intel_id)
    if bid_id is not None:
        q = q.filter(UploadedPhoto.bid_id == bid_id)
    return q.offset(skip).limit(limit).all()


@router.get("/photos/{photo_id}", response_model=UploadedPhotoRead, summary="Get photo metadata")
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    obj = db.get(UploadedPhoto, photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")
    return obj


@router.get(
    "/photos/{photo_id}/file",
    summary="Download a photo file",
    response_class=FileResponse,
)
def download_photo(photo_id: int, db: Session = Depends(get_db)):
    obj = db.get(UploadedPhoto, photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")
    path = Path(obj.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        path=str(path),
        media_type=obj.content_type or "application/octet-stream",
        filename=obj.original_filename,
    )


@router.delete(
    "/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a photo",
)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    obj = db.get(UploadedPhoto, photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")
    path = Path(obj.storage_path)
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", path, exc)
    db.delete(obj)
    db.commit()
