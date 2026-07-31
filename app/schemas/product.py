"""Product schemas — the catalogue root, its four free-shape editor blocks."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas._camel import CamelModel, CamelORMModel

ProductStatus = Literal["available", "roadmap"]


class HighlightItem(CamelModel):
    title: str = ""
    body: str = ""


class SpecGroup(CamelModel):
    group: str = ""
    rows: list[tuple[str, str]] = Field(default_factory=list)


class ImageItem(CamelModel):
    label: str = ""
    src: str = ""


class ProductRead(CamelORMModel):
    id: str
    slug: str
    name: str
    series: str
    tagline: str
    category: str
    status: str
    note: str
    form_factor: str
    has_models: bool
    summary: str
    highlights: list[HighlightItem]
    applications: list[str]
    specs: list[SpecGroup]
    images: list[ImageItem]
    created_at: datetime
    updated_at: datetime


class ProductCreate(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    slug: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    series: str = Field(default="", max_length=80)
    tagline: str = Field(min_length=1, max_length=200)
    category: str
    status: ProductStatus = "available"
    note: str = Field(default="", max_length=200)
    form_factor: str = Field(default="", max_length=80)
    has_models: bool = False
    summary: str = Field(min_length=1)
    highlights: list[HighlightItem] = Field(default_factory=list)
    applications: list[str] = Field(default_factory=list)
    specs: list[SpecGroup] = Field(default_factory=list)
    images: list[ImageItem] = Field(default_factory=list)


class ProductUpdate(CamelModel):
    slug: str | None = Field(default=None, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    series: str | None = Field(default=None, max_length=80)
    tagline: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = None
    status: ProductStatus | None = None
    note: str | None = Field(default=None, max_length=200)
    form_factor: str | None = Field(default=None, max_length=80)
    has_models: bool | None = None
    summary: str | None = Field(default=None, min_length=1)
    highlights: list[HighlightItem] | None = None
    applications: list[str] | None = None
    specs: list[SpecGroup] | None = None
    images: list[ImageItem] | None = None
