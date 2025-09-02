from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

class AIRecommendationLog(Base, TimestampMixin, SchemaConfigMixin):
    """Individual recommendation items with relaxed constraints for secondary service."""
    __tablename__ = "ai_recommendation_log"

    # Ensure UUID generation (fixes null constraint violation)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    
    # Foreign key relationships REMOVED - references only
    person_id = Column(UUID(as_uuid=True), nullable=True, comment="Reference to ai_person.id (no FK constraint)")
    note_id = Column(Integer, nullable=True, comment="Reference to ai_notes.id (no FK constraint)")
    task_id = Column(Integer, nullable=True, comment="Reference to ai_task.id (no FK constraint)")
    
    # Legacy fields (keep for backward compatibility)
    module_name = Column(String(50), nullable=True, comment="Module or context of the recommendation")
    recommended_entity_type = Column(String(50), nullable=True, comment="Type of entity recommended")
    recommended_entity_id = Column(String(50), nullable=True, comment="ID of the recommended entity")
    recommendation_score = Column(Integer, nullable=True, comment="Score or rank of the recommendation")
    recommendation_tier = Column(String(25), nullable=True, comment="Tier or category of the recommendation")
    rationale = Column(Text, nullable=True)
    
    # New detailed fields (from RecommendationItem model)
    text = Column(Text, nullable=False, comment="Human-readable recommendation text")
    section = Column(String(100), nullable=True, comment="Bucket/category (e.g., 'event_engagement')")
    priority = Column(String(20), default="normal", nullable=False, comment="low|normal|high")
    confidence = Column(Float, nullable=True, comment="Confidence score 0.0-1.0")
    tags = Column(ARRAY(String), nullable=True, comment="Array of tags")
    
    # Source tracking
    scenario_type = Column(String(50), nullable=True, comment="Scenario type (e.g., family_new)")
    source = Column(String(100), default="followup_note_agent", nullable=True, comment="Agent/system that produced the recommendation")
    model_version = Column(String(50), nullable=True, comment="AI model version used")
    suggested_by = Column(String(20), default="ai", nullable=False, comment="ai|human|system")
    
    # Suppression tracking (separate from ai_suppression_log for item-level suppression)
    suppressed = Column(Boolean, default=False, nullable=False)
    suppress_reason = Column(Text, nullable=True)
    
    # Additional metadata
    meta = Column(JSONB, nullable=True, comment="Free-form extra context")

    # Relationships removed since no FK constraints
    
    def __repr__(self):
        return f"<AIRecommendationLog(id={self.id}, text='{self.text[:50]}...', priority='{self.priority}')>"
