from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database.models.base import Base
from app.database.models.common import TimestampMixin

class SuppressionLog(Base,TimestampMixin):
    __tablename__ = "ai_suppression_log"
    __table_args__ = {"schema": "demo"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(Text)
    module_name = Column(String(50))
    suppressed_entity_id = Column(String(50))
