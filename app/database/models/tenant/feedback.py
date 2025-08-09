from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

class FeedbackHelpfulness(str, PyEnum):
    """Feedback helpfulness rating enumeration."""
    YES = "yes"
    NO = "no"
    PARTIALLY = "partially"

class FeedbackTone(str, PyEnum):
    """Feedback tone enumeration."""
    POSITIVE = "positive"
    CONSTRUCTIVE = "constructive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class AIEntityType(str, PyEnum):
    """AI entity type enumeration for polymorphic feedback."""
    NOTE = "note"
    RECOMMENDATION = "recommendation"
    DECISION = "decision"
    TASK = "task"
    ANALYSIS = "analysis"

class AIFeedback(Base, TimestampMixin, SchemaConfigMixin):
    """Consolidated AI feedback model for all AI-generated content.
    
    This model combines feedback collection and analysis capabilities,
    supporting both user feedback and automated analysis of AI outputs.
    """
    __tablename__ = "ai_feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Polymorphic entity reference
    entity_type = Column(String(50), nullable=False)  # 'note', 'recommendation', 'decision', etc.
    # Person context (for all feedback types)
    person_id = Column(UUID(as_uuid=True), ForeignKey('ai_person.id'), nullable=False)
    
    #note refrence
    note_id = Column(Integer, ForeignKey('ai_notes.id'), nullable=True)
    #task refrence
    task_id = Column(Integer, ForeignKey('ai_task.id'), nullable=True)
    
    # User feedback fields (from AIFeedback)
    helpfulness = Column(String(20))  # Optional for automated analysis
    user_comment = Column(String(500))
    admin_id = Column(UUID(as_uuid=True))  # Who provided the feedback
    
    # Automated analysis fields (from AIFeedbackAnalysis)
    feedback_category = Column(String(100))
    tone = Column(String(25))  # 'positive', 'constructive', 'neutral', 'negative'
    suggested_action = Column(Text)
    analysis_text = Column(Text)  # Automated analysis content
    
    # AI metadata (consolidated)
    ai_model_version = Column(String(50))
    ai_confidence_score = Column(Float)  # 0.0 to 1.0
    confidence_score_int = Column(Integer)  # For backward compatibility (0-100)
    
    # Feedback type and source tracking
    is_user_feedback = Column(Boolean, default=False)  # True if from user, False if automated
    is_automated_analysis = Column(Boolean, default=False)  # True if AI-generated analysis
    
    # Relationships
    ai_person = relationship("AIPerson", back_populates="ai_feedback")
    ai_note = relationship("AINotes", back_populates="ai_feedback")
    
    def __repr__(self):
        return f"<AIFeedback(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id})>"