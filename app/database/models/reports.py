from datetime import date, datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, Enum as SQLEnum, Date, UniqueConstraint, Index
from sqlalchemy.sql import text
from sqlalchemy.orm import declarative_base, relationship
from app.database.models.base import Base, SchemaConfigMixin
from app.database.models.common import TimestampMixin
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4
from sqlalchemy import func, Index

class ReportType(Enum):
    SNAPSHOT = "Snapshot"
    JOURNEY = "Journey"
    WEEKLY = "Weekly"

class Report(Base, TimestampMixin, SchemaConfigMixin):
    __tablename__ = 'reports'
    __table_args__ = {'schema': 'tenant'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    report_type = Column(String(50), nullable=False)  # e.g., "Snapshot", "Journey", "Weekly"
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    purpose = Column(String(255))
    content = Column(JSONB)  # Store report content in JSON format
    generated_by = Column(String(255))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    church_branch = relationship("Tenants", backref="reports")