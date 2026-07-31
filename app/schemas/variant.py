"""Variant schemas — Jupiter's six-digit SKUs and everyone else's chassis models."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas._camel import CamelModel, CamelORMModel

VariantStatus = Literal["available", "roadmap"]
JupiterCode = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class JupiterModelRead(CamelORMModel):
    id: str
    code: str
    name: str
    family: str
    rack_units: str
    status: str
    created_at: datetime
    updated_at: datetime


class JupiterModelCreate(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    code: str = JupiterCode
    name: str = Field(min_length=1, max_length=120)
    family: str
    rack_units: str = Field(default="4U", max_length=10)
    status: VariantStatus = "available"


class JupiterModelUpdate(CamelModel):
    code: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    family: str | None = None
    rack_units: str | None = Field(default=None, max_length=10)
    status: VariantStatus | None = None


class ChassisModelRead(CamelORMModel):
    id: str
    model: str
    ru: str
    img: str
    bullets: list[str]
    family: str
    status: str
    created_at: datetime
    updated_at: datetime


class ChassisModelCreate(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    ru: str = Field(default="2U", max_length=10)
    img: str = Field(default="", max_length=300)
    bullets: list[str] = Field(default_factory=list)
    family: str
    status: VariantStatus = "available"


class ChassisModelUpdate(CamelModel):
    model: str | None = Field(default=None, min_length=1, max_length=80)
    ru: str | None = Field(default=None, max_length=10)
    img: str | None = Field(default=None, max_length=300)
    bullets: list[str] | None = None
    family: str | None = None
    status: VariantStatus | None = None
