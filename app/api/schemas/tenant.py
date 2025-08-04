"""Tenant-related Pydantic schemas for API request/response models."""

"""
Tenant-related Pydantic schemas with clean separation of concerns.
Updated to match actual tenant creation data structure.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum
import re

# === ENUMS ===

class SubscriptionType(str, Enum):
    """Subscription types."""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionPlan(str, Enum):
    """Subscription billing plans."""
    MONTHLY = "monthly"
    ANNUALLY = "annually"

class ChurchSize(str, Enum):
    """Church size categories."""
    SMALL = "0-200"
    MEDIUM = "201-500"
    LARGE = "501-1000"
    XLARGE = "1000+"

class BatchProvisioningStatus(str, Enum):
    """Status enum for batch provisioning operations."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# === BASE SCHEMAS ===

class AccountInformation(BaseModel):
    """Account information for the tenant admin."""
    first_name: str = Field(..., min_length=1, max_length=100, description="Admin first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Admin last name")
    phone: str = Field(..., min_length=10, max_length=20, description="Admin phone number")
    email: str = Field(..., description="Admin email address")
    custom_password: Optional[str] = Field(None, min_length=8, description="Custom password for admin account")

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class ChurchInformation(BaseModel):
    """Church/organization information."""
    name: str = Field(..., min_length=1, max_length=255, description="Church/organization name")
    email: str = Field(..., description="Church contact email")
    domain: str = Field(..., min_length=1, max_length=100, description="Domain identifier (used for schema_name)")
    address: str = Field(..., min_length=1, max_length=500, description="Church address")
    country: str = Field(..., min_length=1, max_length=100, description="Country")
    state: str = Field(..., min_length=1, max_length=100, description="State/Province")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    size: ChurchSize = Field(..., description="Church size category")
    branch: str = Field(..., min_length=1, max_length=255, description="Branch name")
    timezone: str = Field(..., max_length=50, description="Timezone (e.g., America/Regina)")

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format for schema name generation."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Domain must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

class SubscriptionDetails(BaseModel):
    """Subscription information."""
    type: SubscriptionType = Field(..., description="Subscription type")
    plan: SubscriptionPlan = Field(..., description="Billing plan")
    amount: float = Field(..., ge=0, description="Subscription amount")
    date: datetime = Field(..., description="Subscription date")

class TenantProvisioningConfig(BaseModel):
    """Configuration schema for tenant provisioning operations."""
    max_concurrent_operations: int = Field(5, description="Maximum concurrent provisioning operations")
    timeout_seconds: int = Field(300, description="Timeout for individual operations in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts for failed operations")
    
    class Config:
        from_attributes = True

# === TENANT REGISTRY SCHEMAS (Public Schema) ===

class TenantRegistryCreate(BaseModel):
    """Schema for creating a new tenant in the registry."""
    # Account Information
    account_info: AccountInformation = Field(..., description="Admin account information")
    
    # Church Information
    church_info: ChurchInformation = Field(..., description="Church/organization information")
    
    # Subscription Details
    subscription: SubscriptionDetails = Field(..., description="Subscription information")
    
    # System Fields
    schema_name: Optional[str] = Field(None, description="Custom schema name (auto-generated from domain if not provided)")
    provision_schema: bool = Field(True, description="Whether to provision database schema")
    run_migrations: bool = Field(True, description="Whether to run initial migrations")
    is_active: bool = Field(True, description="Whether tenant is active")

    @validator('schema_name', always=True)
    def generate_schema_name(cls, v, values):
        """Generate schema name from domain if not provided."""
        if v is None and 'church_info' in values:
            domain = values['church_info'].domain
            # Clean domain for use as schema name
            schema_name = domain.lower().replace('-', '_').replace(' ', '_')
            return schema_name
        return v

class TenantRegistryUpdate(BaseModel):
    """Schema for updating tenant registry information."""
    # Account Information Updates
    account_info: Optional[AccountInformation] = Field(None, description="Updated admin account information")
    
    # Church Information Updates
    church_info: Optional[ChurchInformation] = Field(None, description="Updated church information")
    
    # Subscription Updates
    subscription: Optional[SubscriptionDetails] = Field(None, description="Updated subscription information")
    
    # System Fields
    is_active: Optional[bool] = Field(None, description="Whether tenant is active")

class TenantRegistryInDB(BaseModel):
    """
    Tenant registry data from public.tenant_registry table.
    Used by AI service for tenant management and linking.
    """
    id: int = Field(..., description="Tenant Registry ID (AI service identifier)")
    tenant_name: str = Field(..., description="Tenant name")
    tenant_type: Optional[str] = Field("church", description="Tenant type")
    domain: str = Field(..., description="Domain identifier")
    is_active: bool = Field(True, description="Whether tenant is active")
    
    # Admin Account Information
    admin_first_name: Optional[str] = Field(None, description="Admin first name")
    admin_last_name: Optional[str] = Field(None, description="Admin last name")
    admin_email: Optional[str] = Field(None, description="Admin email")
    admin_phone: Optional[str] = Field(None, description="Admin phone")
    
    # Contact Information (general tenant contact)
    email: Optional[str] = Field(None, description="General contact email")
    phone: Optional[str] = Field(None, description="General contact phone")
    website: Optional[str] = Field(None, description="Website URL")
    social_links: Optional[dict] = Field(None, description="Social media links")
    
    # Location Details (primary fields from frontend) - MADE OPTIONAL
    street_address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    tenant_country_code: Optional[str] = Field(None, description="Country code")
    zip: Optional[str] = Field(None, description="Postal code")
    landmark: Optional[str] = Field(None, description="Landmark")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    # Legacy location fields (for backward compatibility)
    tenant_address: Optional[str] = Field(None, description="Legacy address field")
    tenant_city: Optional[str] = Field(None, description="Legacy city field")
    tenant_state: Optional[str] = Field(None, description="Legacy state field")
    tenant_country: Optional[str] = Field(None, description="Legacy country field")
    tenant_timezone: Optional[str] = Field(None, description="Legacy timezone field")
    
    # Church Specific Fields - MADE OPTIONAL
    church_size: Optional[str] = Field(None, description="Church size (small, medium, large)")
    parish_name: Optional[str] = Field(None, description="Parish name")
    branch: Optional[str] = Field(None, description="Branch")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    tenant_head: Optional[UUID] = Field(None, description="Tenant head UUID")
    tenant_status: Optional[str] = Field(None, description="Tenant status")
    
    # Configuration
    adult_consent: Optional[int] = Field(16, description="Adult consent age")
    member_data_retention_period: Optional[int] = Field(30, description="Data retention period")
    team_deletion_grace_period: Optional[int] = Field(30, description="Team deletion grace period")
    group_deletion_grace_period: Optional[int] = Field(30, description="Group deletion grace period")
    
    # Subscription Information - MADE OPTIONAL
    subscription_type: Optional[str] = Field(None, description="Subscription type (basic, premium, enterprise)")
    subscription_plan: Optional[str] = Field(None, description="Subscription plan")
    subscription_status: Optional[str] = Field(None, description="Subscription status")
    subscription_amount: Optional[float] = Field(None, description="Subscription amount")  # Fixed: Changed from str to float
    subscription_date: Optional[date] = Field(None, description="Subscription creation date")
    subscription_start_date: Optional[date] = Field(None, description="Subscription start date")
    subscription_end_date: Optional[date] = Field(None, description="Subscription end date")
    
    # Schema Management - REQUIRED
    schema_name: str = Field(..., description="Database schema name")
    schema_provisioned: bool = Field(False, description="Whether schema is provisioned")
    migrations_applied: bool = Field(False, description="Whether migrations are applied")
    api_key: str = Field(..., description="Tenant API key")
    
    # Timestamps
    tenant_date_created: Optional[date] = Field(None, description="Tenant creation date")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True

# === TENANT ISOLATED SCHEMAS (Tenant-Specific Schema) ===

class TenantBase(BaseModel):
    """Base schema for tenant operations."""
    tenant_name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    domain: str = Field(..., min_length=1, max_length=100, description="Domain identifier")
    is_active: bool = Field(True, description="Whether tenant is active")

class TenantIsolatedCreate(BaseModel):
    """Schema for creating a tenant in isolated schema."""
    tenant_registry_id: int = Field(..., description="Links to public.tenant_registry.id")
    tenant_name: str = Field(..., description="Tenant name")
    domain: str = Field(..., description="Tenant domain")
    is_active: bool = Field(True, description="Whether tenant is active")
    
    # Admin Account Information
    admin_first_name: Optional[str] = Field(None, description="Admin first name")
    admin_last_name: Optional[str] = Field(None, description="Admin last name")
    admin_email: Optional[str] = Field(None, description="Admin email")
    admin_phone: Optional[str] = Field(None, description="Admin phone")
    
    # Contact Information
    email: Optional[str] = Field(None, description="General contact email")
    phone: Optional[str] = Field(None, description="General contact phone")
    website: Optional[str] = Field(None, description="Website URL")
    social_links: Optional[dict] = Field(None, description="Social media links")
    
    # Location Information
    street_address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    zip: Optional[str] = Field(None, description="Postal code")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    # Church Information
    church_size: Optional[str] = Field(None, description="Church size")
    parish_name: Optional[str] = Field(None, description="Parish name")
    branch: Optional[str] = Field(None, description="Branch")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    
    # Subscription Information
    subscription_type: Optional[str] = Field(None, description="Subscription type")
    subscription_plan: Optional[str] = Field(None, description="Subscription plan")
    subscription_amount: Optional[float] = Field(None, description="Subscription amount")
    subscription_date: Optional[date] = Field(None, description="Subscription date")

class TenantIsolatedUpdate(BaseModel):
    """Schema for updating tenant in isolated schema."""
    tenant_name: Optional[str] = Field(None, description="Tenant name")
    is_active: Optional[bool] = Field(None, description="Whether tenant is active")
    
    # Admin Account Information
    admin_first_name: Optional[str] = Field(None, description="Admin first name")
    admin_last_name: Optional[str] = Field(None, description="Admin last name")
    admin_email: Optional[str] = Field(None, description="Admin email")
    admin_phone: Optional[str] = Field(None, description="Admin phone")
    
    # Contact Information
    email: Optional[str] = Field(None, description="General contact email")
    phone: Optional[str] = Field(None, description="General contact phone")
    website: Optional[str] = Field(None, description="Website URL")
    social_links: Optional[dict] = Field(None, description="Social media links")
    
    # Location Information
    street_address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    zip: Optional[str] = Field(None, description="Postal code")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    # Church Information
    church_size: Optional[str] = Field(None, description="Church size")
    parish_name: Optional[str] = Field(None, description="Parish name")
    branch: Optional[str] = Field(None, description="Branch")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    
    # Subscription Information
    subscription_type: Optional[str] = Field(None, description="Subscription type")
    subscription_plan: Optional[str] = Field(None, description="Subscription plan")
    subscription_amount: Optional[str] = Field(None, description="Subscription amount")
    subscription_date: Optional[date] = Field(None, description="Subscription date")

class TenantIsolatedInDB(BaseModel):
    """Schema for tenant data in isolated schema."""
    id: int = Field(..., description="Tenant ID in isolated schema")
    tenant_registry_id: int = Field(..., description="Links to public.tenant_registry.id")
    tenant_name: str = Field(..., description="Tenant name")
    domain: str = Field(..., description="Tenant domain")
    is_active: bool = Field(..., description="Whether tenant is active")
    
    # Admin Account Information
    admin_first_name: Optional[str] = Field(None, description="Admin first name")
    admin_last_name: Optional[str] = Field(None, description="Admin last name")
    admin_email: Optional[str] = Field(None, description="Admin email")
    admin_phone: Optional[str] = Field(None, description="Admin phone")
    
    # Contact Information
    email: Optional[str] = Field(None, description="General contact email")
    phone: Optional[str] = Field(None, description="General contact phone")
    website: Optional[str] = Field(None, description="Website URL")
    social_links: Optional[dict] = Field(None, description="Social media links")
    
    # Location Information
    street_address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    zip: Optional[str] = Field(None, description="Postal code")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    # Church Information
    church_size: Optional[str] = Field(None, description="Church size")
    parish_name: Optional[str] = Field(None, description="Parish name")
    branch: Optional[str] = Field(None, description="Branch")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    
    # Subscription Information
    subscription_type: Optional[str] = Field(None, description="Subscription type")
    subscription_plan: Optional[str] = Field(None, description="Subscription plan")
    subscription_amount: Optional[str] = Field(None, description="Subscription amount")
    subscription_date: Optional[date] = Field(None, description="Subscription date")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True

# === PROVISIONING AND MANAGEMENT SCHEMAS ===

class TenantSchemaProvision(BaseModel):
    """Schema for tenant schema provisioning requests."""
    tenant_id: int = Field(..., description="Tenant registry ID")
    schema_name: str = Field(..., description="Schema name to provision")
    run_migrations: bool = Field(True, description="Whether to run migrations after provisioning")
    copy_data: bool = Field(False, description="Whether to copy data from registry to isolated schema")

class TenantMigrationRequest(BaseModel):
    """Schema for tenant migration requests."""
    tenant_id: int = Field(..., description="Tenant registry ID")
    schema_name: str = Field(..., description="Target schema name")
    migration_type: str = Field("up", description="Migration direction (up/down)")
    target_revision: Optional[str] = Field(None, description="Target migration revision")

class TenantMigrationStatus(BaseModel):
    """Schema for tenant migration status."""
    tenant_id: int = Field(..., description="Tenant registry ID")
    schema_name: str = Field(..., description="Schema name")
    migrations_applied: bool = Field(..., description="Whether migrations are applied")
    current_revision: Optional[str] = Field(None, description="Current migration revision")
    last_migration_date: Optional[datetime] = Field(None, description="Last migration timestamp")
    migration_errors: Optional[List[str]] = Field(None, description="Migration error messages")

class TenantProvisionResponse(BaseModel):
    """Response schema for tenant provisioning operations."""
    tenant_id: int = Field(..., description="Tenant registry ID")
    schema_name: str = Field(..., description="Provisioned schema name")
    schema_provisioned: bool = Field(..., description="Whether schema was successfully provisioned")
    migrations_applied: bool = Field(..., description="Whether migrations were applied")
    data_copied: bool = Field(False, description="Whether data was copied to isolated schema")
    auth_synced: bool = Field(False, description="Whether auth data was synced from external service")
    api_key: str = Field(..., description="Generated API key")
    provisioning_time: Optional[float] = Field(None, description="Provisioning time in seconds")
    errors: Optional[List[str]] = Field(None, description="Any errors encountered during provisioning")

class BatchTenantCreate(BaseModel):
    """Schema for batch tenant creation."""
    tenants: List[TenantRegistryCreate] = Field(..., description="List of tenants to create")
    provision_schemas: bool = Field(True, description="Whether to provision schemas for all tenants")
    run_migrations: bool = Field(True, description="Whether to run migrations for all tenants")
    copy_data: bool = Field(False, description="Whether to copy data to isolated schemas")

class TenantProvisioningResult(BaseModel):
    """Result schema for individual tenant provisioning in batch operations."""
    tenant_id: Optional[int] = Field(None, description="Tenant registry ID (if successful)")
    domain: str = Field(..., description="Tenant domain")
    success: bool = Field(..., description="Whether provisioning was successful")
    schema_name: Optional[str] = Field(None, description="Provisioned schema name")
    api_key: Optional[str] = Field(None, description="Generated API key")
    errors: Optional[List[str]] = Field(None, description="Error messages if provisioning failed")

class BatchProvisioningResponse(BaseModel):
    """Response schema for batch tenant provisioning."""
    total_requested: int = Field(..., description="Total number of tenants requested")
    successful: int = Field(..., description="Number of successfully provisioned tenants")
    failed: int = Field(..., description="Number of failed provisioning attempts")
    results: List[TenantProvisioningResult] = Field(..., description="Individual provisioning results")
    total_time: Optional[float] = Field(None, description="Total batch provisioning time in seconds")

# === RESPONSE SCHEMAS ===

class TenantRegistryResponse(BaseModel):
    """Response schema for tenant registry operations."""
    id: int = Field(..., description="Tenant Registry ID")
    tenant_name: str = Field(..., description="Tenant name")
    domain: str = Field(..., description="Domain identifier")
    is_active: bool = Field(..., description="Whether tenant is active")
    schema_name: str = Field(..., description="Database schema name")
    schema_provisioned: bool = Field(..., description="Whether schema is provisioned")
    api_key: str = Field(..., description="Tenant API key")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        from_attributes = True

class TenantRegistryDetailResponse(BaseModel):
    """Detailed response schema for tenant registry operations."""
    id: int = Field(..., description="Tenant Registry ID")
    tenant_name: str = Field(..., description="Tenant name")
    tenant_type: Optional[str] = Field("church", description="Tenant type")
    domain: str = Field(..., description="Domain identifier")
    is_active: bool = Field(..., description="Whether tenant is active")
    
    # Admin Account Information
    admin_first_name: Optional[str] = Field(None, description="Admin first name")
    admin_last_name: Optional[str] = Field(None, description="Admin last name")
    admin_email: Optional[str] = Field(None, description="Admin email")
    admin_phone: Optional[str] = Field(None, description="Admin phone")
    
    # Location Information
    street_address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    # Church Information
    church_size: Optional[str] = Field(None, description="Church size")
    branch: Optional[str] = Field(None, description="Branch")
    
    # Subscription Information
    subscription_type: Optional[str] = Field(None, description="Subscription type")
    subscription_plan: Optional[str] = Field(None, description="Subscription plan")
    subscription_amount: Optional[str] = Field(None, description="Subscription amount")
    
    # Schema Management
    schema_name: str = Field(..., description="Database schema name")
    schema_provisioned: bool = Field(..., description="Whether schema is provisioned")
    migrations_applied: bool = Field(..., description="Whether migrations are applied")
    api_key: str = Field(..., description="Tenant API key")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True

class TenantIsolatedResponse(BaseModel):
    """Response schema for isolated tenant operations."""
    id: int = Field(..., description="Tenant ID in isolated schema")
    tenant_registry_id: int = Field(..., description="Links to public.tenant_registry.id")
    tenant_name: str = Field(..., description="Tenant name")
    domain: str = Field(..., description="Tenant domain")
    is_active: bool = Field(..., description="Whether tenant is active")
    
    # Admin Account Information
    admin_first_name: Optional[str] = Field(None, description="Admin first name")
    admin_last_name: Optional[str] = Field(None, description="Admin last name")
    admin_email: Optional[str] = Field(None, description="Admin email")
    
    # Location Information
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    
    # Church Information
    church_size: Optional[str] = Field(None, description="Church size")
    branch: Optional[str] = Field(None, description="Branch")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True

class TenantListResponse(BaseModel):
    """Response schema for tenant list operations."""
    tenants: List[TenantRegistryResponse] = Field(..., description="List of tenants")
    total: int = Field(..., description="Total number of tenants")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

class TenantStatsResponse(BaseModel):
    """Response schema for tenant statistics."""
    total_tenants: int = Field(..., description="Total number of tenants")
    active_tenants: int = Field(..., description="Number of active tenants")
    provisioned_tenants: int = Field(..., description="Number of tenants with provisioned schemas")
    inactive_tenants: int = Field(..., description="Number of inactive tenants")

class TenantBulkUpdate(BaseModel):
    """Schema for bulk tenant update operations."""
    tenant_ids: List[str] = Field(..., description="List of tenant IDs to update")
    update_data: Dict[str, Any] = Field(..., description="Data to update for all tenants")
    
    class Config:
        from_attributes = True

class BulkUpdateResponse(BaseModel):
    """Response schema for bulk tenant update operations."""
    total_requested: int = Field(..., description="Total number of tenants requested for update")
    successful: int = Field(..., description="Number of successfully updated tenants")
    failed: int = Field(..., description="Number of failed update attempts")
    results: List[Dict[str, Any]] = Field(..., description="Individual update results")
    total_time: Optional[float] = Field(None, description="Total bulk update time in seconds")
    
    class Config:
        from_attributes = True
    
class TenantSearchResponse(BaseModel):
    """Response schema for tenant search operations."""
    tenants: List[TenantRegistryResponse] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of matching tenants")
    search_term: str = Field(..., description="Search term used")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")

class TenantDeletionResponse(BaseModel):
    """Response schema for tenant deletion operations."""
    message: str = Field(..., description="Deletion confirmation message")
    tenant_id: str = Field(..., description="ID of the deleted tenant")
    schema_name: Optional[str] = Field(None, description="Name of the deleted schema")
    schema_dropped: bool = Field(..., description="Whether the tenant schema was dropped")
    deleted_at: datetime = Field(..., description="Timestamp when deletion occurred")
    
    class Config:
        from_attributes = True

class AuthSyncResponse(BaseModel):
    """Response schema for auth data synchronization operations."""
    tenant_id: int = Field(..., description="Tenant registry ID")
    schema_name: str = Field(..., description="Target schema name")
    sync_pattern: str = Field(..., description="Synchronization pattern used")
    success: bool = Field(..., description="Whether sync was successful")
    total_users: int = Field(..., description="Total users found in Auth Service")
    validated_users: int = Field(..., description="Number of users that passed validation")
    synced_users: int = Field(..., description="Number of users successfully synced")
    failed_users: int = Field(..., description="Number of users that failed to sync")
    validation_time: float = Field(..., description="Time spent on validation in seconds")
    sync_time: float = Field(..., description="Time spent on sync operation in seconds")
    total_time: float = Field(..., description="Total operation time in seconds")
    errors: List[str] = Field(..., description="List of error messages")
    message: str = Field(..., description="Summary message")
    
    class Config:
        from_attributes = True