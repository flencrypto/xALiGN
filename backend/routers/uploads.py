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

logger = logging.getLogger("align.uploads")

router = APIRouter(prefix="/uploads", tags=["Uploads"])

# Storage directory – use /tmp in CI/test, configurable via env
_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
_MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
_ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "image/svg+xml",
}
_ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".svg"}


def _safe_filename(original: str) -> str:
    """Generate a safe, unique filename preserving the original extension."""
    ext = Path(original).name.rsplit(".", 1)
    ext = ("." + ext[-1].lower()) if len(ext) == 2 else ""
    if ext not in _ALLOWED_EXTS:
        ext = ".bin"
    return f"{uuid.uuid4().hex}{ext}"


def _resolve_upload_path(obj) -> Path | None:
    """Safely resolve the on-disk path for an uploaded file record.

    Strategy (in order):
    1. If ``storage_path`` is set, resolve it and verify it remains within
       ``_UPLOAD_DIR`` via ``Path.relative_to()``.  If valid *and* the file
       exists, use it.  This preserves compatibility with existing records
       while catching tampered paths.
    2. Fall back to reconstructing the path from ``filename`` (the UUID-based
       safe name stored at upload time) within the current ``_UPLOAD_DIR``.
       This handles the case where ``UPLOAD_DIR`` has changed between writes
       and reads, or where ``storage_path`` pointed outside the directory.

    Returns the resolved ``Path`` if the file exists, otherwise ``None``.
    """
    upload_dir = _UPLOAD_DIR.resolve()

    # Attempt 1: trust storage_path after containment check
    if obj.storage_path:
        try:
            candidate = Path(obj.storage_path).resolve()
            candidate.relative_to(upload_dir)  # raises ValueError if outside
            if candidate.exists():
                return candidate
        except (ValueError, OSError):
            pass

    # Attempt 2: reconstruct from the safe filename
    # Path.name strips all directory components (e.g. "../../etc/passwd" → "passwd"),
    # so this is safe against path traversal in obj.filename.
    safe_name = Path(obj.filename).name
    fallback = (upload_dir / safe_name).resolve()
    try:
        fallback.relative_to(upload_dir)  # extra safety guard
    except ValueError:
        return None
    return fallback if fallback.exists() else None


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
    # Validate by content_type when provided; fall back to extension check
    # when the client does not supply a MIME type.
    original_name = file.filename or "upload.bin"
    ext = ("." + original_name.rsplit(".", 1)[-1].lower()) if "." in original_name else ""
    if file.content_type:
        if file.content_type not in _ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(sorted(_ALLOWED_TYPES))}",
            )
    else:
        # No content-type header – validate by file extension as a fallback.
        if ext not in _ALLOWED_EXTS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension: {ext!r}. Allowed: {', '.join(sorted(_ALLOWED_EXTS))}",
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
    path = _resolve_upload_path(obj)
    if path is None:
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
    path = _resolve_upload_path(obj)
    if path is not None:
        try:
            path.unlink()
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", path, exc)
    db.delete(obj)
    db.commit()
