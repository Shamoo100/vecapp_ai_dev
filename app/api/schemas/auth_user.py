"""
Authentication and User schemas for VecApp AI Service.
Clean architecture with proper separation between central system and AI service concerns.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# === USER SCHEMAS ===

class UserResponse(BaseModel):
    """
    User information for AI service operations.
    Represents authenticated users from central system.
    """
    id: UUID = Field(..., description="Person ID from central system")
    username: Optional[str] = Field(..., description="Username")
    email: Optional[str] = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    roles: Optional[List[str]] = Field(default_factory=list, description="User roles")
    is_active: Optional[bool] = Field(True, description="User active status")
    
    # AI service linking fields
    tenant_registry_id: int = Field(..., description="Links to TenantRegistry.id for AI service")
    schema_name: str = Field(..., description="Tenant schema name (primary identifier)")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "john.doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "roles": ["member", "admin"],
                "is_active": True,
                "tenant_registry_id": 1,
                "schema_name": "demo"
            }
        }

# === TENANT SCHEMAS ===

class TenantContextResponse(BaseModel):
    """
    Lightweight tenant context for authentication and request processing.
    Used in auth headers and FastAPI dependencies.
    """
    id: int = Field(..., description="Tenant Registry ID (AI service identifier)")
    name: str = Field(..., description="Tenant display name")
    schema_name: str = Field(..., description="Database schema name (central system identifier)")
    domain: str = Field(..., description="Tenant domain")
    is_active: bool = Field(True, description="Tenant active status")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Demo Church",
                "schema_name": "demo",
                "domain": "demo.vecapp.com",
                "is_active": True
            }
        }

class TenantRegistryResponse(BaseModel):
    """
    Complete tenant registry information for administrative operations.
    Represents full data from public.tenant_registry table.
    """
    id: int = Field(..., description="Tenant Registry ID")
    tenant_name: str = Field(..., description="Official tenant name")
    tenant_type: str = Field(..., description="Type of tenant (e.g., church)")
    domain: str = Field(..., description="Tenant domain")
    schema_name: str = Field(..., description="Database schema name")
    api_key: str = Field(..., description="Tenant API key")
    
    # Provisioning status
    schema_provisioned: bool = Field(..., description="Schema provisioning status")
    migrations_applied: bool = Field(..., description="Migration application status")
    is_active: bool = Field(..., description="Tenant active status")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Optional contact information
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Optional location information
    tenant_address: Optional[str] = Field(None, description="Address")
    tenant_city: Optional[str] = Field(None, description="City")
    tenant_state: Optional[str] = Field(None, description="State")
    tenant_country: Optional[str] = Field(None, description="Country")
    
    class Config:
        from_attributes = True

# === AUTH CONTEXT SCHEMAS ===

class AuthContextResponse(BaseModel):
    """
    Complete authentication context with properly typed user and tenant information.
    """
    authenticated: bool = Field(..., description="Authentication status")
    user: Optional[UserResponse] = Field(None, description="Authenticated user information")
    tenant: Optional[TenantContextResponse] = Field(None, description="Tenant context")
    timestamp: str = Field(..., description="Authentication timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "authenticated": True,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "john.doe",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "roles": ["member"],
                    "is_active": True,
                    "tenant_registry_id": 1,
                    "schema_name": "demo"
                },
                "tenant": {
                    "id": 1,
                    "name": "Demo Church",
                    "schema_name": "demo",
                    "domain": "demo.vecapp.com",
                    "is_active": True
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

# === VALIDATION SCHEMAS ===

class ValidationRequest(BaseModel):
    """Request model for authentication and authorization validation."""
    required_permission: Optional[str] = Field(None, description="Required permission")
    required_role: Optional[str] = Field(None, description="Required role")

class ValidationResponse(BaseModel):
    """Response model for authentication and authorization validation."""
    valid: bool = Field(..., description="Validation result")
    user_id: Optional[UUID] = Field(None, description="User ID if valid")
    tenant_registry_id: Optional[int] = Field(None, description="Tenant Registry ID if valid")
    schema_name: Optional[str] = Field(None, description="Schema name if valid")
    has_permission: bool = Field(False, description="Permission check result")
    has_role: bool = Field(False, description="Role check result")
    message: str = Field(..., description="Validation message")