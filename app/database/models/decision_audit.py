from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.database.models.base import Base, SchemaConfigMixin
from app.database.models.common import TimestampMixin

class DecisionAudit(Base, TimestampMixin, SchemaConfigMixin):
    __tablename__ = "ai_decision_audit"
    __table_args__ = {"schema": "demo"}  # Default schema, can be changed via configure_schema()

    id = Column(PostgresUUID, primary_key=True)
    person_id = Column(PostgresUUID, nullable=False)
    rule_id = Column(String(100))
    rule_description = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)
    triggered = Column(Boolean)
