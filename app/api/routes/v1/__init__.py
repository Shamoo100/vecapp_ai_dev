"""API v1 routes package.

This package contains all the API v1 route modules for the VecApp AI Service.
Each module defines FastAPI routers for specific functionality areas.
"""

from fastapi import APIRouter
from . import (
    auth_routes,
   # example_ai_service,  # Add the AI examples for testing authentication patterns
    tenant_routes,  # Re-enabled with consolidated service
    followup_routes,
    # feedback,  # Temporarily disabled due to import issues - REPLACED by consolidated followup_routes
    # followup_notes,  # Temporarily disabled due to import issues - REPLACED by consolidated followup_routes
)



# Create v1 router
v1_router = APIRouter(prefix="/v1", tags=["v1"])

# Include working routes for authentication testing
v1_router.include_router(auth_routes.router, tags=["Authentication"])
#v1_router.include_router(example_ai_service.router, tags=["ai-examples"])

# Include consolidated tenant routes
v1_router.include_router(tenant_routes.router, tags=["Tenants"])

# Include NEW consolidated follow-up routes (replaces feedback and followup_notes)
v1_router.include_router(followup_routes.router, tags=["Follow-up"])



# Expose all routers for easy access
__all__ = [
    "v1_router",
    "auth_routes",
    "tenant_routes",
    "followup_routes", 
]