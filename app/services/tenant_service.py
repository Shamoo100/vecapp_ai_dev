from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.tenant import TenantRepository
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantInDB

class TenantService:
    """Service for tenant-related operations."""
    
    def __init__(self):
        self.repository = TenantRepository()
    
    async def create_tenant(self, db: AsyncSession, tenant_in: TenantCreate) -> TenantInDB:
        """Create a new tenant."""
        tenant_data = tenant_in.dict()
        # Generate API key
        tenant_data["api_key"] = self._generate_api_key()
        
        db_tenant = await self.repository.create(db, tenant_data)
        return TenantInDB.from_orm(db_tenant)
    
    async def get_tenant(self, db: AsyncSession, tenant_id: str) -> Optional[TenantInDB]:
        """Get a tenant by ID."""
        db_tenant = await self.repository.get(db, tenant_id)
        if db_tenant:
            return TenantInDB.from_orm(db_tenant)
        return None
    
    async def get_tenants(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[TenantInDB]:
        """Get multiple tenants."""
        db_tenants = await self.repository.get_multi(db, skip=skip, limit=limit)
        return [TenantInDB.from_orm(tenant) for tenant in db_tenants]
    
    async def update_tenant(
        self, db: AsyncSession, tenant_id: str, tenant_in: TenantUpdate
    ) -> Optional[TenantInDB]:
        """Update a tenant."""
        tenant_data = tenant_in.dict(exclude_unset=True)
        db_tenant = await self.repository.update(db, id=tenant_id, obj_in=tenant_data)
        if db_tenant:
            return TenantInDB.from_orm(db_tenant)
        return None
    
    async def delete_tenant(self, db: AsyncSession, tenant_id: str) -> None:
        """Delete a tenant."""
        await self.repository.delete(db, id=tenant_id)
    
    def _generate_api_key(self) -> str:
        """Generate a unique API key."""
        import secrets
        return secrets.token_urlsafe(32)