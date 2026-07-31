"""Local-disk storage backend."""

import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.storage.base import StorageBackend, StoredFile

_CHUNK_SIZE = 1024 * 1024
_SAFE_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _sanitize_folder(folder: str) -> str:
    """Allow only simple nested folders like 'products/mercury'."""
    if not folder:
        return ""
    segments = [s for s in folder.strip("/").split("/") if s]
    for segment in segments:
        if not _SAFE_SEGMENT.match(segment):
            raise BadRequestError(f'Invalid folder name: "{segment}"')
    return "/".join(segments)


def _sanitize_filename(filename: str) -> tuple[str, str]:
    """Return (safe_stem, extension) from an untrusted client filename."""
    name = Path(filename or "file").name
    stem, _, ext = name.rpartition(".")
    if not stem:
        stem, ext = ext, ""
    ext = ext.lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
        raise BadRequestError(f'File type ".{ext}" is not allowed. Allowed: {allowed}')
    safe_stem = re.sub(r"[^a-z0-9_-]+", "-", stem.lower()).strip("-") or "file"
    return safe_stem[:60], ext


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path | None = None, base_url: str | None = None):
        self.root = (root or Path(settings.UPLOAD_DIR)).resolve()
        self.base_url = (base_url or f"{settings.PUBLIC_BASE_URL}/uploads").rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile, *, folder: str = "") -> StoredFile:
        folder = _sanitize_folder(folder)
        stem, ext = _sanitize_filename(file.filename or "")
        stored_name = f"{uuid.uuid4().hex[:12]}-{stem}.{ext}"
        rel_path = f"{folder}/{stored_name}" if folder else stored_name

        target = self.root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)

        size = 0
        max_bytes = settings.max_upload_size_bytes
        try:
            async with aiofiles.open(target, "wb") as out:
                while chunk := await file.read(_CHUNK_SIZE):
                    size += len(chunk)
                    if size > max_bytes:
                        raise BadRequestError(
                            f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit"
                        )
                    await out.write(chunk)
        except BaseException:
            # Any failure mid-write (size limit, disconnect, disk error) must
            # not leave a partial file behind.
            target.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

        return StoredFile(
            filename=stored_name,
            path=rel_path,
            url=self.url_for(rel_path),
            size=size,
            content_type=file.content_type or "application/octet-stream",
        )

    async def delete(self, path: str) -> bool:
        target = (self.root / path).resolve()
        # Refuse anything that escapes the upload root.
        if not target.is_relative_to(self.root) or not target.is_file():
            return False
        target.unlink()
        return True

    def url_for(self, path: str) -> str:
        return f"{self.base_url}/{path}"


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageBackend()
    raise ValueError(
        f"Unsupported STORAGE_BACKEND: {settings.STORAGE_BACKEND!r} "
        "(implement an S3/Supabase/Cloudinary backend and register it here)"
    )
