"""
AI Rate Limiting Model
Tracks API usage for rate limiting across all tenants.
"""
from sqlalchemy import Column, String, DateTime, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..base import Base


class AIRateLimitLog(Base):
    """
    Rate limiting log stored in public schema for cross-tenant rate limiting.
    Tracks API calls to prevent abuse.
    """
    __tablename__ = 'ai_rate_limit_log'
    __table_args__ = (
        Index('idx_rate_limit_user_action', 'user_id', 'action'),
        Index('idx_rate_limit_timestamp', 'timestamp'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User and action
    user_id = Column(UUID(as_uuid=True), nullable=False, comment="User ID from headers")
    tenant_id = Column(String(255), nullable=False, comment="Tenant ID as in schema_name from headers")
    action = Column(String(100), nullable=False, comment="Action being rate limited")
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AIRateLimitLog(user_id={self.user_id}, action={self.action})>"