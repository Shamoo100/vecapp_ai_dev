from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class ReportStatus(str, Enum):
    """Status of a report"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportCreate(BaseModel):
    """Data needed to create a new report"""
    report_type: str = Field(default="followup_summary", description="Type of report to generate")
    date_range_start: datetime = Field(..., description="Start date for report data")
    date_range_end: datetime = Field(..., description="End date for report data")

class ReportResponse(BaseModel):
    """Data returned when fetching a report"""
    id: UUID = Field(..., description="Unique identifier for the report")
    status: ReportStatus = Field(..., description="Current status of the report")
    created_at: Optional[datetime] = Field(None, description="When the report was requested")
    updated_at: Optional[datetime] = Field(None, description="When the report was last updated")
    report_url: Optional[str] = Field(None, description="URL to download the report PDF")
    report_data: Optional[Dict[str, Any]] = Field(None, description="Summary data from the report")
    message: Optional[str] = Field(None, description="Additional information about the report")

class VisitorSummary(BaseModel):
    """Visitor summary section of the report"""
    total_visitors: int = Field(..., description="Total number of visitors")
    single_family: int = Field(..., description="Number of single-family engagements")
    multi_family: int = Field(..., description="Number of multi-family engagements")
    total_family_members: int = Field(..., description="Total number of family members")
    summary_text: str = Field(..., description="Summary analysis text")

class EngagementBreakdown(BaseModel):
    """Engagement breakdown section of the report"""
    interests: Dict[str, float] = Field(..., description="Interest categories to percentages")
    concerns: List[Dict[str, Any]] = Field(..., description="Common concerns with frequencies")
    needs: List[Dict[str, Any]] = Field(..., description="Identified needs with frequencies")
    feedback_sentiment: Dict[str, float] = Field(..., description="Sentiment analysis percentages")
    top_requests: List[Dict[str, Any]] = Field(..., description="Top requests with frequencies")
    summary_text: str = Field(..., description="Summary analysis text")

class OutcomeTrends(BaseModel):
    """Outcome trends section of the report"""
    decisions: Dict[str, float] = Field(..., description="Decision categories to percentages")
    reasons: List[Dict[str, Any]] = Field(..., description="Reasons for decisions with frequencies")
    next_steps: Dict[str, float] = Field(..., description="Next steps to percentages")
    correlations: List[str] = Field(..., description="Identified correlations between visitor traits and decisions")
    summary_text: str = Field(..., description="Summary analysis text")

class IndividualSummary(BaseModel):
    """Individual summary item"""
    visitor_id: str = Field(..., description="Visitor ID")
    family_id: Optional[str] = Field(None, description="Family ID if applicable")
    name: str = Field(..., description="Visitor name")
    summary: str = Field(..., description="Summarized follow-up notes")
    status: str = Field(..., description="Follow-up status")
    key_points: List[str] = Field(..., description="Key points extracted from notes")

class Recommendation(BaseModel):
    """Recommendation item"""
    recommendation: str = Field(..., description="The recommended action")
    rationale: str = Field(..., description="Rationale for the recommendation")
    impact: str = Field(..., description="Expected impact")
    priority: int = Field(..., description="Priority level (1-5)")

class FullReport(BaseModel):
    """Complete report data structure"""
    metadata: Dict[str, Any] = Field(..., description="Report metadata")
    visitor_summary: VisitorSummary = Field(..., description="Visitor summary section")
    engagement_breakdown: EngagementBreakdown = Field(..., description="Engagement breakdown section")
    outcome_trends: OutcomeTrends = Field(..., description="Outcome trends section")
    individual_summaries: List[IndividualSummary] = Field(..., description="Individual summaries section")
    recommendations: List[Recommendation] = Field(..., description="Recommendations section") 