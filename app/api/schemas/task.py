from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class TaskBase(BaseModel):
    """Base schema for tasks."""
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: str = Field(..., description="Task priority level (low, medium, high, urgent)")
    status: str = Field(default="pending", description="Task status (pending, in_progress, completed, cancelled)")
    assigned_to: Optional[UUID] = Field(None, description="ID of the person assigned to the task")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    category: Optional[str] = Field(None, description="Task category")
    tags: Optional[List[str]] = Field(default=[], description="Task tags")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    created_by: UUID = Field(..., description="ID of the person who created the task")
    tenant_id: int = Field(..., description="Tenant ID")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[str] = Field(None, description="Task priority level")
    status: Optional[str] = Field(None, description="Task status")
    assigned_to: Optional[UUID] = Field(None, description="ID of the person assigned to the task")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    category: Optional[str] = Field(None, description="Task category")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    completion_notes: Optional[str] = Field(None, description="Notes upon task completion")


class TaskResponse(TaskBase):
    """Schema for task API responses."""
    model_config = {"from_attributes": True}
    
    id: UUID = Field(description="Unique task identifier")
    tenant_id: int = Field(description="Tenant ID")
    created_by: UUID = Field(description="ID of the person who created the task")
    completion_notes: Optional[str] = Field(None, description="Notes upon task completion")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    created_at: datetime = Field(description="Task creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TaskListResponse(BaseModel):
    """Schema for paginated task list responses."""
    tasks: List[TaskResponse] = Field(description="List of tasks")
    total: int = Field(description="Total number of tasks")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    has_next: bool = Field(description="Whether there are more pages")
    has_prev: bool = Field(description="Whether there are previous pages")


class VolunteerAssignmentBase(BaseModel):
    """Base schema for volunteer assignments."""
    person_id: UUID = Field(..., description="ID of the person to be assisted")
    volunteer_id: UUID = Field(..., description="ID of the assigned volunteer")
    assignment_type: str = Field(..., description="Type of assignment")
    priority: str = Field(..., description="Assignment priority level")
    notes: Optional[str] = Field(None, description="Additional assignment notes")
    task_id: Optional[UUID] = Field(None, description="Related task ID")


class VolunteerAssignmentCreate(VolunteerAssignmentBase):
    """Schema for creating a new volunteer assignment."""
    tenant_id: int = Field(..., description="Tenant ID")
    created_by: UUID = Field(..., description="ID of the person who created the assignment")


class VolunteerAssignmentUpdate(BaseModel):
    """Schema for updating a volunteer assignment."""
    assignment_type: Optional[str] = Field(None, description="Type of assignment")
    priority: Optional[str] = Field(None, description="Assignment priority level")
    notes: Optional[str] = Field(None, description="Additional assignment notes")
    status: Optional[str] = Field(None, description="Assignment status")
    completion_notes: Optional[str] = Field(None, description="Completion notes")


class VolunteerAssignmentResponse(VolunteerAssignmentBase):
    """Schema for volunteer assignment response data."""
    model_config = {"from_attributes": True}
    
    id: UUID = Field(description="Unique assignment identifier")
    tenant_id: int = Field(description="Tenant ID")
    created_by: UUID = Field(description="ID of the person who created the assignment")
    status: str = Field(description="Assignment status")
    completion_notes: Optional[str] = Field(None, description="Completion notes")
    completion_time: Optional[datetime] = Field(None, description="Assignment completion time")
    created_at: datetime = Field(description="Assignment creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class VolunteerAssignmentListResponse(BaseModel):
    """Schema for paginated volunteer assignment list responses."""
    assignments: List[VolunteerAssignmentResponse] = Field(description="List of volunteer assignments")
    total: int = Field(description="Total number of assignments")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    has_next: bool = Field(description="Whether there are more pages")
    has_prev: bool = Field(description="Whether there are previous pages")


class VolunteerPerformance(BaseModel):
    """Schema for volunteer performance metrics."""
    volunteer_id: UUID = Field(description="Volunteer ID")
    assignments_completed: int = Field(description="Number of completed assignments")
    average_response_time: float = Field(description="Average response time in hours")
    satisfaction_score: float = Field(description="Average satisfaction score")
    engagement_quality: float = Field(description="Engagement quality score")
    period_start: datetime = Field(description="Performance period start date")
    period_end: datetime = Field(description="Performance period end date")