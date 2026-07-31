"""Storage backend abstraction.

The API layer only ever talks to `StorageBackend`, so swapping local disk for
S3 / Supabase Storage / Cloudinary is a new backend class + a config change.
"""

from abc import ABC, abstractmethod

from fastapi import UploadFile
from pydantic import BaseModel


class StoredFile(BaseModel):
    filename: str
    # Backend-relative path, e.g. "products/mercury/3f2a…-front.jpg"
    path: str
    url: str
    size: int
    content_type: str


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, *, folder: str = "") -> StoredFile: ...

    @abstractmethod
    async def delete(self, path: str) -> bool: ...

    @abstractmethod
    def url_for(self, path: str) -> str: ...
