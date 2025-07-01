from datetime import date, datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, Enum as SQLEnum, Date, UniqueConstraint, Index
from sqlalchemy.sql import text
from sqlalchemy.orm import declarative_base, relationship
from app.database.models.base import Base
from app.database.models.common import TimestampMixin


# Enums for constrained choices
class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class MaritalStatus(Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"

class CommunicationMethod(Enum):
    EMAIL = "Email"
    PHONE = "Phone"
    SMS = "SMS"
    MAIL = "Mail"

class FamilyRelationship(Enum):
    SPOUSE = "Spouse"
    CHILD = "Child"
    PARENT = "Parent"
    SIBLING = "Sibling"
    OTHER = "Other"

class Visitor(Base, TimestampMixin):
    __tablename__ = 'visitors'
    __table_args__ = {'schema': 'demo'}
    
    visitor_id = Column(Integer, primary_key=True, autoincrement=True)
    # Basic Information
    title = Column(String(20), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    race = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    marital_status = Column(SQLEnum(MaritalStatus), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    preferred_communication_method = Column(SQLEnum(CommunicationMethod), nullable=False)
    best_contact_time = Column(String(50), nullable=False)
    receive_devotionals = Column(Boolean, nullable=False)
    occupation = Column(String(100), nullable=False)
    relocated = Column(Boolean, nullable=False)
    how_heard = Column(String(100), nullable=False)
    joining_church_consideration = Column(Boolean, nullable=False)
    joining_church_contact_time = Column(String(50), nullable=False)
    prayer_request = Column(Text, nullable=False)
    feedback = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    

    
    # Relationships
    family_members = relationship("FamilyMember", back_populates="visitor")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('email', 'phone', name='uix_visitor_contact'),
        Index('idx_visitor_name', 'first_name', 'last_name'),
    )

class FamilyMember(Base, TimestampMixin):
    __tablename__ = 'family_members'
    __table_args__ = {'schema': 'demo'}
    
    family_member_id = Column(Integer, primary_key=True, autoincrement=True)
    visitor_id = Column(Integer, ForeignKey('visitors.visitor_id'), nullable=False)
    
    # Family Member Information
    title = Column(String(20), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    family_relationship = Column(SQLEnum(FamilyRelationship), nullable=False)
    

    
    # Relationships
    visitor = relationship("Visitor", back_populates="family_members")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('email', 'phone', name='uix_family_contact'),
        Index('idx_family_relationship', 'family_relationship'),
    )