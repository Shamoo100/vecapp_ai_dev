from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import logging

from app.services.followup_service import FollowupService
from app.api.schemas.event_schemas import VisitorEventData, AINoteFeedback
from app.security.dependencies import get_current_tenant
from app.database.repositories.tenant_context import TenantContextMiddleware

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/visitor-followup", tags=["Visitor Follow-up"])


class GenerateNoteRequest(BaseModel):
    """Request model for generating visitor follow-up notes."""
    event_data: VisitorEventData
    priority: Optional[str] = "medium"
    async_processing: Optional[bool] = False


class GenerateNoteResponse(BaseModel):
    """Response model for note generation."""
    note_id: str
    status: str
    confidence_score: float
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


@router.post(
    "/generate-note",
    response_model=GenerateNoteResponse,
    summary="Generate AI-Powered Visitor Follow-up Note",
    description="Generate a comprehensive AI-powered follow-up note for a church visitor using enhanced data collection and analysis."
)
async def generate_visitor_note(
    request: GenerateNoteRequest,
    background_tasks: BackgroundTasks,
    tenant: str = Depends(get_current_tenant)
) -> GenerateNoteResponse:
    """
    Generate an AI-powered visitor follow-up note with comprehensive analysis.
    
    This endpoint:
    - Collects data from multiple sources (visitor profile, welcome form, notes, etc.)
    - Performs AI analysis for sentiment, interests, and recommendations
    - Generates structured recommendations across four categories
    - Saves the note to both member service and AI audit databases
    - Supports both synchronous and asynchronous processing
    """
    try:
        followup_service = FollowupService(tenant)
        
        if request.async_processing:
            # Process in background for large data sets
            background_tasks.add_task(
                _process_note_async,
                followup_service,
                request.event_data
            )
            
            return GenerateNoteResponse(
                note_id=f"async_{request.event_data.event_id}",
                status="processing",
                confidence_score=0.0,
                generation_timestamp=request.event_data.timestamp,
                processing_mode="async"
            )
        else:
            # Synchronous processing
            result = await followup_service.generate_enhanced_summary_note(request.event_data)
            
            return GenerateNoteResponse(
                note_id=str(result['note_id']),
                status="completed",
                confidence_score=result['ai_note']['confidence_score'],
                generation_timestamp=result['ai_note']['generation_timestamp'],
                processing_mode="sync"
            )
            
    except ValueError as e:
        logger.warning(f"Invalid request for note generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating visitor note: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate visitor note")


@router.post(
    "/submit-feedback",
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


@router.get(
    "/note/{note_id}",
    summary="Get AI-Generated Note with Feedback",
    description="Retrieve an AI-generated note with any associated admin feedback and quality metrics."
)
async def get_note_with_feedback(
    note_id: str,
    tenant: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Retrieve an AI-generated note with feedback history.
    
    Returns:
    - The original AI-generated note
    - All feedback submissions
    - Quality metrics and confidence scores
    - Generation metadata
    """
    try:
        followup_service = FollowupService(tenant)
        
        result = await followup_service.get_note_with_feedback(note_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving note: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve note")


@router.post(
    "/legacy/generate",
    summary="Legacy Note Generation (Backward Compatibility)",
    description="Legacy endpoint for backward compatibility with existing integrations."
)
async def legacy_generate_note(
    schema_name: str,
    person_id: int,
    task_id: int,
    tenant: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Legacy endpoint for generating visitor notes.
    Maintained for backward compatibility with existing systems.
    """
    try:
        followup_service = FollowupService(tenant)
        
        result = await followup_service.generate_summary_note(
            schema_name, person_id, task_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in legacy note generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate note")


async def _process_note_async(
    followup_service: FollowupService,
    event_data: VisitorEventData
) -> None:
    """
    Background task for asynchronous note processing.
    Used for large data sets or when immediate response is not required.
    """
    try:
        result = await followup_service.generate_enhanced_summary_note(event_data)
        logger.info(f"Async note generation completed for event {event_data.event_id}")
        
        # Could trigger notifications or webhooks here
        
    except Exception as e:
        logger.error(f"Async note generation failed for event {event_data.event_id}: {str(e)}")
        # Could trigger error notifications here