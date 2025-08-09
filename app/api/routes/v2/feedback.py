"""
Feedback API for AI-generated follow-up notes.

Provides endpoints for submitting and retrieving feedback on AI-generated content.
Requires user and tenant authentication via headers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Tuple
import logging

from app.database.repositories.connection import DatabaseConnection
from app.data.repositories.feedback_repository import FeedbackRepository
from app.api.schemas.feedback import (
    SubmitFeedbackRequest,
    FeedbackSubmissionResponse,
    FeedbackResponse
)
from app.api.schemas.auth_user import UserResponse, TenantContextResponse
from app.security.dependencies import UserAndTenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])

async def get_db() -> Session:
    """Get database session."""
    async with DatabaseConnection.get_session() as session:
        yield session

@router.post("/submit", response_model=FeedbackSubmissionResponse)
async def submit_feedback(
    feedback_request: SubmitFeedbackRequest,
    auth: Tuple[UserResponse, TenantContextResponse] = Depends(UserAndTenant),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on an AI-generated follow-up note.
    
    Requires user and tenant authentication via headers:
    - X-auth-user: User context from central VecApp
    - X-request-tenant: Tenant context from central VecApp
    
    Args:
        feedback_request: Feedback data including note_id, helpfulness, comment
        auth: User and tenant context from headers
        db: Database session
    
    Returns:
        Feedback submission response with created feedback record
    """
    user, tenant = auth
    
    try:
        feedback_repo = FeedbackRepository(db)

        # Add user and tenant info to the request
        feedback_request.admin_id = user.id
        feedback_request.tenant_id = tenant.id

        # Verify the note exists and is AI-generated
        if not feedback_repo.check_note_exists(feedback_request.note_id, tenant.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI-generated note with ID {feedback_request.note_id} not found"
            )

        # Submit the feedback
        feedback = feedback_repo.submit_feedback(feedback_request)

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to submit feedback. Feedback may already exist from this user for this note."
            )

        # Convert to response model
        feedback_response = FeedbackResponse(
            id=feedback.id,
            note_id=feedback.note_id,
            visitor_id=feedback.visitor_id,
            admin_id=feedback.admin_id,
            tenant_id=feedback.tenant_id,
            helpfulness=feedback.helpfulness,
            comment=feedback.comment,
            ai_model_version=feedback.ai_model_version,
            ai_confidence_score=feedback.ai_confidence_score,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at
        )

        logger.info(
            f"Feedback submitted by user {user.id} for note {feedback_request.note_id} "
            f"in tenant {tenant.schema_name}"
        )

        return FeedbackSubmissionResponse(
            feedback=feedback_response,
            note_updated=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while submitting feedback"
        )

@router.get("/health")
async def feedback_health_check():
    """Health check endpoint for feedback service."""
    return {
        "status": "healthy",
        "service": "feedback",
        "message": "Feedback service is operational"
    }