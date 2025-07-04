"""Tenant-related Pydantic schemas for API request/response models."""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator


class TenantBase(BaseModel):
    """Base tenant schema with common fields."""
    tenant_name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    tenant_type: Optional[str] = Field("church", max_length=50, description="Tenant type")
    domain: str = Field(..., min_length=1, max_length=255, description="Tenant domain")
    is_active: bool = Field(True, description="Whether tenant is active")
    
    # Contact Information
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    phone: Optional[str] = Field(None, max_length=255, description="Contact phone")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    
    # Location Details
    tenant_address: Optional[str] = Field(None, max_length=255, description="Address")
    tenant_city: Optional[str] = Field(None, max_length=255, description="City")
    tenant_state: Optional[str] = Field(None, max_length=255, description="State")
    tenant_country: Optional[str] = Field(None, max_length=255, description="Country")
    tenant_country_code: Optional[str] = Field(None, max_length=10, description="Country code")
    zip: Optional[str] = Field(None, max_length=10, description="Postal code")
    landmark: Optional[str] = Field(None, max_length=255, description="Landmark")
    tenant_timezone: Optional[str] = Field(None, max_length=255, description="Timezone")
    
    # Church Specific Fields
    parish_name: Optional[str] = Field(None, max_length=255, description="Parish name")
    branch: Optional[str] = Field(None, max_length=255, description="Branch")
    logo_url: Optional[str] = Field(None, max_length=255, description="Logo URL")
    tenant_head: Optional[UUID] = Field(None, description="Tenant head UUID")
    tenant_status: Optional[str] = Field(None, max_length=255, description="Tenant status")

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format."""
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError('Domain must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v.lower()


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    provision_schema: bool = Field(True, description="Whether to provision database schema")
    run_migrations: bool = Field(True, description="Whether to run initial migrations")


class TenantUpdate(BaseModel):
    """Schema for updating an existing tenant."""
    tenant_name: Optional[str] = Field(None, min_length=1, max_length=255)
    tenant_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    
    # Contact Information
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    
    # Location Details
    tenant_address: Optional[str] = Field(None, max_length=255)
    tenant_city: Optional[str] = Field(None, max_length=255)
    tenant_state: Optional[str] = Field(None, max_length=255)
    tenant_country: Optional[str] = Field(None, max_length=255)
    tenant_country_code: Optional[str] = Field(None, max_length=10)
    zip: Optional[str] = Field(None, max_length=10)
    landmark: Optional[str] = Field(None, max_length=255)
    tenant_timezone: Optional[str] = Field(None, max_length=255)
    
    # Church Specific Fields
    parish_name: Optional[str] = Field(None, max_length=255)
    branch: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=255)
    tenant_head: Optional[UUID] = Field(None)
    tenant_status: Optional[str] = Field(None, max_length=255)


class TenantInDB(TenantBase):
    """Schema for tenant data from database."""
    id: int = Field(..., description="Tenant ID")
    api_key: str = Field(..., description="Tenant API key")
    schema_name: str = Field(..., description="Database schema name")
    schema_provisioned: bool = Field(False, description="Whether schema is provisioned")
    migrations_applied: bool = Field(False, description="Whether migrations are applied")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class TenantSchemaProvision(BaseModel):
    """Schema for tenant schema provisioning request."""
    tenant_id: str = Field(..., description="Tenant ID")
    force_recreate: bool = Field(False, description="Force recreate schema if exists")


class TenantMigrationRequest(BaseModel):
    """Schema for tenant migration request."""
    tenant_id: str = Field(..., description="Tenant ID")
    target_revision: Optional[str] = Field(None, description="Target migration revision (default: head)")
    force: bool = Field(False, description="Force migration even if schema not provisioned")


class TenantMigrationStatus(BaseModel):
    """Schema for tenant migration status response."""
    tenant_id: str = Field(..., description="Tenant ID")
    schema_name: str = Field(..., description="Database schema name")
    current_revision: Optional[str] = Field(None, description="Current migration revision")
    pending_migrations: List[str] = Field(default_factory=list, description="Pending migration revisions")
    schema_provisioned: bool = Field(..., description="Whether schema is provisioned")
    migrations_applied: bool = Field(..., description="Whether any migrations are applied")


class TenantProvisionResponse(BaseModel):
    """Schema for tenant provisioning response."""
    tenant: TenantInDB = Field(..., description="Tenant information")
    schema_created: bool = Field(..., description="Whether schema was created")
    migrations_applied: bool = Field(..., description="Whether migrations were applied")
    migration_status: TenantMigrationStatus = Field(..., description="Migration status")
    message: str = Field(..., description="Status message")