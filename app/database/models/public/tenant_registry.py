#!/usr/bin/env python3
"""
Tenant Registry Model

This model represents the central tenant registry stored in the public schema.
It keeps track of all tenants in the system and their schema provisioning status.
Each record here corresponds to one tenant with their own isolated schema.
"""

from sqlalchemy import (
    Column, String, Boolean, JSON, Integer, Date, 
    DateTime, UniqueConstraint, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.database.models.base import Base
from app.database.models.common import TimestampMixin


class TenantRegistry(Base, TimestampMixin):
    """
    Central tenant registry stored in public schema.
    
    This table keeps track of all tenants in the system and manages
    their schema provisioning status. Each tenant gets their own
    isolated database schema for their data.
    """
    
    __tablename__ = 'tenant_registry'
    __table_args__ = (
        UniqueConstraint('domain', name='tenant_registry_domain_unique'),
        UniqueConstraint('schema_name', name='tenant_registry_schema_unique'),
        UniqueConstraint('api_key', name='tenant_registry_api_key_unique'),
        # No schema specified - defaults to public schema
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_name = Column(String(255), nullable=False)
    tenant_type = Column(String(50), default='church')
    domain = Column(String(255), nullable=False, unique=True)
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
    
    # Schema Management - Critical for multi-tenant architecture
    schema_name = Column(String(255), nullable=False, unique=True)
    schema_provisioned = Column(Boolean, default=False, nullable=False)
    migrations_applied = Column(Boolean, default=False, nullable=False)
    api_key = Column(String(255), nullable=False, unique=True)
    
    # Timestamps
    tenant_date_created = Column(Date, default=func.current_date())
    
    def __repr__(self):
        return f"<TenantRegistry(id={self.id}, domain='{self.domain}', schema='{self.schema_name}')>"
    
    @property
    def is_fully_provisioned(self) -> bool:
        """Check if tenant is fully provisioned with schema and migrations."""
        return self.schema_provisioned and self.migrations_applied
    
    @property
    def provisioning_status(self) -> str:
        """Get human-readable provisioning status."""
        if not self.schema_provisioned:
            return "Not Provisioned"
        elif not self.migrations_applied:
            return "Schema Created, Migrations Pending"
        else:
            return "Fully Provisioned"