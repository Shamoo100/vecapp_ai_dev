from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, UUID, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin, AIProcessingMixin

class AINotes(Base, TimestampMixin, AIProcessingMixin, SchemaConfigMixin):
    """AI-generated notes model with relaxed constraints for secondary service."""
    __tablename__ = 'ai_notes'
    
    # Core identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=True)
    
    # Links to related entities (FOREIGN KEYS REMOVED - references only)
    person_id = Column(UUID, nullable=True, comment="Person who wrote the note, in AI context default ai ID")
    task_id = Column(Integer, nullable=True, index=True, comment="Reference to ai_task.id (no FK constraint)")
    task_assignee_id = Column(UUID, nullable=True)
    recipient_id = Column(UUID, nullable=True, comment="Reference to ai_person.id (no FK constraint)")
    recipient_family_id = Column(UUID, nullable=True, comment="Reference to ai_fam.id (no FK constraint)")
    
    # Note content
    notes_body = Column(Text, nullable=True)
    note_link = Column(String(255), nullable=True)
    meta = Column(JSONB, nullable=True, comment="Additional metadata, e.g., tags, categories, etc.")
    
    # AI-specific metadata
    ai_generated = Column(Boolean, default=True, nullable=False)
    ai_model_used = Column(String(100), nullable=True, comment="Model name used for generation")
    ai_generation_prompt = Column(Text, nullable=True)
    ai_review_status = Column(String(50), default='pending', nullable=False)
    
    # Enhanced AI tracking
    scenario_type = Column(String(50), nullable=True, comment="Type of scenario (e.g., family_new, individual_visit)")
    generation_source = Column(String(100), nullable=True, comment="Source system/agent that generated this note")
    quality_score = Column(Float, nullable=True, comment="AI quality assessment score")
    
    # Status tracking
    is_edited = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships (viewonly=True since no FK constraints)
    # Note: These will work for queries but won't enforce referential integrity
    
    def __repr__(self):
        return f"<AINotes(id={self.id}, person_id={self.person_id}, ai_model='{self.ai_model_used}')>"