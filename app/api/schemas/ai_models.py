from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, Field, UUID4, IPvAnyAddress

# --- AI Person Schemas ---

class AIPersonBase(BaseModel):
    """Base schema for AI Person"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fam_id: Optional[UUID4] = None
    relationship: Optional[str] = None
    is_adult: Optional[bool] = None
    spiritual_need: Optional[str] = None
    spiritual_challenge: Optional[str] = None
    prayer_request: Optional[str] = None

class AIPersonCreate(AIPersonBase):
    """Schema for creating AI Person"""
    id: UUID4 = Field(..., description="UUID from member service")

class AIPersonUpdate(BaseModel):
    """Schema for updating AI Person"""
    ai_note_generated: Optional[bool] = None
    ai_processing_status: Optional[str] = None
    ai_confidence_score: Optional[str] = None
    ai_model_version: Optional[str] = None
    last_ai_processed_at: Optional[datetime] = None

class AIPersonResponse(AIPersonBase):
    """Schema for AI Person response"""
    id: UUID4
    ai_note_generated: bool
    ai_processing_status: str
    ai_confidence_score: Optional[str] = None
    ai_model_version: Optional[str] = None
    last_ai_processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- AI Notes Schemas ---

class AINotesBase(BaseModel):
    """Base schema for AI Notes"""
    title: Optional[str] = None
    notes_body: Optional[str] = None
    note_link: Optional[str] = None
    ai_model_used: Optional[str] = None
    ai_confidence_score: Optional[str] = None
    ai_review_status: str = "pending"

class AINotesCreate(AINotesBase):
    """Schema for creating AI Notes"""
    person_id: Optional[UUID4] = None
    task_id: Optional[int] = None
    recipient_id: Optional[UUID4] = None
    ai_generation_prompt: Optional[str] = None

class AINotesResponse(AINotesBase):
    """Schema for AI Notes response"""
    id: int
    person_id: Optional[UUID4] = None
    task_id: Optional[int] = None
    ai_generated: bool
    is_edited: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- AI Task Schemas ---

class AITaskBase(BaseModel):
    """Base schema for AI Task"""
    task_title: Optional[str] = None
    task_description: Optional[str] = None
    task_type: Optional[str] = None
    task_status: Optional[str] = None
    task_priority: Optional[str] = None
    ai_agent_type: Optional[str] = None
    ai_task_reasoning: Optional[str] = None
    ai_suggested_approach: Optional[str] = None
    ai_confidence_score: Optional[str] = None

class AITaskCreate(AITaskBase):
    """Schema for creating AI Task"""
    person_id: Optional[UUID4] = None
    ai_auto_execute: bool = False

class AITaskResponse(AITaskBase):
    """Schema for AI Task response"""
    id: int
    person_id: Optional[UUID4] = None
    ai_generated: bool
    ai_auto_execute: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

# --- AI Audit Log Schema ---

class AIAuditLog(BaseModel):
    """Schema for AI audit logging"""
    id: Optional[int] = Field(None, description="Primary key ID")
    user_id: UUID = Field(..., description="User ID from X-auth-user header")
    user_email: str = Field(..., description="User email for readability")
    tenant_id: str = Field(..., description="Tenant ID from X-request-tenant header")
    action: str = Field(..., description="Action performed (e.g., 'feedback_submit')")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of affected resource")
    endpoint: Optional[str] = Field(None, description="API endpoint called")
    http_method: Optional[str] = Field(None, description="HTTP method used")
    ip_address: Optional[IPvAnyAddress] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional event details as JSON")
    success: str = Field("true", description="Whether action succeeded")
    error_message: Optional[str] = Field(None, description="Error message if action failed")
    timestamp: datetime = Field(..., description="When the action occurred")
    duration_ms: Optional[str] = Field(None, description="Request duration in milliseconds")

    class Config:
        from_attributes = True
