from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

from app.database.models.base import Base, SchemaConfigMixin
from app.database.models.common import TimestampMixin

class AIFeedbackAnalysis(Base, TimestampMixin, SchemaConfigMixin):
    __tablename__ = "ai_feedback_analysis"
    __table_args__ = {"schema": "demo"}  # Default schema, can be changed via configure_schema()

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("demo.person.id"), nullable=False)
    feedback_category = Column(String(100))
    tone = Column(String(25))  # 'positive', 'constructive'
    suggested_action = Column(Text)
    feedback_text = Column(Text)
    confidence_score = Column(Integer)

    #Relationships
    person = relationship("Person", back_populates="feedback_analysis")
