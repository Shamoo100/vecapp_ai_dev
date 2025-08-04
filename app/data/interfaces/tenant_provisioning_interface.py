"""
Tenant Provisioning Repository Interface

Defines the contract for tenant provisioning operations including
CRUD, schema management, migrations, and batch processing.
"""

from typing import List, Optional, Dict, Any, Protocol
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.tenant import (
    TenantRegistryCreate, TenantRegistryUpdate, TenantRegistryInDB,
    TenantSchemaProvision, TenantMigrationRequest,
    TenantMigrationStatus, TenantProvisionResponse,
    BatchTenantCreate, BatchProvisioningResponse,
    TenantBulkUpdate, BulkUpdateResponse
)


class ITenantProvisioningRepository(Protocol):
    """Interface for tenant provisioning repository operations."""
    
    # ==================== BASIC CRUD OPERATIONS ====================
    
    async def create_tenant(self, db: AsyncSession, tenant_data: Dict[str, Any]) -> TenantRegistryInDB:
        """Create a new tenant in the registry."""
        ...
    
    async def get_tenant_by_id(self, db: AsyncSession, tenant_id: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by ID."""
        ...
    
    async def get_tenant_by_domain(self, db: AsyncSession, domain: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by domain."""
        ...
    
    async def get_tenant_by_api_key(self, db: AsyncSession, api_key: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by API key."""
        ...
    
    async def get_tenants(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[TenantRegistryInDB]:
        """Get multiple tenants with optional filtering."""
        ...
    
    async def update_tenant(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[TenantRegistryInDB]:
        """Update a tenant."""
        ...
    
    async def delete_tenant(self, db: AsyncSession, tenant_id: str) -> bool:
        """Delete a tenant."""
        ...
    
    # ==================== SCHEMA MANAGEMENT ====================
    
    async def create_tenant_schema(self, db: AsyncSession, schema_name: str) -> bool:
        """Create a database schema for the tenant."""
        ...
    
    async def drop_tenant_schema(self, db: AsyncSession, schema_name: str) -> bool:
        """Drop a tenant's database schema."""
        ...
    
    async def schema_exists(self, db: AsyncSession, schema_name: str) -> bool:
        """Check if a schema exists."""
        ...
    
    async def update_schema_status(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        schema_provisioned: Optional[bool] = None,
        migrations_applied: Optional[bool] = None
    ) -> bool:
        """Update tenant schema status."""
        ...
    
    # ==================== MIGRATION MANAGEMENT ====================
    
    async def run_tenant_migrations(
        self, 
        schema_name: str, 
        target_revision: str = "head"
    ) -> bool:
        """Run Alembic migrations for a specific tenant schema."""
        ...
    
    async def get_current_revision(
        self, 
        db: AsyncSession, 
        schema_name: str
    ) -> Optional[str]:
        """Get the current migration revision for a tenant schema."""
        ...
    
    async def get_migration_status(
        self, 
        db: AsyncSession, 
        schema_name: str
    ) -> TenantMigrationStatus:
        """Get the current migration status for a tenant schema."""
        ...
    
    # ==================== BATCH OPERATIONS ====================
    
    async def validate_tenant_batch_data(self, tenants: List[TenantRegistryCreate]) -> List[str]:
        """Validate tenant data before batch processing."""
        ...
    
    async def bulk_update_tenants(
        self, 
        db: AsyncSession, 
        tenant_ids: List[str], 
        update_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform bulk updates on multiple tenants."""
        ...
    
    # ==================== UTILITY OPERATIONS ====================
    
    async def get_tenant_stats(self, db: AsyncSession) -> Dict[str, int]:
        """Get tenant statistics."""
        ...
    
    async def search_tenants(
        self, 
        db: AsyncSession, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TenantRegistryInDB]:
        """Search tenants by name, domain, or email."""
        ...
    
    async def get_active_tenants(self, db: AsyncSession) -> List[TenantRegistryInDB]:
        """Get all active tenants."""
        ...
    
    async def get_provisioned_tenants(self, db: AsyncSession) -> List[TenantRegistryInDB]:
        """Get all tenants with provisioned schemas."""
        ...
    
    # ==================== ADMIN OPERATIONS ====================
    
    async def create_super_admin(
        self, 
        db: AsyncSession, 
        tenant: TenantRegistryInDB, 
        admin_email: str, 
        admin_password: str
    ) -> Dict[str, Any]:
        """Create a super admin user for the tenant."""
        ...
    
    async def seed_initial_data(
        self, 
        db: AsyncSession, 
        tenant: TenantRegistryInDB
    ) -> Dict[str, Any]:
        """Seed initial data for the tenant."""
        ...
    
    async def insert_tenant_data(
        self, 
        db: AsyncSession, 
        tenant: TenantRegistryInDB
    ) -> bool:
        """Insert tenant data into the tenant schema."""
        ...