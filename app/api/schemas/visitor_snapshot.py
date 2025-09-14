from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from enum import IntEnum

class NoteCriteria(IntEnum):
    """Note scope criteria for visitor snapshots"""
    FIRST_VISIT_ONLY = 0  # Only first time visit note and welcome form data
    ALL_NOTES = 1         # All notes attached to the family members

class FamilyCriteria(IntEnum):
    """Family grouping criteria for visitor snapshots"""
    GROUPED_BY_FAMILY = 0  # Group family members together
    INDIVIDUAL_SUMMARY = 1 # Keep as individual summary

class VisitorSnapshotRequest(BaseModel):
    """Request model for visitor snapshot pagination"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    note_criteria: NoteCriteria = Field(default=NoteCriteria.FIRST_VISIT_ONLY, description="0=first visit only, 1=all notes")
    family_criteria: FamilyCriteria = Field(default=FamilyCriteria.GROUPED_BY_FAMILY, description="0=grouped by family, 1=individual")
    report_purpose: Optional[str] = Field(default=None, max_length=500, description="Optional report purpose/label")

class NoteSummary(BaseModel):
    """Individual note summary entry"""
    date_created: datetime
    note_type: str  # e.g., "first time visit note", "follow up note"
    summary: str
    note_id: Optional[int] = None

class VisitorSummaryEntry(BaseModel):
    """Individual visitor snapshot entry"""
    visitor_id: UUID
    name: str
    first_visit_date: Optional[datetime]
    family_size: int
    family_members: List[str]
    contact_person: str
    visitor_summary: str
    sentiment_classification: str
    notes_scope_used: str
    report_purpose: Optional[str]
    note_summaries: List[NoteSummary] = Field(default_factory=list, description="Individual note summaries with dates and types")
    is_expanded: bool = False

class VisitorSnapshotResponse(BaseModel):
    """Response model for visitor snapshots"""
    entries: List[VisitorSummaryEntry]
    total_count: int
    page: int
    has_more: bool
    ai_disclaimer: str