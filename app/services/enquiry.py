"""Enquiry service — inbox CRUD (list/update-status/delete).

Enquiries are visitor-submitted data, not admin edits, so — matching the
former mock's `activity: false` — mutations here are NOT recorded to the
activity feed.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enquiry import Enquiry
from app.repositories.enquiry import EnquiryRepository
from app.schemas.enquiry import EnquiryUpdate


class EnquiryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.enquiries = EnquiryRepository(session)

    async def list_enquiries(self) -> list[Enquiry]:
        return await self.enquiries.list_all(order_by="received_at", order="desc")

    async def get_enquiry(self, enquiry_id) -> Enquiry:
        enquiry = await self.enquiries.get(enquiry_id)
        if enquiry is None:
            raise NotFoundError("Enquiry not found")
        return enquiry

    async def update_status(self, enquiry_id, data: EnquiryUpdate) -> Enquiry:
        enquiry = await self.get_enquiry(enquiry_id)
        enquiry = await self.enquiries.update(enquiry, data.model_dump(exclude_unset=True))
        await self.session.commit()
        return enquiry

    async def delete_enquiry(self, enquiry_id) -> None:
        enquiry = await self.get_enquiry(enquiry_id)
        await self.enquiries.hard_delete(enquiry)
        await self.session.commit()
