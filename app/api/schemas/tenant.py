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
    schema_name: Optional[str] = Field(None, description="Custom schema name (optional, auto-generated if not provided)")
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



from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from .tenant import TenantCreate, TenantInDB


class BatchProvisioningStatus(str, Enum):
    """Status of batch provisioning operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


class TenantProvisioningResult(BaseModel):
    """Result of a single tenant provisioning operation."""
    tenant_name: str = Field(..., description="Name of the tenant")
    domain: str = Field(..., description="Tenant domain")
    success: bool = Field(..., description="Whether provisioning was successful")
    tenant_id: Optional[int] = Field(None, description="Created tenant ID if successful")
    schema_name: Optional[str] = Field(None, description="Created schema name if successful")
    api_key: Optional[str] = Field(None, description="Generated API key if successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    schema_created: bool = Field(False, description="Whether schema was created")
    migrations_applied: bool = Field(False, description="Whether migrations were applied")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to process this tenant")


class BatchTenantCreate(BaseModel):
    """Schema for batch tenant creation request."""
    tenants: List[TenantCreate] = Field(..., min_items=1, max_items=50, description="List of tenants to create")
    provision_schema: bool = Field(True, description="Whether to provision database schemas")
    run_migrations: bool = Field(True, description="Whether to run migrations")
    parallel_processing: bool = Field(True, description="Whether to process tenants in parallel")
    max_concurrent: int = Field(5, ge=1, le=10, description="Maximum concurrent operations")
    continue_on_error: bool = Field(True, description="Whether to continue processing if one tenant fails")


class BatchProvisioningResponse(BaseModel):
    """Response for batch tenant provisioning."""
    batch_id: str = Field(..., description="Unique batch operation ID")
    status: BatchProvisioningStatus = Field(..., description="Overall batch status")
    total_tenants: int = Field(..., description="Total number of tenants to process")
    successful_tenants: int = Field(0, description="Number of successfully processed tenants")
    failed_tenants: int = Field(0, description="Number of failed tenant operations")
    results: List[TenantProvisioningResult] = Field(default_factory=list, description="Individual tenant results")
    started_at: datetime = Field(..., description="When the batch operation started")
    completed_at: Optional[datetime] = Field(None, description="When the batch operation completed")
    total_processing_time_seconds: Optional[float] = Field(None, description="Total time taken for the batch")
    error_summary: Optional[str] = Field(None, description="Summary of errors if any")


class BatchStatusRequest(BaseModel):
    """Request to check batch operation status."""
    batch_id: str = Field(..., description="Batch operation ID to check")


class TenantProvisioningConfig(BaseModel):
    """Configuration for tenant provisioning."""
    max_concurrent_operations: int = Field(5, ge=1, le=20, description="Maximum concurrent provisioning operations")
    operation_timeout_seconds: int = Field(300, ge=30, le=1800, description="Timeout for individual operations")
    retry_attempts: int = Field(3, ge=0, le=5, description="Number of retry attempts for failed operations")
    retry_delay_seconds: int = Field(5, ge=1, le=60, description="Delay between retry attempts")
    enable_rollback: bool = Field(True, description="Whether to rollback on failure")


class TenantBulkUpdate(BaseModel):
    """Schema for bulk tenant updates."""
    tenant_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of tenant IDs to update")
    update_data: Dict[str, Any] = Field(..., description="Data to update for all tenants")
    apply_migrations: bool = Field(False, description="Whether to apply pending migrations")


class BulkUpdateResponse(BaseModel):
    """Response for bulk tenant updates."""
    batch_id: str = Field(..., description="Unique batch operation ID")
    total_tenants: int = Field(..., description="Total number of tenants to update")
    successful_updates: int = Field(0, description="Number of successful updates")
    failed_updates: int = Field(0, description="Number of failed updates")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Individual update results")
    processing_time_seconds: float = Field(..., description="Total processing time")