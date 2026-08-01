"""Category schemas."""

from pydantic import Field

from app.schemas._camel import CamelModel, CamelORMModel


class CategoryRead(CamelORMModel):
    id: str
    key: str
    label: str
    blurb: str | None = None


class CategoryCreate(CamelModel):
    id: str = Field(min_length=1, max_length=60)
    label: str = Field(min_length=1, max_length=120)
    blurb: str | None = None


class CategoryUpdate(CamelModel):
    # `id` is deliberately absent — products reference it as a FK, so the
    # key is permanent once created.
    label: str | None = Field(default=None, min_length=1, max_length=120)
    blurb: str | None = None
