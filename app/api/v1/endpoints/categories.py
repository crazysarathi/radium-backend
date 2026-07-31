"""Category endpoints — read-only lookup for the product form's category select."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryRead
from app.schemas.common import APIResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=APIResponse[list[CategoryRead]])
async def list_categories(session: DBSession, user: CurrentUser) -> APIResponse[list[CategoryRead]]:
    categories = await CategoryRepository(session).list_all(order_by="label", order="asc")
    return APIResponse(data=[CategoryRead.model_validate(c) for c in categories])
