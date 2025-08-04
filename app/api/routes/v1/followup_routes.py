"""
Consolidated Follow-up Routes for VecApp AI Service.

This module provides two main endpoints:
1. Internal follow-up note generation (event-driven processing)
2. Feedback submission for AI-generated notes

Simplified and consolidated from multiple route files for better maintainability.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import logging
import time

from app.services.followup_service import FollowupService
from app.api.schemas.event_schemas import VisitorEventData, AINoteFeedback
from app.security.dependencies import get_current_tenant
from fastapi import Body

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/followup", tags=["Follow-up"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class InternalFollowupRequest(BaseModel):
    """Request model for internal follow-up note generation (event-driven)."""
    event_data: VisitorEventData
    priority: Optional[str] = "medium"
    async_processing: Optional[bool] = True


class InternalFollowupResponse(BaseModel):
    """Response model for internal follow-up note generation."""
    note_id: str
    status: str
    confidence_score: Optional[float] = None
    generation_timestamp: str
    processing_mode: str  # "sync" or "async"


class SubmitFeedbackRequest(BaseModel):
    """Request model for submitting feedback on AI notes."""
    note_id: str
    feedback: AINoteFeedback


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    feedback_id: str
    status: str
    note_id: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/internal/generate",
    response_model=InternalFollowupResponse,
    summary="Internal Follow-up Note Generation",
    description="Generate AI-powered follow-up note for internal event-driven processing. Supports both sync and async modes."
)
async def generate_internal_followup_note(
    request: InternalFollowupRequest,
    background_tasks: BackgroundTasks,
    tenant: str = Depends(get_current_tenant)
) -> InternalFollowupResponse:
    """
    Generate an AI-powered visitor follow-up note for internal processing.
    
    This endpoint is designed for event-driven processing where:
    - Events trigger follow-up note generation
    - Processing can be asynchronous for better performance
    - Comprehensive data collection from multiple services
    - Family scenario handling based on event data
    
    The system will:
    1. Analyze the family scenario from event data
    2. Collect relevant data using the appropriate family methods
    3. Generate AI-powered insights and recommendations
    4. Save results to both member service and AI audit databases
    """
    try:
        followup_service = FollowupService(tenant)
        
        if request.async_processing:
            # Process in background for better performance
            background_tasks.add_task(
                _process_note_async,
                followup_service,
                request.event_data
            )
            
            return InternalFollowupResponse(
                note_id=f"async_{request.event_data.event_id}_{int(time.time())}",
                status="processing",
                confidence_score=None,
                generation_timestamp=request.event_data.timestamp,
                processing_mode="async"
            )
        else:
            # Synchronous processing
            result = await followup_service.generate_enhanced_summary_note(request.event_data)
            
            return InternalFollowupResponse(
                note_id=str(result['note_id']),
                status="completed",
                confidence_score=result['ai_note']['confidence_score'],
                generation_timestamp=result['ai_note']['generation_timestamp'],
                processing_mode="sync"
            )
            
    except ValueError as e:
        logger.warning(f"Invalid request for internal note generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating internal followup note: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate followup note")

# ============================================================================
# MISSING SQS MESSAGE ENDPOINT
# ============================================================================
@router.post(
    "/internal/process-missing",
    response_model=InternalFollowupResponse,
    summary="Process Missing SQS Message",
    description="Synchronously process a missing or failed SQS message by generating the follow-up note and deleting the message from the queue."
)
async def process_missing_sqs_message(
    event_data: VisitorEventData = Body(..., description="Visitor event data"),
    receipt_handle: str = Body(..., description="SQS receipt handle for message deletion"),
    tenant: str = Depends(get_current_tenant)
) -> InternalFollowupResponse:
    try:
        followup_service = FollowupService()

        # Build visitor context
        visitor_context = await followup_service.context_builder.build_context(event_data)

        # Generate note and delete SQS message
        result = await followup_service.generate_enhanced_summary_note(
            event_data, visitor_context, receipt_handle=receipt_handle
        )

        return InternalFollowupResponse(
            note_id=str(result['note_id']),
            status="completed",
            confidence_score=result['ai_note']['confidence_score'],
            generation_timestamp=result['ai_note']['generation_timestamp'],
            processing_mode="sync"
        )

    except Exception as e:
        logger.error(f"Error processing missing SQS message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process missing SQS message")

# ============================================================================
# FEEDBACK ENDPOINT
# ============================================================================

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit Feedback on AI-Generated Note",
    description="Submit admin feedback on AI-generated notes for continuous improvement and quality assurance."
)
async def submit_note_feedback(
    request: SubmitFeedbackRequest,
    tenant: str = Depends(get_current_tenant)
) -> FeedbackResponse:
    """
    Submit feedback on an AI-generated visitor follow-up note.
    
    This endpoint allows administrators to:
    - Rate the quality and accuracy of AI-generated notes
    - Provide specific feedback on recommendations
    - Flag notes that need human review
    - Contribute to AI model improvement
    
    Feedback is used to:
    - Improve future AI note generation
    - Identify patterns in note quality
    - Train and refine AI models
    - Provide quality metrics for administrators
    """
    try:
        followup_service = FollowupService(tenant)
        
        result = await followup_service.submit_feedback(
            request.note_id,
            request.feedback
        )
        
        return FeedbackResponse(
            feedback_id=result['feedback_id'],
            status=result['status'],
            note_id=request.note_id
        )
        
    except ValueError as e:
        logger.warning(f"Invalid feedback submission: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def followup_health_check():
    """Health check endpoint for consolidated follow-up service."""
    return {
        "status": "healthy",
        "service": "followup-consolidated",
        "endpoints": [
            "/followup/internal/generate",
            "/followup/feedback"
        ],
        "message": "Consolidated follow-up service is operational"
    }


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def _process_note_async(
    followup_service: FollowupService,
    event_data: VisitorEventData
) -> None:
    """
    Background task for asynchronous note processing.
    
    This handles:
    - Large data collection operations
    - Complex family scenario analysis
    - AI processing that might take longer
    - Database operations across multiple services
    """
    try:
        result = await followup_service.generate_enhanced_summary_note(event_data)
        logger.info(f"Async note generation completed for event {event_data.event_id}")
        
        # Could trigger notifications, webhooks, or additional processing here
        
    except Exception as e:
        logger.error(f"Async note generation failed for event {event_data.event_id}: {str(e)}")
        # Could trigger error notifications or retry mechanisms here
