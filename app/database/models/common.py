from sqlalchemy import (
    Column, String,Integer,
    DateTime, Enum as SQLEnum,func,
    Float, Text 
)
from app.database.models.enums import Gender, FollowUpType

# common.py
class PersonMixin:
    """Common fields for person-like models."""
    title = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    # etc.


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns to models."""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class SchemaConfigMixin:
    """
    Mixin for schema configuration.
    
    This mixin should NOT set __table_args__ directly as it interferes
    with Alembic's auto-detection. Instead, models should handle their
    own schema configuration in their migration environment.
    """
    pass  # Empty mixin - schema is handled by migration environment


class AIProcessingMixin:
    """Mixin for AI processing metadata."""
    ai_confidence_score = Column(Float, nullable=True, comment="AI confidence score (0.0 to 1.0)")
    ai_model_version = Column(String(50), nullable=True, comment="Version of AI model used")
    ai_processing_status = Column(String(20), nullable=True, comment="Current processing status")
    processing_started_at = Column(DateTime(timezone=True), nullable=True, comment="When AI processing started")
    processing_completed_at = Column(DateTime(timezone=True), nullable=True, comment="When AI processing completed")
    retry_count = Column(Integer, default=0, nullable=True, comment="Number of processing retries")
    error_message = Column(Text, nullable=True, comment="Error message if processing failed")
    follow_up_note_type = Column(SQLEnum(FollowUpType), nullable=True, comment="Type of follow-up note")