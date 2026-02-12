"""Photo upload and management endpoints."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Photo storage directory — relative to project root
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "photos"
_INDEX_FILE = _DATA_DIR / "index.json"
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
_EXT_MAP = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _ensure_dirs() -> None:
    """Create data directories if they don't exist."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _INDEX_FILE.exists():
        _INDEX_FILE.write_text("[]")


def _load_index() -> list[dict[str, Any]]:
    """Load the photo metadata index."""
    _ensure_dirs()
    try:
        return json.loads(_INDEX_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_index(index: list[dict[str, Any]]) -> None:
    """Save the photo metadata index."""
    _ensure_dirs()
    _INDEX_FILE.write_text(json.dumps(index, indent=2, default=str))


def _find_photo(photo_id: str) -> dict[str, Any] | None:
    """Find a photo entry by ID."""
    index = _load_index()
    for entry in index:
        if entry["id"] == photo_id:
            return entry
    return None


@router.post("/photos/upload")
async def upload_photo(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a photo for investigation reference.

    Accepts image/jpeg, image/png, image/webp. Max 10MB.
    """
    # Validate content type
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: {', '.join(_ALLOWED_TYPES)}",
        )

    # Read file content
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {_MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    _ensure_dirs()

    # Generate unique ID and save
    photo_id = str(uuid.uuid4())
    ext = _EXT_MAP.get(content_type, "jpg")
    filename = f"{photo_id}.{ext}"
    file_path = _DATA_DIR / filename

    file_path.write_bytes(content)

    # Build metadata entry
    entry = {
        "id": photo_id,
        "filename": file.filename or filename,
        "stored_filename": filename,
        "content_type": content_type,
        "size": len(content),
        "url": f"/api/photos/{photo_id}",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    # Update index
    index = _load_index()
    index.append(entry)
    _save_index(index)

    logger.info("Photo uploaded: %s (%s, %d bytes)", photo_id, content_type, len(content))

    return {
        "id": photo_id,
        "filename": entry["filename"],
        "url": entry["url"],
        "uploaded_at": entry["uploaded_at"],
    }


@router.get("/photos/{photo_id}")
async def get_photo(photo_id: str) -> FileResponse:
    """Serve an uploaded photo by ID."""
    entry = _find_photo(photo_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = _DATA_DIR / entry["stored_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Photo file missing")

    return FileResponse(
        path=str(file_path),
        media_type=entry.get("content_type", "image/jpeg"),
        filename=entry.get("filename", entry["stored_filename"]),
    )


@router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: str) -> dict[str, str]:
    """Delete an uploaded photo."""
    entry = _find_photo(photo_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Delete file
    file_path = _DATA_DIR / entry["stored_filename"]
    if file_path.exists():
        file_path.unlink()

    # Remove from index
    index = _load_index()
    index = [e for e in index if e["id"] != photo_id]
    _save_index(index)

    logger.info("Photo deleted: %s", photo_id)

    return {"status": "deleted", "id": photo_id}
