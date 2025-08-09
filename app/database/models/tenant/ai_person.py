from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, UUID, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin  

class AIPerson(Base, TimestampMixin, SchemaConfigMixin):
    """
    Minimal person model for AI processing.
    Maintains consistency with member service schema while focusing on AI needs.
    """
    __tablename__ = 'ai_person'
    
    # Core identification (matching member service)
    id = Column(UUID, primary_key=True, index=True)  # Same UUID as member service
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    middle_name = Column(String(50), nullable=True)
    joined_via = Column(String(50), nullable=True)
    
    # Essential demographic info for AI context
    gender = Column(String(10), nullable=True)
    dob = Column(Date, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(25), nullable=True)
    
    # Family relationship
    fam_id = Column(UUID, nullable=True, index=True)  # Reference only
    fam_relationship = Column(String(50), nullable=True)  # relationship to family head
    is_adult = Column(Boolean, nullable=True)
    
    # User classification - Foreign Keys to lookup tables
    user_type_id = Column(Integer, ForeignKey('user_types.id'), nullable=True, index=True)
    user_status_id = Column(Integer, ForeignKey('user_statuses.id'), nullable=True, index=True)
    
    # Spiritual context for AI notes
    invited_on = Column(DateTime, default=func.now(), nullable=True)
    first_time_visit = Column(DateTime, default=func.now(), nullable=False)
    timezone = Column(String(50), nullable=True)
    time_to_contact = Column(String(50), nullable=True)
    joining_our_church = Column(String(50), nullable=True)
    daily_devotional = Column(String(50), nullable=True)
    just_relocated = Column(String(50), nullable=True)
    consider_joining = Column(String(50), nullable=True)
    feedback = Column(String(250), nullable=True)
    baptism_date = Column(Date, nullable=True)
    conversion_date = Column(Date, nullable=True)
    membership_date = Column(Date, nullable=True)
    spiritual_need = Column(Text, nullable=True)
    spiritual_challenge = Column(Text, nullable=True)
    prayer_request = Column(Text, nullable=True)
    
    # AI Processing Status
    ai_note_generated = Column(Boolean, default=False, nullable=False)
    ai_processing_status = Column(String(50), default='pending', nullable=False)
    ai_confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    ai_model_version = Column(String(50), nullable=True)
    last_ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships - Remove the problematic family relationship
    user_type = relationship("UserType", back_populates="ai_persons")
    user_status = relationship("UserStatus", back_populates="ai_persons")
    ai_notes = relationship("AINotes", back_populates="person", cascade="all, delete-orphan")
    ai_tasks = relationship("AITask", back_populates="person", cascade="all, delete-orphan")
    ai_feedback = relationship("AIFeedback", back_populates="ai_person", cascade="all, delete-orphan")
    ai_decision_audits = relationship("DecisionAudit", back_populates="ai_person", cascade="all, delete-orphan")
    ai_recommendation_logs = relationship("AIRecommendationLog", back_populates="ai_person", cascade="all, delete-orphan")
    ai_suppression_logs = relationship("SuppressionLog", back_populates="ai_person", cascade="all, delete-orphan")
    # family = relationship("AIFam", back_populates="family_members", foreign_keys=[fam_id], viewonly=True)  # REMOVED
    
    def __repr__(self):
        return f"<AIPerson(id={self.id}, name='{self.first_name} {self.last_name}', ai_status='{self.ai_processing_status}')>"