"""Storage service – local filesystem or Amazon S3.

Selected at runtime via the STORAGE_BACKEND environment variable:
  STORAGE_BACKEND=local  (default)  – stores files under UPLOAD_DIR
  STORAGE_BACKEND=s3                – stores files in S3_BUCKET

S3 environment variables (required when STORAGE_BACKEND=s3):
  S3_BUCKET           – bucket name
  S3_REGION           – AWS region (default: us-east-1)
  AWS_ACCESS_KEY_ID   – optional (falls back to IAM role / env chain)
  AWS_SECRET_ACCESS_KEY

Public API
----------
  save_file(data: bytes, key: str, content_type: str) -> str
      Stores a file and returns a URL or local path string.

  load_file(key: str) -> bytes
      Returns the file bytes.

  delete_file(key: str) -> None
      Deletes the file.

  public_url(key: str) -> str
      Returns the public URL (for S3) or local path.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger("align.storage")

_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()
_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
_S3_BUCKET = os.getenv("S3_BUCKET", "")
_S3_REGION = os.getenv("S3_REGION", "us-east-1")


# ── Local ──────────────────────────────────────────────────────────────────────

def _local_resolve(key: str) -> Path:
    """
    Resolve *key* relative to _UPLOAD_DIR and raise ValueError if the
    resolved path escapes the upload directory (path-traversal guard).
    """
    resolved = (_UPLOAD_DIR / key).resolve()
    upload_root = _UPLOAD_DIR.resolve()
    if not resolved.is_relative_to(upload_root):
        raise ValueError(f"Storage key {key!r} escapes the upload directory.")
    return resolved


def _local_save(data: bytes, key: str) -> str:
    dest = _local_resolve(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return str(dest)


def _local_load(key: str) -> bytes:
    path = _local_resolve(key)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {key}")
    return path.read_bytes()


def _local_delete(key: str) -> None:
    path = _local_resolve(key)
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            logger.warning("Could not delete local file %s: %s", path, exc)


def _local_url(key: str) -> str:
    return str(_UPLOAD_DIR / key)


# ── S3 ─────────────────────────────────────────────────────────────────────────

def _s3_client():
    try:
        import boto3
    except ImportError:
        raise RuntimeError("boto3 is not installed; cannot use S3 storage.")
    return boto3.client("s3", region_name=_S3_REGION)


def _s3_save(data: bytes, key: str, content_type: str) -> str:
    client = _s3_client()
    client.put_object(
        Bucket=_S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    logger.info("Uploaded %s to s3://%s/%s", key, _S3_BUCKET, key)
    return f"s3://{_S3_BUCKET}/{key}"


def _s3_load(key: str) -> bytes:
    client = _s3_client()
    response = client.get_object(Bucket=_S3_BUCKET, Key=key)
    return response["Body"].read()


def _s3_delete(key: str) -> None:
    client = _s3_client()
    client.delete_object(Bucket=_S3_BUCKET, Key=key)
    logger.info("Deleted s3://%s/%s", _S3_BUCKET, key)


def _s3_url(key: str) -> str:
    return f"https://{_S3_BUCKET}.s3.{_S3_REGION}.amazonaws.com/{key}"


# ── Public API ─────────────────────────────────────────────────────────────────

def save_file(data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    """Store file data and return a URL or local path."""
    if _BACKEND == "s3":
        if not _S3_BUCKET:
            raise RuntimeError("S3_BUCKET environment variable is not set.")
        return _s3_save(data, key, content_type)
    return _local_save(data, key)


def load_file(key: str) -> bytes:
    """Load file bytes by storage key."""
    if _BACKEND == "s3":
        return _s3_load(key)
    return _local_load(key)


def delete_file(key: str) -> None:
    """Delete a file by storage key."""
    if _BACKEND == "s3":
        _s3_delete(key)
    else:
        _local_delete(key)


def public_url(key: str) -> str:
    """Return a public URL or path for the stored file."""
    if _BACKEND == "s3":
        return _s3_url(key)
    return _local_url(key)
