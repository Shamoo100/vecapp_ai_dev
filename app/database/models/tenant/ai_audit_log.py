"""
AI Service Audit Log Model
Tracks all admin actions and system events for audit purposes.
"""
from sqlalchemy import Column, String, Text, DateTime, Index, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin


class AIAuditLog(Base, TimestampMixin, SchemaConfigMixin):
    """
    Audit log for AI service admin actions and system events.
    Stores detailed information about who did what and when.
    """
    __tablename__ = 'ai_audit_log'
    __table_args__ = (
        Index('idx_ai_audit_user_id', 'user_id'),
        Index('idx_ai_audit_action', 'action'),
        Index('idx_ai_audit_timestamp', 'timestamp'),
        Index('idx_ai_audit_tenant_id', 'tenant_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User and tenant context
    user_id = Column(UUID(as_uuid=True), nullable=False, comment="User ID from X-auth-user header")
    user_email = Column(String(255), nullable=False, comment="User email for readability")
    tenant_id = Column(String(255), nullable=False, comment="Tenant ID from X-request-tenant header")
    
    # Action details
    action = Column(String(100), nullable=False, comment="Action performed (e.g., 'feedback_submit')")
    resource_type = Column(String(50), nullable=True, comment="Type of resource affected")
    resource_id = Column(String(255), nullable=True, comment="ID of affected resource")
    
    # Request context
    endpoint = Column(String(255), nullable=True, comment="API endpoint called")
    http_method = Column(String(10), nullable=True, comment="HTTP method used")
    ip_address = Column(INET, nullable=True, comment="Client IP address")
    user_agent = Column(Text, nullable=True, comment="Client user agent")
    
    # Event details
    details = Column(JSONB, nullable=True, comment="Additional event details as JSON")
    success = Column(String(10), nullable=False, default='true', comment="Whether action succeeded")
    error_message = Column(Text, nullable=True, comment="Error message if action failed")
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    duration_ms = Column(String(20), nullable=True, comment="Request duration in milliseconds")

    def __repr__(self):
        return f"<AIAuditLog(id={self.id}, user={self.user_email}, action={self.action})>"