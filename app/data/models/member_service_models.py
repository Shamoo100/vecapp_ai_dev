# app/data/models/member_service_models.py
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class _Model(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="ignore",
        validate_default=True,
        ser_json_inf_nan='null',
        frozen=True,
    )

class FamilyMember(_Model):
    id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    relationship: Optional[str] = None
    user_type_id: Optional[int] = None
    member_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PersonNote(_Model):
    id: int
    title: str
    person_id: Optional[UUID] = None
    notes_body: Optional[str] = None
    type: Optional[str] = None
    note_link: Optional[str] = None
    note_photos: Optional[List[str]] = None
    file_attachment: Optional[List[str]] = None
    is_edited: bool
    is_archived: bool
    task_id: Optional[int] = None
    task_assignee_id: Optional[int] = None
    recipient_id: Optional[UUID] = None
    recipient_fam_id: Optional[UUID] = None
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

class PersonProfile(_Model):
    id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    marital_status: Optional[str] = None
    wedding_date: Optional[date] = None
    join_date: Optional[date] = None
    membership_date: Optional[date] = None
    baptism_date: Optional[date] = None
    conversion_date: Optional[date] = None
    user_type_id: Optional[int] = None
    member_status: Optional[str] = None
    how_join: Optional[str] = None
    joined_via: Optional[str] = None
    is_verified: Optional[bool] = None
    has_account: Optional[bool] = None
    employment_status: Optional[str] = None
    employer: Optional[str] = None
    profession: Optional[str] = None
    job_title: Optional[str] = None
    highest_qualification: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    is_graduated: Optional[bool] = None
    spiritual_need: Optional[str] = None
    spiritual_challenge: Optional[str] = None
    prayer_request: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    fam_id: Optional[UUID] = None

    # joined family info
    family_head_first_name: Optional[str] = None
    family_head_last_name: Optional[str] = None
    fam_address: Optional[str] = None
    fam_city: Optional[str] = None
    fam_state: Optional[str] = None
    fam_country: Optional[str] = None
    fam_zip: Optional[str] = None

    # enrichment
    family_members: List[FamilyMember] = Field(default_factory=list)

class FamilyProfile(_Model):
    fam_id: UUID
    family_head_id: UUID
    family_size: Optional[int] = None
    family_head_first_name: Optional[str] = None
    family_head_last_name: Optional[str] = None
    family_head_spouse_first_name: Optional[str] = None
    family_head_email: Optional[str] = None
    family_head_phone: Optional[str] = None
    family_head_dob: Optional[date] = None 
    fam_address: Optional[str] = None
    fam_city: Optional[str] = None
    fam_state: Optional[str] = None
    fam_country: Optional[str] = None
    fam_zip: Optional[str] = None 
    family_members: List[FamilyMember] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

class Task(_Model):
    id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class FollowUpTask(_Model):
    id: int
    process_id: Optional[int] = None
    created_by: Optional[UUID] = None
    task_title: Optional[str] = None
    task_description: Optional[str] = None
    task_type: Optional[str] = None
    task_status: Optional[str] = None
    task_resolution: Optional[str] = None
    task_priority: Optional[str] = None
    task_planned_startdate: Optional[date] = None
    task_planned_enddate: Optional[date] = None
    task_actual_startdatetime: Optional[datetime] = None
    task_actual_enddatetime: Optional[datetime] = None
    recipient_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    assignees: List['TaskAssignee'] = Field(default_factory=list)
    task_notes: List['PersonNote'] = Field(default_factory=list)
    feedback: List['TaskFeedback'] = Field(default_factory=list)

class TaskAssignee(_Model):
    id: int
    task_id: int
    assignee_id: Optional[UUID] = None
    assignee_role_id: Optional[int] = None
    is_accept: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Enriched data
    assignee_name: Optional[str] = None
    assignee_email: Optional[str] = None
    role_title: Optional[str] = None

class TaskFeedback(_Model):
    id: int
    task_id: int
    is_contacted: Optional[str] = None
    has_responded: Optional[str] = None
    agreed_to_join: Optional[str] = None
    provided_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Enriched data
    provider_name: Optional[str] = None

class PrayerRequest(_Model):
    person_id: UUID
    prayer_request: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # From person table - prayer_request field
    person_name: Optional[str] = None

class PersonFeedback(_Model):
    person_id: UUID
    feedback: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # From person table - feedback field
    person_name: Optional[str] = None

class PersonDecision(_Model):
    person_id: UUID
    consider_joining: Optional[str] = None
    joining_our_church: Optional[str] = None
    daily_devotional: Optional[str] = None
    just_relocated: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # From person table decision fields
    person_name: Optional[str] = None

class JourneyReportData(_Model):
    """Comprehensive data model for journey report generation"""
    person_id: UUID
    person_profile: PersonProfile
    follow_up_tasks: List[FollowUpTask] = Field(default_factory=list)
    prayer_requests: List[PrayerRequest] = Field(default_factory=list)
    feedback_entries: List[PersonFeedback] = Field(default_factory=list)
    decisions: List[PersonDecision] = Field(default_factory=list)
    notes: List[PersonNote] = Field(default_factory=list)
    
    # Summary metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    last_contact_date: Optional[datetime] = None
    engagement_score: Optional[float] = None

class TaskAssignee(_Model):
    id: int
    task_id: int
    assignee_id: int
    role: Optional[str] = None
    created_at: datetime
    updated_at: datetime