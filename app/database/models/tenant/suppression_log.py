from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

class AISuppressionLog(Base, TimestampMixin, SchemaConfigMixin):
    """Track system-level suppression events with relaxed constraints for secondary service."""
    __tablename__ = "ai_suppression_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    
    # Entity being suppressed (FK constraint removed)
    person_id = Column(UUID(as_uuid=True), nullable=False, comment="Reference to ai_person.id (no FK constraint)")
    suppressed_entity_type = Column(String(50), nullable=False, comment="Type: recommendation, note, task, etc.")
    suppressed_entity_id = Column(String(50), nullable=True, comment="ID of suppressed entity")
    
    # Suppression details
    reason = Column(Text, nullable=False, comment="Reason for suppression")
    suppression_type = Column(String(50), nullable=False, comment="manual, automatic, policy, etc.")
    module_name = Column(String(50), nullable=True, comment="Module that triggered suppression")
    
    # Context and metadata
    suppressed_by_user_id = Column(UUID, nullable=True, comment="User who initiated suppression")
    auto_suppression_rule = Column(String(100), nullable=True, comment="Rule that triggered auto-suppression")
    meta = Column(JSONB, nullable=True, comment="Additional suppression context")
    
    # Relationships removed since no FK constraints
    
    def __repr__(self):
        return f"<AISuppressionLog(id={self.id}, entity_type='{self.suppressed_entity_type}', reason='{self.reason[:50]}...')>"
