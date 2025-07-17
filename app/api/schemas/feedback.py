from pydantic import BaseModel, Field, UUID4, validator
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
    note_id: int = Field(..., description="ID of the AI-generated note")
    visitor_id: UUID = Field(..., description="ID of the visitor the note is about")
    admin_id: UUID = Field(..., description="ID of the admin submitting feedback")
    tenant_id: int = Field(..., description="Tenant ID for multi-tenancy")
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
                "tenant_id": 1,
                "helpfulness": "yes",
                "comment": "Very insightful analysis of visitor behavior"
            }
        }

class FeedbackResponse(BaseModel):
    """Response model for feedback operations"""
    id: int
    note_id: int
    visitor_id: UUID
    admin_id: UUID
    tenant_id: int
    helpfulness: FeedbackHelpfulness
    comment: Optional[str]
    ai_model_version: Optional[str]
    ai_confidence_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "note_id": 123,
                "visitor_id": "550e8400-e29b-41d4-a716-446655440000",
                "admin_id": "550e8400-e29b-41d4-a716-446655440001",
                "tenant_id": 1,
                "helpfulness": "yes",
                "comment": "Very insightful analysis of visitor behavior",
                "ai_model_version": "gpt-4-turbo",
                "ai_confidence_score": 0.85,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

class FeedbackSubmissionResponse(BaseModel):
    """Response model for successful feedback submission"""
    success: bool = True
    message: str = "Feedback submitted successfully"
    feedback: FeedbackResponse
    note_updated: bool = Field(..., description="Whether the note was marked as feedback received")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Feedback submitted successfully",
                "feedback": {
                    "id": 1,
                    "note_id": 123,
                    "visitor_id": "550e8400-e29b-41d4-a716-446655440000",
                    "admin_id": "550e8400-e29b-41d4-a716-446655440001",
                    "tenant_id": 1,
                    "helpfulness": "yes",
                    "comment": "Very insightful analysis",
                    "ai_model_version": "gpt-4-turbo",
                    "ai_confidence_score": 0.85,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                },
                "note_updated": True
            }
        }

class GetFeedbackResponse(BaseModel):
    """Response model for retrieving feedback for a note"""
    note_id: int
    feedback_count: int
    feedback_received: bool
    feedback_list: list[FeedbackResponse]
    
    class Config:
        schema_extra = {
            "example": {
                "note_id": 123,
                "feedback_count": 2,
                "feedback_received": True,
                "feedback_list": [
                    {
                        "id": 1,
                        "note_id": 123,
                        "visitor_id": "550e8400-e29b-41d4-a716-446655440000",
                        "admin_id": "550e8400-e29b-41d4-a716-446655440001",
                        "tenant_id": 1,
                        "helpfulness": "yes",
                        "comment": "Very helpful",
                        "ai_model_version": "gpt-4-turbo",
                        "ai_confidence_score": 0.85,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }

# Add new consolidated feedback schemas
class AIFeedbackRequest(BaseModel):
    """Request model for submitting feedback on any AI-generated content"""
    entity_type: str = Field(..., description="Type of AI entity (note, task, recommendation)")
    entity_id: UUID4 = Field(..., description="ID of the AI-generated entity")
    admin_id: UUID4 = Field(..., description="ID of the admin submitting feedback")
    helpfulness: FeedbackHelpfulness = Field(..., description="How helpful was the AI content")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")
    
    class Config:
        schema_extra = {
            "example": {
                "entity_type": "note",
                "entity_id": "550e8400-e29b-41d4-a716-446655440000",
                "admin_id": "550e8400-e29b-41d4-a716-446655440001",
                "helpfulness": "yes",
                "comment": "Very insightful AI analysis"
            }
        }

class AIFeedbackResponse(BaseModel):
    """Response model for AI feedback operations"""
    model_config = {"from_attributes": True}
    
    id: UUID4
    entity_type: str
    entity_id: UUID4
    admin_id: UUID4
    helpfulness: FeedbackHelpfulness
    comment: Optional[str]
    ai_model_version: Optional[str]
    ai_confidence_score: Optional[float]
    created_at: datetime
    updated_at: datetime