from uuid import uuid4
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.models.base import Base

class Notes(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    person_id = Column(uuid4, ForeignKey("persons.id"))
    task_assignee_id = Column(Integer, ForeignKey("task_assignees.id"))
    recipient_id = Column(Integer, ForeignKey("recipients.id"))
    recipient_fam_id = Column(Integer, ForeignKey("recipient_families.id"))
    
    title = Column(String)
    notes_body = Column(String)
    note_link = Column(String)
    note_photos = Column(String)
    file_attachment = Column(String)

    is_ai_generated = Column(Boolean, default=False, nullable=False)
    ai_generated_at = Column(DateTime(timezone=True))
    is_edited = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    
    # Relationships
    task = relationship("Task", back_populates="notes")
    person = relationship("Person", back_populates="notes")
    task_assignee = relationship("TaskAssignee", back_populates="notes")
    recipient = relationship("Recipient", back_populates="notes")
    recipient_family = relationship("RecipientFamily", back_populates="notes")


# class VisitorNote(Base, TimestampMixin):
#     __tablename__ = 'visitor_note'
#     __table_args__ = {'schema': 'demo'}

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
#     visitor_id = Column(UUID(as_uuid=True), ForeignKey('demo.visitor.id'), nullable=False)
#     note_content = Column(Text, nullable=False)
#     is_ai_generated = Column(Boolean, default=False, nullable=False)
#     ai_generated_at = Column(DateTime(timezone=True))
#     sentiment = Column(String(50))
#     confidence_score = Column(Float)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())

#     visitor = relationship("Visitor", backref="notes")