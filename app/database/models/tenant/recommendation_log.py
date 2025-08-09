from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

class AIRecommendationLog(Base, TimestampMixin, SchemaConfigMixin):
    __tablename__ = "ai_recommendation_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    # Fix foreign key references to include tenant schema
    person_id = Column(UUID(as_uuid=True), ForeignKey('ai_person.id'), nullable=True)
    note_id = Column(Integer, ForeignKey('ai_notes.id'), nullable=True)
    task_id = Column(Integer, ForeignKey('ai_task.id'), nullable=True)
    module_name = Column(String(50), nullable=False, comment="Module or context of the recommendation")
    recommended_entity_type = Column(String(50), nullable=True, comment="Type of entity recommended  e,g decision, event, note",)
    recommended_entity_id = Column(String(50), nullable=True, comment="ID of the recommended entity")
    recommendation_score = Column(Integer, nullable=True, comment="Score or rank of the recommendation")
    recommendation_tier = Column(String(25), nullable=True, comment="Tier or category of the recommendation")
    rationale = Column(String)

    # Relationships
    ai_person = relationship("AIPerson", back_populates="ai_recommendation_logs")
    ai_note = relationship("AINotes", back_populates="ai_recommendation_logs")
    ai_task = relationship("AITask", back_populates="ai_recommendation_logs")
