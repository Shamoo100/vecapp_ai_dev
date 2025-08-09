from datetime import date, datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, Enum as SQLEnum, Date, UniqueConstraint, Index
from sqlalchemy.sql import text
from sqlalchemy.orm import declarative_base, relationship
from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4
from sqlalchemy import func, Index

class ReportType(Enum):
    SNAPSHOT = "Snapshot"
    JOURNEY = "Journey"
    WEEKLY = "Weekly"

class Report(Base, TimestampMixin, SchemaConfigMixin):
    __tablename__ = 'reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, comment="Unique identifier for the report")
    admin_id = Column(UUID(as_uuid=True), nullable=False, comment="Admin who created the report")
    report_type = Column(String(50), nullable=False, comment="Type of report, e.g., Snapshot, Journey, Weekly")
    date_range_start = Column(Date, nullable=False, comment="Start date of the report period")
    date_range_end = Column(Date, nullable=False, comment="End date of the report period")
    purpose = Column(String(255), comment="Purpose or context of the report")
    content = Column(JSONB, nullable=False, comment="Content of the report")  # Store report content in JSON format
    generated_by = Column(String(255), nullable=False, comment="User or system that generated the report")
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="Timestamp when the report was generated")


    def __repr__(self):
        return f"<Report(id={self.id}, tenant_id={self.tenant_id}, type={self.report_type}, start={self.date_range_start}, end={self.date_range_end})>"
