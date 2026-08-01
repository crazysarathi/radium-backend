"""Product endpoints."""

from fastapi import APIRouter, status

from app.api.deps import DBSession, WriterUser
from app.schemas.common import APIResponse
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=APIResponse[list[ProductRead]])
async def list_products(session: DBSession) -> APIResponse[list[ProductRead]]:
    products = await ProductService(session).list_products()
    return APIResponse(data=[ProductRead.model_validate(p) for p in products])


@router.post("", response_model=APIResponse[ProductRead], status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate, session: DBSession, user: WriterUser
) -> APIResponse[ProductRead]:
    product = await ProductService(session).create_product(body)
    return APIResponse(message="Product created", data=ProductRead.model_validate(product))


@router.get("/{product_id}", response_model=APIResponse[ProductRead])
async def get_product(product_id: str, session: DBSession) -> APIResponse[ProductRead]:
    product = await ProductService(session).get_product(product_id)
    return APIResponse(data=ProductRead.model_validate(product))


@router.patch("/{product_id}", response_model=APIResponse[ProductRead])
async def update_product(
    product_id: str, body: ProductUpdate, session: DBSession, user: WriterUser
) -> APIResponse[ProductRead]:
    product = await ProductService(session).update_product(product_id, body)
    return APIResponse(message="Product updated", data=ProductRead.model_validate(product))


@router.delete("/{product_id}", response_model=APIResponse[None])
async def delete_product(
    product_id: str, session: DBSession, user: WriterUser
) -> APIResponse[None]:
    await ProductService(session).delete_product(product_id)
    return APIResponse(message="Product deleted")
