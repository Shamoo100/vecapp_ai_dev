from sqlalchemy import (
    Column, String, Boolean, JSON, Integer, Date, 
    DateTime, Enum as SQLEnum, UniqueConstraint, text, func
)
from app.database.models.enums import Gender

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