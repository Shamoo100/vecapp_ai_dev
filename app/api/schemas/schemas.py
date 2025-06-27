#\"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class VisitorBase(BaseModel):
    """Base schema for visitor data."""
    name: str = Field(..., description="Visitor's full name")
    email: str = Field(..., description="Visitor's email address")
    phone: Optional[str] = Field(None, description="Visitor's phone number")
    visit_purpose: str = Field(..., description="Purpose of the visit")
    notes: Optional[str] = Field(None, description="Additional notes about the visitor")

class VisitorCreate(VisitorBase):
    """Schema for creating a new visitor."""
    pass

class VisitorResponse(VisitorBase):
    """Schema for visitor response data."""
    id: str
    created_at: datetime
    status: str
    engagement_score: Optional[float] = None

    class Config:
        orm_mode = True

class VolunteerAssignmentBase(BaseModel):
    """Base schema for volunteer assignments."""
    visitor_id: str = Field(..., description="ID of the visitor to be assisted")
    volunteer_id: str = Field(..., description="ID of the assigned volunteer")
    assignment_type: str = Field(..., description="Type of assignment")
    priority: str = Field(..., description="Assignment priority level")
    notes: Optional[str] = Field(None, description="Additional assignment notes")

class VolunteerAssignmentCreate(VolunteerAssignmentBase):
    """Schema for creating a new volunteer assignment."""
    pass

class VolunteerAssignmentResponse(VolunteerAssignmentBase):
    """Schema for volunteer assignment response data."""
    id: str
    created_at: datetime
    status: str
    completion_time: Optional[datetime] = None

    class Config:
        orm_mode = True

class DashboardMetrics(BaseModel):
    """Schema for dashboard analytics metrics."""
    total_visitors: int
    active_engagements: int
    average_engagement_score: float
    volunteer_availability: float
    recent_activities: List[Dict[str, Any]]

class VisitorTrends(BaseModel):
    """Schema for visitor trend analytics."""
    time_periods: List[str]
    visitor_counts: List[int]
    engagement_rates: List[float]
    conversion_rates: List[float]

class VolunteerPerformance(BaseModel):
    """Schema for volunteer performance metrics."""
    volunteer_id: str
    assignments_completed: int
    average_response_time: float
    satisfaction_score: float
    engagement_quality: float

class FollowupNoteCreate(BaseModel):
    """Schema for creating a follow-up note."""
    visitor_id: str = Field(..., description="ID of the visitor")
    content: str = Field(..., description="Content of the follow-up note")
    note_type: str = Field(..., description="Type of follow-up note")
    priority: Optional[str] = Field(None, description="Priority level of the note")

class FollowupNoteResponse(FollowupNoteCreate):
    """Schema for follow-up note response data."""
    id: str
    created_at: datetime
    last_updated: datetime
    status: str

    class Config:
        orm_mode = True
