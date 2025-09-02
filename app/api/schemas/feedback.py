from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class FeedbackHelpfulness(str, Enum):
    """Enumeration for feedback helpfulness rating"""
    YES = "yes"
    NO = "no"
    PARTIALLY = "partially"

class SubmitFeedbackRequest(BaseModel):
    """Request model for submitting feedback on AI-generated notes"""
    task_id: Optional[int] = Field(None, description="ID of the AI-generated note") 
    note_id: int = Field(..., description="ID of the AI-generated note")
    visitor_id: UUID = Field(..., description="ID of the visitor the note is about")
    admin_id: UUID = Field(..., description="ID of the admin submitting feedback")
    tenant_schema: str = Field(..., description="Tenant ID for multi-tenancy")
    helpfulness: FeedbackHelpfulness = Field(..., description="How helpful was the AI-generated note")
    comment: Optional[str] = Field(None, max_length=100, description="Optional comment (max 100 characters)")
    
    @validator('comment')
    def validate_comment(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "note_id": 123,
                "visitor_id": "550e8400-e29b-41d4-a716-446655440000",
                "admin_id": "550e8400-e29b-41d4-a716-446655440001",
                "tenant_schema": "test",
                "helpfulness": "yes",
                "comment": "Very insightful analysis of visitor behavior"
            }
        }

class FeedbackResponse(BaseModel):
    """Response model for feedback operations"""
    feedback_id: str = Field(..., description="ID of the submitted feedback")
    status: str = Field(..., description="Status of the feedback submission")
    note_id: int = Field(..., description="ID of the note that received feedback")
    
    class Config:
        schema_extra = {
            "example": {
                "feedback_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "submitted",
                "note_id": 123
            }
        }