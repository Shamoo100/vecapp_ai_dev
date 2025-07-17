from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin, AIProcessingMixin

class AINotes(Base, TimestampMixin, AIProcessingMixin, SchemaConfigMixin):
    """AI-generated notes model."""
    __tablename__ = 'ai_notes'
    
    # Core identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=True)
    
    # Links to related entities
    person_id = Column(UUID, nullable=True) #person who wrote the note, in AI context default ai ID
    task_id = Column(Integer, ForeignKey('ai_task.id'), nullable=True, index=True)
    task_assignee_id = Column(UUID, nullable=True)
    recipient_id = Column(UUID, ForeignKey('ai_person.id'), nullable=True)
    recipient_family_id = Column(UUID, ForeignKey('ai_fam.id'), nullable=True)
    
    # Note content
    notes_body = Column(Text, nullable=True)
    note_link = Column(String(255), nullable=True)
    meta = Column(JSONB, nullable=True, comment="Additional metadata, e.g., tags, categories, etc.")
    
    # AI-specific metadata (remove duplicates)
    ai_generated = Column(Boolean, default=True, nullable=False)
    ai_model_used = Column(String(100), nullable=True)  # Keep this, different from ai_model_version
    ai_generation_prompt = Column(Text, nullable=True)
    ai_review_status = Column(String(50), default='pending', nullable=False)
    
    # Status tracking
    is_edited = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    person = relationship("AIPerson", back_populates="ai_notes")
    task = relationship("AITask", back_populates="ai_notes")
    ai_feedback = relationship("AIFeedback", back_populates="ai_note")  # ADD
    ai_recommendation_logs = relationship("AIRecommendationLog", back_populates="ai_note")  # ADD
    
    def __repr__(self):
        return f"<AINotes(id={self.id}, person_id={self.person_id}, ai_model='{self.ai_model_used}')>"