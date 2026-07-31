"""Enquiry repository."""

from app.models.enquiry import Enquiry
from app.repositories.base import BaseRepository


class EnquiryRepository(BaseRepository[Enquiry]):
    model = Enquiry
    default_sort_field = "received_at"
