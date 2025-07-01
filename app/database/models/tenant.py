from sqlalchemy import (
    Column, String, Boolean, JSON, Integer, Date, 
    DateTime, UniqueConstraint, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.database.models.base import Base, SchemaConfigMixin
from app.database.models.common import TimestampMixin


class Tenant(Base, TimestampMixin, SchemaConfigMixin):
    """Database model representing a church tenant."""
    
    __tablename__ = 'tenant'
    __table_args__ = (
        UniqueConstraint('domain', name='tenant_domain_unique'),
        {'schema': 'demo'}  # Default schema, can be changed via configure_schema()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_name = Column(String(255), nullable=False)
    tenant_type = Column(String(50))
    domain = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Contact Information
    email = Column(String(255))
    phone = Column(String(255))
    website = Column(String(255))
    social_links = Column(JSONB)
    
    # Location Details
    tenant_address = Column(String(255))
    tenant_city = Column(String(255))
    tenant_state = Column(String(255))
    tenant_country = Column(String(255))
    tenant_country_code = Column(String(10))
    zip = Column(String(10))
    landmark = Column(String(255))
    tenant_timezone = Column(String(255))
    
    # Church Specific Fields
    parish_name = Column(String(255))
    branch = Column(String(255))
    logo_url = Column(String(255))
    tenant_head = Column(UUID(as_uuid=True))
    tenant_status = Column(String(255))
    
    # Configuration
    adult_consent = Column(Integer, nullable=False, server_default=text('16'))
    member_data_retention_period = Column(Integer, nullable=False, server_default=text('30'))
    team_deletion_grace_period = Column(Integer, nullable=False, server_default=text('30'))
    group_deletion_grace_period = Column(Integer, nullable=False, server_default=text('30'))
    
    # Timestamps
    tenant_date_created = Column(Date)

    # #Relationships
    persons = relationship("Person", back_populates="tenant")