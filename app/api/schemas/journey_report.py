from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

"follow up journey report request and response models"
# ============================================================================
# MODELS
# ============================================================================

class JourneyReportRequest(BaseModel):
    """Request model for journey report generation"""
    start_date: datetime = Field(..., description="Start date for first-time visits")
    end_date: datetime = Field(..., description="End date for first-time visits")
    report_purpose: Optional[str] = Field(None, max_length=500, description="Optional report purpose/label")

class VisitorJourneyEntry(BaseModel):
    """Individual visitor/family journey entry"""
    visitor_family_name: str
    follow_up_context: str  # "Individual" or "Family"
    family_size: int
    first_time_visit_date: datetime
    primary_contact: str
    contact_attempts: int
    task_summary: str  # e.g., "3 total – 2 completed, 1 pending"
    task_assignees: List[str]
    task_creation_date: Optional[datetime]
    task_completion_date: Optional[datetime]
    unresolved_needs: List[str]
    visitor_decision: str
    decision_rationale: str
    ai_recommendations: List[str]

class JourneyReportResponse(BaseModel):
    """Response model for journey report"""
    report_id: str
    generated_at: datetime
    report_purpose: Optional[str]
    date_range: dict
    summary_stats: dict
    entries: List[VisitorJourneyEntry]
    total_visitors: int
    visitors_joined: int
    visitors_undecided: int
    visitors_not_interested: int