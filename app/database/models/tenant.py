from sqlalchemy import (
    Column, String, Boolean, JSON, Integer, Date, 
    DateTime, UniqueConstraint, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.database.models.base import Base
from app.database.models.common import TimestampMixin


class ChurchBranch(Base, TimestampMixin):
    """Database model representing a church branch tenant."""
    
    __tablename__ = 'church_branch'
    __table_args__ = (
        UniqueConstraint('domain', name='church_branch_domain_unique'),
        {'schema': 'demo'}
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ChurchBranch(id={self.id}, name='{self.tenant_name}', domain='{self.domain}')>"