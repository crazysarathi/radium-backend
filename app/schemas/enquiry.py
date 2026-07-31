"""Enquiry schemas — contact-form submissions landing in the admin inbox."""

import uuid
from datetime import datetime
from typing import Literal

from app.schemas._camel import CamelModel, CamelORMModel

EnquiryStatus = Literal["new", "replied", "closed"]


class EnquiryRead(CamelORMModel):
    id: uuid.UUID
    name: str
    org: str
    email: str
    phone: str
    interest: str
    message: str
    status: str
    received_at: datetime


class EnquiryUpdate(CamelModel):
    status: EnquiryStatus
