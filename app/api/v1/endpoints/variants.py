"""Variant endpoints — one generic collection for every family's model line-up."""

from fastapi import APIRouter, Query, status

from app.api.deps import DBSession, WriterUser
from app.schemas.common import APIResponse
from app.schemas.variant import VariantCreate, VariantRead, VariantUpdate
from app.services.variant import VariantService

router = APIRouter(prefix="/variants", tags=["Variants"])


@router.get("", response_model=APIResponse[list[VariantRead]])
async def list_variants(
    session: DBSession,
    family: str | None = Query(default=None, description="Filter by product family id"),
) -> APIResponse[list[VariantRead]]:
    variants = await VariantService(session).list_variants(family)
    return APIResponse(data=[VariantRead.model_validate(v) for v in variants])


@router.post("", response_model=APIResponse[VariantRead], status_code=status.HTTP_201_CREATED)
async def create_variant(
    body: VariantCreate, session: DBSession, user: WriterUser
) -> APIResponse[VariantRead]:
    variant = await VariantService(session).create_variant(body)
    return APIResponse(message="Variant created", data=VariantRead.model_validate(variant))


@router.get("/{variant_id}", response_model=APIResponse[VariantRead])
async def get_variant(variant_id: str, session: DBSession) -> APIResponse[VariantRead]:
    variant = await VariantService(session).get_variant(variant_id)
    return APIResponse(data=VariantRead.model_validate(variant))


@router.patch("/{variant_id}", response_model=APIResponse[VariantRead])
async def update_variant(
    variant_id: str, body: VariantUpdate, session: DBSession, user: WriterUser
) -> APIResponse[VariantRead]:
    variant = await VariantService(session).update_variant(variant_id, body)
    return APIResponse(message="Variant updated", data=VariantRead.model_validate(variant))


@router.delete("/{variant_id}", response_model=APIResponse[None])
async def delete_variant(
    variant_id: str, session: DBSession, user: WriterUser
) -> APIResponse[None]:
    await VariantService(session).delete_variant(variant_id)
    return APIResponse(message="Variant deleted")
