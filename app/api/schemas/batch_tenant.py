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