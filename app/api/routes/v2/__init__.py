"""API v2 route initialization."""
from fastapi import APIRouter

# V2 is currently a placeholder - no actual routes implemented yet
# from .routes import (
#     analytics_v2,
#     visitors_v2,
# )

v2_router = APIRouter(prefix="/v2", tags=["v2"])

# TODO: Implement v2 routes with breaking changes
# v2_router.include_router(analytics_v2.router, prefix="/analytics", tags=["analytics-v2"])
# v2_router.include_router(visitors_v2.router, prefix="/visitors", tags=["visitors-v2"])

# Placeholder health check for v2
@v2_router.get("/health")
async def v2_health_check():
    return {"status": "ok", "version": "v2", "message": "V2 API placeholder"}