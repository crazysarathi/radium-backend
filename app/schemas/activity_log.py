"""Activity log schema — read-only feed for the console's History page."""

import uuid
from datetime import datetime

from app.schemas._camel import CamelORMModel


class ActivityRead(CamelORMModel):
    id: uuid.UUID
    type: str
    module: str
    label: str
    at: datetime
