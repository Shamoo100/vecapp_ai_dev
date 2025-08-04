from sqlalchemy import Column, String, Integer, Boolean, Index
from sqlalchemy.orm import relationship

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

class UserStatus(Base, TimestampMixin, SchemaConfigMixin):
    """
    User status lookup table for tracking user lifecycle status.
    Defines different statuses like active, inactive, deceased.
    """
    __tablename__ = 'user_statuses'
    __table_args__ = (
        Index('idx_user_status_name', 'name'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    ai_persons = relationship("AIPerson", back_populates="user_status")
    
    def __repr__(self):
        return f"<UserStatus(id={self.id}, name='{self.name}', active={self.is_active})>"