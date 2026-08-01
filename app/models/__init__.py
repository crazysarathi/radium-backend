"""Import all models here so Base.metadata (and Alembic autogenerate) sees them."""

from app.models.accessory import Accessory
from app.models.activity_log import ActivityLog
from app.models.category import Category
from app.models.enquiry import Enquiry
from app.models.password_reset_token import PasswordResetToken
from app.models.product import Product
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.models.variant import Variant

__all__ = [
    "Accessory",
    "ActivityLog",
    "Category",
    "Enquiry",
    "PasswordResetToken",
    "Product",
    "RefreshToken",
    "User",
    "UserRole",
    "Variant",
]
