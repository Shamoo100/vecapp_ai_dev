from uuid import uuid4
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

class SuppressionLog(Base, TimestampMixin, SchemaConfigMixin):
    __tablename__ = "ai_suppression_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey('ai_person.id'), nullable=False)
    reason = Column(Text)
    module_name = Column(String(50))
    suppressed_entity_id = Column(String(50))

    # Relationships
    ai_person = relationship("AIPerson", back_populates="ai_suppression_logs")
