"""API v1 routes package.

This package contains all the API v1 route modules for the VecApp AI Service.
Each module defines FastAPI routers for specific functionality areas.
"""

# Import all route modules to make them available for import
from . import (
    auth_routes,
    feedback,
    followup_notes,
)

# Expose all routers for easy access
__all__ = [
    "auth_routes",
    "feedback",
    "followup_notes",
]