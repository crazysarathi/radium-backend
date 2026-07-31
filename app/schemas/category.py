"""Category schemas — read-only lookup, no admin UI mutates these yet."""

from app.schemas._camel import CamelORMModel


class CategoryRead(CamelORMModel):
    id: str
    key: str
    label: str
    blurb: str | None = None
