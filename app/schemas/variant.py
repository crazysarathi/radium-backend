"""Variant schemas — one generic shape for every family's model line-up."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas._camel import CamelModel, CamelORMModel

VariantStatus = Literal["available", "roadmap"]


class VariantRead(CamelORMModel):
    id: str
    name: str
    code: str | None
    family: str
    rack_units: str
    img: str
    bullets: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class VariantCreate(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    code: str | None = Field(default=None, min_length=1, max_length=80)
    family: str
    rack_units: str = Field(default="2U", max_length=10)
    img: str = Field(default="", max_length=300)
    bullets: list[str] = Field(default_factory=list)
    status: VariantStatus = "available"


class VariantUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    code: str | None = Field(default=None, min_length=1, max_length=80)
    family: str | None = None
    rack_units: str | None = Field(default=None, max_length=10)
    img: str | None = Field(default=None, max_length=300)
    bullets: list[str] | None = None
    status: VariantStatus | None = None
