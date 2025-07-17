"""API v1 route initialization."""
from fastapi import APIRouter
from .routes import (
    auth_routes,
    followup_notes,
    feedback
)

# Create v1 router
v1_router = APIRouter(prefix="/v1", tags=["v1"])

# Include all v1 routes
v1_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
v1_router.include_router(followup_notes.router, prefix="/followup-notes", tags=["followup-notes"])
v1_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])