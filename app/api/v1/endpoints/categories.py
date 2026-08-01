"""Category endpoints — public catalogue reads, writer-only mutations."""

from fastapi import APIRouter, status

from app.api.deps import DBSession, WriterUser
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import APIResponse
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=APIResponse[list[CategoryRead]])
async def list_categories(session: DBSession) -> APIResponse[list[CategoryRead]]:
    categories = await CategoryService(session).list_categories()
    return APIResponse(data=[CategoryRead.model_validate(c) for c in categories])


@router.post("", response_model=APIResponse[CategoryRead], status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate, session: DBSession, user: WriterUser
) -> APIResponse[CategoryRead]:
    category = await CategoryService(session).create_category(body)
    return APIResponse(message="Category created", data=CategoryRead.model_validate(category))


@router.get("/{category_id}", response_model=APIResponse[CategoryRead])
async def get_category(category_id: str, session: DBSession) -> APIResponse[CategoryRead]:
    category = await CategoryService(session).get_category(category_id)
    return APIResponse(data=CategoryRead.model_validate(category))


@router.patch("/{category_id}", response_model=APIResponse[CategoryRead])
async def update_category(
    category_id: str, body: CategoryUpdate, session: DBSession, user: WriterUser
) -> APIResponse[CategoryRead]:
    category = await CategoryService(session).update_category(category_id, body)
    return APIResponse(message="Category updated", data=CategoryRead.model_validate(category))


@router.delete("/{category_id}", response_model=APIResponse[None])
async def delete_category(
    category_id: str, session: DBSession, user: WriterUser
) -> APIResponse[None]:
    await CategoryService(session).delete_category(category_id)
    return APIResponse(message="Category deleted")
