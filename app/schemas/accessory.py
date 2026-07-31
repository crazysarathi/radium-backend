"""Accessory schemas."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas._camel import CamelModel, CamelORMModel

AccessoryStatus = Literal["available", "roadmap"]


class AccessoryRead(CamelORMModel):
    id: str
    name: str
    sku: str
    category: str
    description: str
    for_: list[str] = Field(alias="for")
    status: str
    created_at: datetime
    updated_at: datetime


class AccessoryCreate(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    sku: str = Field(min_length=1, max_length=60)
    category: str = Field(min_length=1, max_length=80)
    description: str = ""
    for_: list[str] = Field(default_factory=list, alias="for")
    status: AccessoryStatus = "available"


class AccessoryUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    for_: list[str] | None = Field(default=None, alias="for")
    status: AccessoryStatus | None = None
