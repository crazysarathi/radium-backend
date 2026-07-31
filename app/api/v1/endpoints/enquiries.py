"""Enquiry inbox endpoints (list / update-status / delete — no admin-side create)."""

import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession, WriterUser
from app.schemas.common import APIResponse
from app.schemas.enquiry import EnquiryRead, EnquiryUpdate
from app.services.enquiry import EnquiryService

router = APIRouter(prefix="/enquiries", tags=["Enquiries"])


@router.get("", response_model=APIResponse[list[EnquiryRead]])
async def list_enquiries(session: DBSession, user: CurrentUser) -> APIResponse[list[EnquiryRead]]:
    enquiries = await EnquiryService(session).list_enquiries()
    return APIResponse(data=[EnquiryRead.model_validate(e) for e in enquiries])


@router.get("/{enquiry_id}", response_model=APIResponse[EnquiryRead])
async def get_enquiry(
    enquiry_id: uuid.UUID, session: DBSession, user: CurrentUser
) -> APIResponse[EnquiryRead]:
    enquiry = await EnquiryService(session).get_enquiry(enquiry_id)
    return APIResponse(data=EnquiryRead.model_validate(enquiry))


@router.patch("/{enquiry_id}", response_model=APIResponse[EnquiryRead])
async def update_enquiry(
    enquiry_id: uuid.UUID, body: EnquiryUpdate, session: DBSession, user: WriterUser
) -> APIResponse[EnquiryRead]:
    enquiry = await EnquiryService(session).update_status(enquiry_id, body)
    return APIResponse(message="Enquiry updated", data=EnquiryRead.model_validate(enquiry))


@router.delete("/{enquiry_id}", response_model=APIResponse[None])
async def delete_enquiry(
    enquiry_id: uuid.UUID, session: DBSession, user: WriterUser
) -> APIResponse[None]:
    await EnquiryService(session).delete_enquiry(enquiry_id)
    return APIResponse(message="Enquiry deleted")
