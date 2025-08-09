"""Database models package - base classes only."""
from .base import Base
from .common import TimestampMixin, SchemaConfigMixin
from .enums import *

# Schema-specific models are imported via their respective packages:
# - app.database.models.public for public schema models
# - app.database.models.tenant for tenant schema models

__all__ = ['Base', 'TimestampMixin', 'SchemaConfigMixin']