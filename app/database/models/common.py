from sqlalchemy import (
    Column, String, Boolean, JSON, Integer, Date, 
    DateTime, Enum as SQLEnum, UniqueConstraint, text, func,
    Float, Text  # ADD THESE MISSING IMPORTS
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
    """Mixin for schema configuration."""
    __table_args__ = {'schema': None}  # Will be overridden by subclasses


class AIProcessingMixin:
    """Mixin for AI processing metadata."""
    ai_confidence_score = Column(Float)  # 0.0 to 1.0
    ai_model_version = Column(String(50))
    ai_processing_status = Column(String(20))
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    follow_up_note_type = Column(SQLEnum(FollowUpType))