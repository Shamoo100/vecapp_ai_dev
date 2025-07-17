from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from app.database.repositories.connection import DatabaseConnection
from app.data.interfaces.feedback_repository import FeedbackRepository
from app.database.models.tenant import Tenant 
from app.api.schemas.feedback import (
    SubmitFeedbackRequest,
    FeedbackSubmissionResponse,
    FeedbackResponse,
    GetFeedbackResponse
)
from app.security.api_key import get_current_tenant
from app.security.auth import get_current_tenant_admin, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])

#connect to db
async def get_db() -> Session:
    async with DatabaseConnection.get_session() as session:
        yield session

@router.post("/submit", response_model=FeedbackSubmissionResponse)
async def submit_feedback(
    feedback_request: SubmitFeedbackRequest,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
    current_admin: User = Depends(get_current_tenant_admin)
):
    """
    Submit feedback on an AI-generated note
    
    This endpoint allows admins to provide feedback on AI-generated visitor insight notes.
    The feedback helps improve future AI recommendations and tracks effectiveness.
    
    - **note_id**: ID of the AI-generated note to provide feedback on
    - **visitor_id**: ID of the visitor the note is about
    - **admin_id**: ID of the admin submitting the feedback
    - **tenant_id**: Tenant ID for multi-tenancy support
    - **helpfulness**: Rating of how helpful the note was (yes/no/partially)
    - **comment**: Optional comment (max 100 characters)
    
    Returns the created feedback record and confirmation that the note was marked as having received feedback.
    """
    try:
        feedback_repo = FeedbackRepository(db)
        
        # Verify the note exists and is AI-generated
        if not feedback_repo.check_note_exists(feedback_request.note_id, feedback_request.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI-generated note with ID {feedback_request.note_id} not found"
            )
        
        # Submit the feedback
        feedback = feedback_repo.submit_feedback(feedback_request)
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to submit feedback. Feedback may already exist from this admin for this note."
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
        
        logger.info(f"Feedback submitted successfully for note {feedback_request.note_id}")
        
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

@router.get("/note/{note_id}", response_model=GetFeedbackResponse)
async def get_feedback_for_note(
    note_id: int,
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all feedback for a specific AI-generated note
    
    This endpoint retrieves all feedback submitted for a particular note,
    including feedback count and status.
    
    - **note_id**: ID of the note to get feedback for
    - **tenant_id**: Tenant ID for security and multi-tenancy
    
    Returns feedback summary and list of all feedback records for the note.
    """
    try:
        feedback_repo = FeedbackRepository(db)
        
        # Verify the note exists
        if not feedback_repo.check_note_exists(note_id, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI-generated note with ID {note_id} not found"
            )
        
        # Get feedback for the note
        feedback_list = feedback_repo.get_feedback_for_note(note_id, tenant_id)
        
        # Convert to response models
        feedback_responses = [
            FeedbackResponse(
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
            for feedback in feedback_list
        ]
        
        return GetFeedbackResponse(
            note_id=note_id,
            feedback_count=len(feedback_responses),
            feedback_received=len(feedback_responses) > 0,
            feedback_list=feedback_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback for note {note_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving feedback"
        )

@router.get("/admin/{admin_id}", response_model=List[FeedbackResponse])
async def get_feedback_by_admin(
    admin_id: UUID,
    tenant_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get feedback submitted by a specific admin
    
    This endpoint retrieves all feedback submitted by a particular admin,
    useful for tracking admin engagement and feedback patterns.
    
    - **admin_id**: ID of the admin whose feedback to retrieve
    - **tenant_id**: Tenant ID for security and multi-tenancy
    - **limit**: Maximum number of feedback records to return (default: 50)
    
    Returns list of feedback records submitted by the admin.
    """
    try:
        feedback_repo = FeedbackRepository(db)
        
        # Get feedback by admin
        feedback_list = feedback_repo.get_feedback_by_admin(admin_id, tenant_id, limit)
        
        # Convert to response models
        feedback_responses = [
            FeedbackResponse(
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
            for feedback in feedback_list
        ]
        
        return feedback_responses
        
    except Exception as e:
        logger.error(f"Error retrieving feedback by admin {admin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving admin feedback"
        )

@router.get("/stats", response_model=dict)
async def get_feedback_stats(
    tenant_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics for analytics
    
    This endpoint provides analytics on feedback patterns, including:
    - Total feedback count
    - Breakdown by helpfulness rating
    - Feedback rate (percentage of AI notes that received feedback)
    - Notes with feedback vs total AI notes
    
    - **tenant_id**: Tenant ID for security and multi-tenancy
    - **days**: Number of days to look back for statistics (default: 30)
    
    Returns comprehensive feedback statistics for the specified period.
    """
    try:
        feedback_repo = FeedbackRepository(db)
        
        # Get feedback statistics
        stats = feedback_repo.get_feedback_stats(tenant_id, days)
        
        if not stats:
            return {
                "total_feedback": 0,
                "helpfulness_breakdown": {},
                "notes_with_feedback": 0,
                "total_ai_notes": 0,
                "feedback_rate": 0,
                "period_days": days
            }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving feedback stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving feedback statistics"
        )

@router.get("/health")
async def feedback_health_check():
    """
    Health check endpoint for feedback service
    
    Returns the status of the feedback service.
    """
    return {
        "status": "healthy",
        "service": "feedback",
        "message": "Feedback service is operational"
    }