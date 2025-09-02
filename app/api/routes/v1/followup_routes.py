"""
Consolidated Follow-up Routes for VecApp AI Service.

This module provides three main endpoints:
1. Internal follow-up note generation (event-driven processing)
2. Feedback submission for AI-generated notes
3. Visitor snapshot generation with AI summaries

Simplified and consolidated from multiple route files for better maintainability.
"""
from typing import Dict, Any, Optional
from fastapi import Header, APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import logging
import time
from app.security.dependencies import get_current_schema_name, get_current_tenant
from app.services.followup_service import FollowupService
from app.services.journey_report_service import JourneyReportService
from app.services.visitor_snapshot_service import VisitorSnapshotService
from app.api.schemas.event_schemas import VisitorEventData
from app.api.schemas.feedback import SubmitFeedbackRequest as FeedbackSubmitRequest, FeedbackResponse
from app.api.schemas.visitor_snapshot import (
    VisitorSnapshotRequest,
    VisitorSnapshotResponse,
    VisitorSummaryEntry
)
from app.api.schemas.journey_report import JourneyReportRequest, JourneyReportResponse, VisitorJourneyEntry


from fastapi import Body, Header

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


# ============================================================================
# ENDPOINTS
# ============================================================================
#feedback
@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit Feedback on AI-Generated Note",
    description="Submit admin feedback on AI-generated notes for continuous improvement and quality assurance."
)
async def submit_note_feedback(
    request: FeedbackSubmitRequest,  # Use the proper schema
    tenant: str = Depends(get_current_schema_name),
    x_request_tenant: str = Header(alias="X-Request-Tenant"),
    description="Tenant context (schema name)"
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
        # Initialize service
        followup_service = FollowupService()
        
        # Pass pydantic models to service
        result = await followup_service.submit_feedback(
            str(request.note_id),
            request,
            tenant=tenant
        )
        
        return FeedbackResponse(
            feedback_id=str(result.get('id', 'unknown')),
            status="submitted",
            note_id=request.note_id
        )
        
    except ValueError as e:
        logger.warning(f"Invalid feedback submission: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

#visitor snapshot
@router.post(
    "/visitor-snapshots",
    response_model=VisitorSnapshotResponse,
    summary="Get Visitor Snapshot Report",
    description="Retrieve AI-generated visitor snapshots with pagination support for recent church visitors"
)
async def get_visitor_snapshots(
    request: VisitorSnapshotRequest,
    tenant: str = Depends(get_current_schema_name),
    x_request_tenant: str = Header(alias="X-Request-Tenant")
) -> VisitorSnapshotResponse:
    """
    Generate AI-powered visitor snapshots with pagination support.
    
    This endpoint provides:
    - Paginated list of recent visitors
    - AI-generated summaries for each visitor
    - Family context and sentiment analysis
    - Contact information and preferences
    - Engagement recommendations
    
    Features:
    - Date range filtering (defaults to last 90 days)
    - Configurable page size (1-50 entries)
    - AI-powered visitor analysis
    - Family member integration
    - Sentiment classification
    
    Args:
        request: Pagination and filtering parameters
        tenant: Current tenant schema name
        x_request_tenant: Tenant header for validation
        
    Returns:
        VisitorSnapshotResponse with paginated visitor entries
    """
    try:
        # Validate tenant consistency
        if x_request_tenant != tenant:
            raise HTTPException(
                status_code=400, 
                detail="Tenant mismatch between header and authentication"
            )
        
        # Initialize visitor snapshot service
        snapshot_service = VisitorSnapshotService(tenant)
        await snapshot_service.initialize()
        
        try:
            # Generate visitor snapshots
            result = await snapshot_service.get_visitor_snapshots(
                request=request,
                tenant_id=tenant
            )
            
            logger.info(
                f"Generated {len(result.entries)} visitor snapshots for tenant {tenant}, "
                f"page {request.page}, total: {result.total_count}"
            )
            
            return result
            
        finally:
            # Ensure service cleanup
            await snapshot_service.close()
        
    except ValueError as e:
        logger.warning(f"Invalid visitor snapshot request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating visitor snapshots for tenant {tenant}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate visitor snapshots. Please try again later."
        )

#followup journey report

@router.post(
    "/journey",
    response_model=JourneyReportResponse,
    summary="Generate Follow-Up Journey Report",
    description="Generate AI-powered follow-up journey report for visitors within date range"
)
async def generate_journey_report(
    request: JourneyReportRequest,
    tenant: str = Depends(get_current_schema_name),
    x_request_tenant: str = Header(alias="X-Request-Tenant")
    
) -> JourneyReportResponse:
    """
        Generate a comprehensive follow-up journey report for visitors within a date range.
        
        This endpoint analyzes visitor follow-up journeys, including:
        - Task completion status and assignees
        - AI-powered sentiment analysis and decision prediction
        - Family grouping and engagement metrics
        - Unresolved needs and recommendations
        """
    #validate tenant consistency
    if x_request_tenant != tenant:
        raise HTTPException(
            status_code=400, 
            detail="Tenant mismatch between header and authentication"
        )
    #initialize journey report service
    service = JourneyReportService(tenant=tenant)
    return await service.generate_journey_report(request)

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
            "/followup/feedback",
            "/followup/visitor-snapshots"
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
        result = await followup_service.generate_followup_summary_note(event_data)
        logger.info(f"Async note generation completed for event {event_data.event_id}")
        
        # Could trigger notifications, webhooks, or additional processing here
        
    except Exception as e:
        logger.error(f"Async note generation failed for event {event_data.event_id}: {str(e)}")
        # Could trigger error notifications or retry mechanisms here
