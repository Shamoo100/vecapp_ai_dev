from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TenantBase(BaseModel):
    """Base schema for tenant data."""
    name: str = Field(..., description="Name of the tenant")
    active: bool = Field(True, description="Whether the tenant is active")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant settings")

class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    pass

class TenantUpdate(TenantBase):
    """Schema for updating an existing tenant."""
    name: Optional[str] = None
    active: Optional[bool] = None

class TenantInDB(TenantBase):
    """Schema for tenant data from the database."""
    id: str
    api_key: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True