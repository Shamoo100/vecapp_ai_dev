# app/data/models/ai_service_models.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union, List  # Add List import
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class _Model(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="ignore",
        validate_default=True,
        ser_json_inf_nan="null",
        frozen=True,
    )

# -----------------------------
# A) General Action Audit Log
#    (maps to AIAuditLog table)
# -----------------------------
class AuditLogEntry(_Model):
    user_id: UUID
    user_email: Optional[str] = None
    tenant_id: str
    # Remove duplicate fields
    action: str = Field(..., description="e.g., 'generate_followup_note'")
    resource_type: Optional[str] = Field(default=None, description="e.g., 'ai_note'")
    resource_id: Optional[Union[int, str]] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    success: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[str] = None

# -----------------------------
# B) Decision Audit Log
#    (maps to AIDecisionAudit table)
# -----------------------------
class DecisionAuditEntry(_Model):
    person_id: Optional[UUID]
    rule_id: Optional[str]
    rule_description: Optional[str]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    triggered: bool

# -----------------------------
# C) Task Note Audit Log
#    (maps to AITaskNote table)
# -----------------------------
class TaskNoteInput(_Model):
    # Task context (existing or new)
    task_id: Optional[int]
    task_title: Optional[str]
    task_description: Optional[str]
    task_status: str
    task_priority: str
    ai_agent_type: Optional[str]
    type: Optional[str]
    # IDs / context
    person_id: Optional[UUID]
    recipient_id: Optional[UUID]
    recipient_family_id: Optional[UUID]
    # Note payload
    note_title: Optional[str]
    note_body: str
    note_meta: Optional[Dict[str, Any]]

class TaskNoteResult(_Model):
    task_id: int
    note_id: int

# -----------------------------
# D) Feedback Audit Log
#    (maps to AIFeedback table)
# -----------------------------
class FeedbackInput(_Model):
    entity_type: str = Field(..., description="Type of entity (note, task, etc.)")
    person_id: UUID
    note_id: Optional[int]
    task_id: Optional[int]
    helpfulness: Optional[str]           # "yes" | "no" | "partially"
    user_comment: Optional[str]
    admin_id: Optional[UUID]
    ai_model_version: Optional[str]
    ai_confidence_score: Optional[float]

# -----------------------------
# E) Recommendation Log payload
#    (maps to RecommendationLog table)
# -----------------------------
class RecommendationItem(_Model):
    """
    One normalized recommendation item (one DB row per item).
    section: bucket/area the recommendation belongs to
             examples: "event_engagement", "church_integration",
                       "personal_needs", "feedback_insights"
    """
    text: str = Field(..., description="Human-readable recommendation")
    section: Optional[str] = Field(default=None, description="Bucket/category (e.g., 'event_engagement')")
    priority: Optional[str] = Field(default="normal", description="low|normal|high")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None

    suggested_by: Optional[str] = Field(default="ai", description="ai|human|system")
    suppressed: bool = Field(default=False)
    suppress_reason: Optional[str] = None

class RecommendationLogInput(_Model):
    """
    Batch wrapper: we typically log multiple recommendations per note/task.
    Repository will fan-out each item into a row in recommendation_log.
    """
    person_id: UUID
    note_id: Optional[int] = None
    task_id: Optional[int] = None

    scenario_type: Optional[str] = None              # e.g., "family_new", etc.
    source: Optional[str] = "followup_note_agent"    # agent/system that produced the recs
    model_version: Optional[str] = None              # e.g., "gemini-2.5-flash"

    items: List[RecommendationItem] = Field(default_factory=list)
    meta: Optional[Dict[str, Any]] = None            # free-form extra context

class RecommendationLogResult(_Model):
    """
    Result of creating recommendation log rows.
    """
    ids: List[Union[int, str]]
    count: int

# -----------------------------
# G) Suppression Log
#    (maps to AISuppressionLog table)
# -----------------------------
class SuppressionLogInput(_Model):
    """
    Input for creating suppression log entries.
    """
    person_id: UUID
    suppressed_entity_type: str = Field(..., description="Type: recommendation, note, task, etc.")
    suppressed_entity_id: Optional[str] = Field(None, description="ID of suppressed entity")
    reason: str = Field(..., description="Reason for suppression")
    suppression_type: str = Field(default="automatic", description="manual, automatic, policy, etc.")
    module_name: Optional[str] = Field(default=None, description="Module that triggered suppression")
    suppressed_by_user_id: Optional[UUID] = Field(None, description="User who initiated suppression")
    auto_suppression_rule: Optional[str] = Field(None, description="Rule that triggered auto-suppression")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional suppression context")

class SuppressionLogResult(_Model):
    """
    Result of creating suppression log entry.
    """
    id: UUID
    status: str

# -----------------------------
# F) AI Summary Audit Log
#    (maps to AISummary table)
# -----------------------------

@dataclass
class AISummaryResult:
    """Typed contract for AI summary generation results."""
    ok: bool
    reason: Optional[str] = None                 # "provider_timeout" | "quality_gate_failed" | "provider_error"
    summary: Optional[str] = None                # final admin-facing note content
    recommendations: Optional[List[Dict]] = None # structured recommendations
    quality_score: Optional[float] = None
    provider_meta: Dict[str, Any] = None         # model, tokens, latency, etc.
    
    def __post_init__(self):
        if self.provider_meta is None:
            self.provider_meta = {}