from uuid import uuid4
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.database.models.base import Base
from app.database.models.common import TimestampMixin

class Notes(Base, TimestampMixin):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer)
    person_id = Column(UUID(as_uuid=True), ForeignKey("demo.person.id"))
    task_assignee_id = Column(Integer)
    recipient_id = Column(Integer)
    recipient_fam_id = Column(Integer)
    
    title = Column(String)
    notes_body = Column(String)
    note_link = Column(String)
    note_photos = Column(String)
    file_attachment = Column(String)

    is_ai_generated = Column(Boolean, default=False, nullable=False)
    ai_generated_at = Column(DateTime(timezone=True))
    is_edited = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    

    
    # Relationships
    person = relationship("Person", back_populates="notes")
    


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