from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import datetime, date

# AI Person Schemas
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

# AI Notes Schemas
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

# AI Task Schemas
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
    
    class Config:
        from_attributes = True