"""File upload endpoints (the admin app's `POST /api/media` swap point)."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.deps import WriterUser
from app.schemas.common import APIResponse
from app.storage.base import StorageBackend, StoredFile
from app.storage.local import get_storage

router = APIRouter(prefix="/media", tags=["Media"])

Storage = Annotated[StorageBackend, Depends(get_storage)]


@router.post("", response_model=APIResponse[StoredFile], status_code=status.HTTP_201_CREATED)
async def upload_file(
    user: WriterUser,
    storage: Storage,
    file: Annotated[UploadFile, File()],
    folder: Annotated[str, Query(max_length=100, description="Optional subfolder, e.g. products/mercury")] = "",
) -> APIResponse[StoredFile]:
    stored = await storage.save(file, folder=folder)
    return APIResponse(message="File uploaded", data=stored)
