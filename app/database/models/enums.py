from enum import Enum

class Gender(str, Enum):
    """Gender enumeration."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class MaritalStatus(str, Enum):
    """Marital status enumeration."""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"

class CommunicationMethod(str, Enum):
    """Communication method enumeration."""
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    MAIL = "mail"

class FamilyRelationship(str, Enum):
    """Family relationship enumeration."""
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    SIBLING = "sibling"
    OTHER = "other"

class UserType(str, Enum):
    """User type enumeration."""
    MEMBER = "member"
    VISITOR = "visitor"
    VOLUNTEER = "volunteer"
    STAFF = "staff"

class MemberStatus(str, Enum):
    """Member status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class FollowUpType(str, Enum):
    """Follow up type enumeration."""
    INDIVIDUAL = "individual"
    FAMILY = "family"
