from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID
from enum import Enum

class CommunicationMethod(str, Enum):
    """Enum for communication methods"""
    EMAIL = "email"
    PHONE = "phone"
    TEXT = "text"
    WHATSAPP = "whatsapp"

class MaritalStatus(str, Enum):
    """Enum for marital status"""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"

class FamilyRelationship(str, Enum):
    """Enum for family relationships"""
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    OTHER = "other"

class MemberBasicInfo(BaseModel):
    """Schema for member basic information with optional fields for real-world flexibility"""
    title: Optional[str] = None
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    gender: str = Field(..., min_length=1)
    race: str = Field(..., min_length=1)
    date_of_birth: datetime = Field(...)
    marital_status: MaritalStatus
    # Made optional for children/visitors who may not have personal contact info
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10)
    preferred_communication_method: Optional[CommunicationMethod] = None
    best_contact_time: Optional[str] = Field(None, min_length=1)
    receive_devotionals: Optional[bool] = None
    occupation: Optional[str] = Field(None, min_length=1)
    recently_relocated: Optional[bool] = None
    how_heard_about_us: Optional[str] = Field(None, min_length=1)
    considering_joining: Optional[bool] = None
    # Made optional as visitors may not want to share personal requests/feedback
    prayer_request: Optional[str] = Field(None, min_length=1)
    feedback: Optional[str] = Field(None, min_length=1)
    address: Optional[str] = Field(None, min_length=1)

    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format when provided"""
        if v is not None and not v.isdigit():
            raise ValueError('Phone number must contain only digits')
        return v

    @validator('email_address')
    def validate_email(cls, v):
        """Validate email format when provided"""
        if v is not None and ('@' not in v or '.' not in v):
            raise ValueError('Invalid email format')
        return v

    @validator('date_of_birth')
    def validate_dob(cls, v):
        """Validate date of birth is not in the future"""
        if v > datetime.now():
            raise ValueError('Date of birth cannot be in the future')
        return v

class FamilyMemberInfo(BaseModel):
    """Schema for family member information with optional contact fields"""
    title: Optional[str] = None
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    gender: str = Field(..., min_length=1)
    date_of_birth: datetime = Field(...)
    # Made optional for children who may not have personal contact info
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10)
    family_relationship: FamilyRelationship

    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format when provided"""
        if v is not None and not v.isdigit():
            raise ValueError('Phone number must contain only digits')
        return v

    @validator('email_address')
    def validate_email(cls, v):
        """Validate email format when provided"""
        if v is not None and ('@' not in v or '.' not in v):
            raise ValueError('Invalid email format')
        return v

    @validator('date_of_birth')
    def validate_dob(cls, v):
        """Validate date of birth is not in the future"""
        if v > datetime.now():
            raise ValueError('Date of birth cannot be in the future')
        return v

class MemberProfile(BaseModel):
    """Complete member profile schema"""
    id: UUID
    basic_info: MemberBasicInfo
    family_members: List[FamilyMemberInfo] = []
    created_at: datetime
    updated_at: datetime