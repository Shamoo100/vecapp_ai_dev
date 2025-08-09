"""Main API router configuration."""
from fastapi import APIRouter
from app.api.routes.v1 import v1_router
from app.api.routes.v2 import v2_router  # For future versions

# Main API router
api_router = APIRouter(prefix="/api")

# Include versioned routers
api_router.include_router(v1_router)
# api_router.include_router(v2_router)  # Future version