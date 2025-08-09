from sqlalchemy import (
    Column, String, Boolean, JSON, Integer, Date, 
    DateTime, UniqueConstraint, text, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from uuid import uuid4

from ..base import Base
from ..common import TimestampMixin, SchemaConfigMixin


class Tenant(Base, TimestampMixin, SchemaConfigMixin):
    """
    Tenant-specific model stored in each tenant's isolated schema.
    
    This model represents the tenant's own information within their
    isolated schema. Each tenant has their own copy of this table
    in their dedicated schema (e.g., demo.tenant_info, church1.tenant_info).
    """
    
    __tablename__ = 'tenants'
    __table_args__ = (
        UniqueConstraint('domain', name='tenant_domain_unique'),
        # Schema will be set dynamically based on tenant context
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_name = Column(String(255), nullable=False)
    tenant_type = Column(String(50))
    domain = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Admin Account Information (from frontend account_info)
    admin_first_name = Column(String(255), nullable=True)
    admin_last_name = Column(String(255), nullable=True)
    admin_email = Column(String(255), nullable=True)
    admin_phone = Column(String(20), nullable=True)
    
    # Contact Information (general tenant contact)
    email = Column(String(255))
    phone = Column(String(255))
    website = Column(String(255))
    social_links = Column(JSONB)
    
    # Location Details (from frontend church_info)
    street_address = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    tenant_country_code = Column(String(10))
    zip = Column(String(10))
    landmark = Column(String(255))
    timezone = Column(String(255), nullable=True)
    
    # Legacy location fields (for backward compatibility)
    tenant_address = Column(String(255))
    tenant_city = Column(String(255))
    tenant_state = Column(String(255))
    tenant_country = Column(String(255))
    tenant_timezone = Column(String(255))
    
    # Church Specific Fields (from frontend church_info)
    church_size = Column(String(50), nullable=True)  # small, medium, large, etc.
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
    
    # Subscription Information (from frontend subscription)
    subscription_type = Column(String(50), nullable=True)  # basic, premium, enterprise
    subscription_plan = Column(String(255), nullable=True)
    subscription_status = Column(String(255), nullable=True)
    subscription_amount = Column(Numeric(10, 2), nullable=True)  # String to handle currency formats
    subscription_date = Column(Date, nullable=True)  # When subscription was created
    subscription_start_date = Column(Date, nullable=True)
    subscription_end_date = Column(Date, nullable=True)
    
    # Registry Reference - links back to the central tenant registry
    registry_id = Column(Integer, nullable=False, comment="References tenant_registry.id in public schema")
    
    # Timestamps
    tenant_date_created = Column(Date)

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.tenant_name}', domain='{self.domain}')>"
    
    @property
    def admin_full_name(self) -> str:
        """Get the full name of the admin user."""
        if self.admin_first_name and self.admin_last_name:
            return f"{self.admin_first_name} {self.admin_last_name}"
        return self.admin_first_name or self.admin_last_name or "Unknown"
    
    @property
    def full_address(self) -> str:
        """Get the complete formatted address."""
        address_parts = [
            self.street_address,
            self.city,
            self.state,
            self.country
        ]
        return ", ".join(part for part in address_parts if part)