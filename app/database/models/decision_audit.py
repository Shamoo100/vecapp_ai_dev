from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID 
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, Enum as SQLEnum, Date, UniqueConstraint, Index
from app.database.models.base import Base, SchemaConfigMixin
from app.database.models.common import TimestampMixin
from sqlalchemy.orm import declarative_base, relationship

class DecisionAudit(Base, TimestampMixin, SchemaConfigMixin):
    __tablename__ = "ai_decision_audit"
    __table_args__ = {'schema': 'tenant'}  # Default schema, can be changed via configure_schema()

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey('person.id'), nullable=False)
    rule_id = Column(String(100))
    rule_description = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)
    triggered = Column(Boolean)

    # Relationships
    person = relationship("Person", back_populates="ai_decision_audit")
