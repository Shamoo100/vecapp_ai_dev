from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime

class NotesBase(BaseModel):
    """Base schema for notes."""
    title: Optional[str] = Field(None, description="Title of the note")
    notes_body: Optional[str] = Field(None, description="Main content of the note")
    note_link: Optional[str] = Field(None, description="Link associated with the note")
    note_photos: Optional[List[str]] = Field(None, description="List of photo URLs")
    file_attachment: Optional[str] = Field(None, description="File attachment URL")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class NotesCreate(NotesBase):
    """Schema for creating a new note."""
    task_id: Optional[int] = Field(None, description="Associated task ID")
    person_id: Optional[UUID4] = Field(None, description="ID of the person the note is about")
    task_assignee_id: Optional[UUID4] = Field(None, description="ID of the task assignee")
    recipient_id: Optional[UUID4] = Field(None, description="ID of the recipient")
    recipient_fam_id: Optional[UUID4] = Field(None, description="Family ID of the recipient")

class NotesResponse(NotesBase):
    """Schema for note response."""
    id: int = Field(..., description="Unique note identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True