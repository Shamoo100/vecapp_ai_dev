from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, UUID, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin 

class AIFam(Base, TimestampMixin, SchemaConfigMixin):
    """
    Minimal family model for AI processing context.
    Stores essential family information needed for AI note generation.
    """
    __tablename__ = 'ai_fam'
    
    # Core identification (matching member service)
    id = Column(UUID, primary_key=True)  # Same UUID as member service
    first_name = Column(String(255), nullable=True)  # Family head first name
    last_name = Column(String(255), nullable=True)   # Family surname
    family_head = Column(UUID, nullable=True)  # Link to family head person
    family_size = Column(Integer, nullable=True)  # Number of family members

    # Remove the problematic relationship
    # family_members = relationship("AIPerson", back_populates="family", viewonly=True)  # REMOVED

    
    def __repr__(self):
        return f"<AIFam(id={self.id}, name='{self.first_name} {self.last_name}', size={self.family_size})>"
