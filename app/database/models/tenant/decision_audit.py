from uuid import uuid4
from sqlalchemy import Column, String, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..base import Base
from ..common import TimestampMixin, AIProcessingMixin, SchemaConfigMixin

class DecisionAudit(Base, TimestampMixin, AIProcessingMixin, SchemaConfigMixin):
    __tablename__ = "ai_decision_audit"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey('ai_person.id'), nullable=True)
    rule_id = Column(String(100), nullable=True)
    rule_description = Column(String, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    triggered = Column(Boolean, nullable=True)

    # Relationships
    ai_person = relationship("AIPerson", back_populates="ai_decision_audits")
