"""Variant endpoints — Jupiter's six-digit SKUs and everyone else's chassis models."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession, WriterUser
from app.schemas.common import APIResponse
from app.schemas.variant import (
    ChassisModelCreate,
    ChassisModelRead,
    ChassisModelUpdate,
    JupiterModelCreate,
    JupiterModelRead,
    JupiterModelUpdate,
)
from app.services.variant import ChassisModelService, JupiterModelService

jupiter_router = APIRouter(prefix="/jupiter-models", tags=["Variants"])
chassis_router = APIRouter(prefix="/chassis-models", tags=["Variants"])


@jupiter_router.get("", response_model=APIResponse[list[JupiterModelRead]])
async def list_jupiter_models(
    session: DBSession, user: CurrentUser
) -> APIResponse[list[JupiterModelRead]]:
    variants = await JupiterModelService(session).list_variants()
    return APIResponse(data=[JupiterModelRead.model_validate(v) for v in variants])


@jupiter_router.post(
    "", response_model=APIResponse[JupiterModelRead], status_code=status.HTTP_201_CREATED
)
async def create_jupiter_model(
    body: JupiterModelCreate, session: DBSession, user: WriterUser
) -> APIResponse[JupiterModelRead]:
    variant = await JupiterModelService(session).create_variant(body)
    return APIResponse(message="Variant created", data=JupiterModelRead.model_validate(variant))


@jupiter_router.get("/{variant_id}", response_model=APIResponse[JupiterModelRead])
async def get_jupiter_model(
    variant_id: str, session: DBSession, user: CurrentUser
) -> APIResponse[JupiterModelRead]:
    variant = await JupiterModelService(session).get_variant(variant_id)
    return APIResponse(data=JupiterModelRead.model_validate(variant))


@jupiter_router.patch("/{variant_id}", response_model=APIResponse[JupiterModelRead])
async def update_jupiter_model(
    variant_id: str, body: JupiterModelUpdate, session: DBSession, user: WriterUser
) -> APIResponse[JupiterModelRead]:
    variant = await JupiterModelService(session).update_variant(variant_id, body)
    return APIResponse(message="Variant updated", data=JupiterModelRead.model_validate(variant))


@jupiter_router.delete("/{variant_id}", response_model=APIResponse[None])
async def delete_jupiter_model(
    variant_id: str, session: DBSession, user: WriterUser
) -> APIResponse[None]:
    await JupiterModelService(session).delete_variant(variant_id)
    return APIResponse(message="Variant deleted")


@chassis_router.get("", response_model=APIResponse[list[ChassisModelRead]])
async def list_chassis_models(
    session: DBSession, user: CurrentUser
) -> APIResponse[list[ChassisModelRead]]:
    variants = await ChassisModelService(session).list_variants()
    return APIResponse(data=[ChassisModelRead.model_validate(v) for v in variants])


@chassis_router.post(
    "", response_model=APIResponse[ChassisModelRead], status_code=status.HTTP_201_CREATED
)
async def create_chassis_model(
    body: ChassisModelCreate, session: DBSession, user: WriterUser
) -> APIResponse[ChassisModelRead]:
    variant = await ChassisModelService(session).create_variant(body)
    return APIResponse(message="Variant created", data=ChassisModelRead.model_validate(variant))


@chassis_router.get("/{variant_id}", response_model=APIResponse[ChassisModelRead])
async def get_chassis_model(
    variant_id: str, session: DBSession, user: CurrentUser
) -> APIResponse[ChassisModelRead]:
    variant = await ChassisModelService(session).get_variant(variant_id)
    return APIResponse(data=ChassisModelRead.model_validate(variant))


@chassis_router.patch("/{variant_id}", response_model=APIResponse[ChassisModelRead])
async def update_chassis_model(
    variant_id: str, body: ChassisModelUpdate, session: DBSession, user: WriterUser
) -> APIResponse[ChassisModelRead]:
    variant = await ChassisModelService(session).update_variant(variant_id, body)
    return APIResponse(message="Variant updated", data=ChassisModelRead.model_validate(variant))


@chassis_router.delete("/{variant_id}", response_model=APIResponse[None])
async def delete_chassis_model(
    variant_id: str, session: DBSession, user: WriterUser
) -> APIResponse[None]:
    await ChassisModelService(session).delete_variant(variant_id)
    return APIResponse(message="Variant deleted")
