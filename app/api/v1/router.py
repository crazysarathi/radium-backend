"""Version 1 API router."""

from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    accessories,
    activity,
    auth,
    categories,
    enquiries,
    health,
    products,
    uploads,
    users,
    variants,
)
from app.core.rate_limit import enforce_default_rate_limit

api_router = APIRouter(dependencies=[Depends(enforce_default_rate_limit)])
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(uploads.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(variants.jupiter_router)
api_router.include_router(variants.chassis_router)
api_router.include_router(accessories.router)
api_router.include_router(enquiries.router)
api_router.include_router(activity.router)
