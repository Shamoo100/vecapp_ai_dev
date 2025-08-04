from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Auth(Base, TimestampMixin, SchemaConfigMixin):
    """
    Authentication model for user login, roles, and permissions.
    Handles both authentication and authorization for tenant users.
    """
    __tablename__ = 'auth'
    __table_args__ = (
        Index('idx_auth_email', 'email'),
        Index('idx_auth_username', 'username'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Authentication fields
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    
    # User identification
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Authorization fields (JSON for flexibility)
    roles = Column(JSONB, nullable=False, default=list, comment="User roles as JSON array")
    permissions = Column(JSONB, nullable=False, default=list, comment="User permissions as JSON array")
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Password management
    password_changed_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = pwd_context.hash(password)
        self.password_changed_at = func.now()
    
    def verify_password(self, password: str) -> bool:
        """Verify the provided password against the stored hash."""
        return pwd_context.verify(password, self.password_hash)
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in (self.roles or [])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in (self.permissions or [])
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def __repr__(self):
        return f"<Auth(id={self.id}, username='{self.username}', email='{self.email}', active={self.is_active})>"