from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, Text, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from ..common import TimestampMixin, AIProcessingMixin, SchemaConfigMixin

class AITask(Base, TimestampMixin, AIProcessingMixin, SchemaConfigMixin):
    """AI-driven task model with relaxed constraints for secondary service."""
    __tablename__ = 'ai_task'
    
    # Core identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Task details
    task_title = Column(String(255), nullable=True)
    task_description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=True)
    task_status = Column(String(100), nullable=True)
    task_priority = Column(String(50), nullable=True)
    
    # Links to related entities (FK constraints removed)
    created_by = Column(UUID)
    recipient_id = Column(Integer, nullable=True)
    recipient_person_id = Column(UUID, nullable=True, comment="Reference to ai_person.id (no FK constraint)")
    recipient_family_id = Column(UUID, nullable=True, comment="Reference to ai_fam.id (no FK constraint)")
    task_assignee_id = Column(UUID, nullable=True)
    
    # Status tracking
    is_archived = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Assignment and routing
    follow_up_user = Column(String(100), nullable=True) 
    assign_usertype = Column(String(100), nullable=True)
    routed_to = Column(String(255), nullable=True)
    task_type_flag = Column(String(100), nullable=True)
    follow_up_prev_task = Column(Boolean, nullable=True)   
    
    # Relationships removed since no FK constraints
    
    def __repr__(self):
        return f"<AITask(id={self.id}, title='{self.task_title}', ai_agent='{self.ai_agent_type}', status='{self.task_status}')>"