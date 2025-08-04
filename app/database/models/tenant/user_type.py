from sqlalchemy import Column, String, Integer, Boolean, Index
from sqlalchemy.orm import relationship

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin

class UserType(Base, TimestampMixin, SchemaConfigMixin):
    """
    User type lookup table for categorizing users.
    Defines different types of users in the system (member, regular attendee, visitor).
    """
    __tablename__ = 'user_types'
    __table_args__ = (
        Index('idx_user_type_name', 'name'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    ai_persons = relationship("AIPerson", back_populates="user_type")
    
    def __repr__(self):
        return f"<UserType(id={self.id}, name='{self.name}', active={self.is_active})>"