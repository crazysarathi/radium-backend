"""Accessory endpoints."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession, WriterUser
from app.schemas.accessory import AccessoryCreate, AccessoryRead, AccessoryUpdate
from app.schemas.common import APIResponse
from app.services.accessory import AccessoryService

router = APIRouter(prefix="/accessories", tags=["Accessories"])


@router.get("", response_model=APIResponse[list[AccessoryRead]])
async def list_accessories(
    session: DBSession, user: CurrentUser
) -> APIResponse[list[AccessoryRead]]:
    accessories = await AccessoryService(session).list_accessories()
    return APIResponse(data=[AccessoryRead.model_validate(a) for a in accessories])


@router.post("", response_model=APIResponse[AccessoryRead], status_code=status.HTTP_201_CREATED)
async def create_accessory(
    body: AccessoryCreate, session: DBSession, user: WriterUser
) -> APIResponse[AccessoryRead]:
    accessory = await AccessoryService(session).create_accessory(body)
    return APIResponse(message="Accessory created", data=AccessoryRead.model_validate(accessory))


@router.get("/{accessory_id}", response_model=APIResponse[AccessoryRead])
async def get_accessory(
    accessory_id: str, session: DBSession, user: CurrentUser
) -> APIResponse[AccessoryRead]:
    accessory = await AccessoryService(session).get_accessory(accessory_id)
    return APIResponse(data=AccessoryRead.model_validate(accessory))


@router.patch("/{accessory_id}", response_model=APIResponse[AccessoryRead])
async def update_accessory(
    accessory_id: str, body: AccessoryUpdate, session: DBSession, user: WriterUser
) -> APIResponse[AccessoryRead]:
    accessory = await AccessoryService(session).update_accessory(accessory_id, body)
    return APIResponse(message="Accessory updated", data=AccessoryRead.model_validate(accessory))


@router.delete("/{accessory_id}", response_model=APIResponse[None])
async def delete_accessory(
    accessory_id: str, session: DBSession, user: WriterUser
) -> APIResponse[None]:
    await AccessoryService(session).delete_accessory(accessory_id)
    return APIResponse(message="Accessory deleted")
