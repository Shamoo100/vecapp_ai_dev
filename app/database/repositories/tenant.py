#!/usr/bin/env python3
"""
Tenant Repository

Repository class for tenant-related database operations.
Provides CRUD operations and tenant-specific queries.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql import Select

from app.database.repositories.base_repository import BaseRepository
from app.database.models.public.tenant_registry import TenantRegistry


class TenantRepository(BaseRepository[TenantRegistry]):
    """Repository for tenant registry operations in the public schema."""
    
    def __init__(self):
        super().__init__(TenantRegistry)
    
    async def get_by_domain(self, db: AsyncSession, domain: str) -> Optional[TenantRegistry]:
        """Get a tenant by domain name."""
        query = select(self.model).where(self.model.domain == domain)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_api_key(self, db: AsyncSession, api_key: str) -> Optional[TenantRegistry]:
        """Get a tenant by API key."""
        query = select(self.model).where(self.model.api_key == api_key)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_schema_name(self, db: AsyncSession, schema_name: str) -> Optional[TenantRegistry]:
        """Get a tenant by schema name."""
        query = select(self.model).where(self.model.schema_name == schema_name)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_active_tenants(self, db: AsyncSession) -> List[TenantRegistry]:
        """Get all active tenants."""
        query = select(self.model).where(self.model.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_provisioned_tenants(self, db: AsyncSession) -> List[TenantRegistry]:
        """Get all tenants with provisioned schemas."""
        query = select(self.model).where(
            self.model.schema_provisioned == True
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_tenants_needing_migration(self, db: AsyncSession) -> List[TenantRegistry]:
        """Get tenants that have schemas but haven't applied migrations."""
        query = select(self.model).where(
            self.model.schema_provisioned == True,
            self.model.migrations_applied == False
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_schema_status(
        self, 
        db: AsyncSession, 
        tenant_id: int, 
        schema_provisioned: bool = None,
        migrations_applied: bool = None
    ) -> Optional[TenantRegistry]:
        """Update tenant schema status fields."""
        update_data = {}
        if schema_provisioned is not None:
            update_data['schema_provisioned'] = schema_provisioned
        if migrations_applied is not None:
            update_data['migrations_applied'] = migrations_applied
        
        if update_data:
            await db.execute(
                update(self.model)
                .where(self.model.id == tenant_id)
                .values(**update_data)
            )
            return await self.get(db, tenant_id)
        return None
    
    async def search_tenants(
        self, 
        db: AsyncSession, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TenantRegistry]:
        """Search tenants by name, domain, or email."""
        search_pattern = f"%{search_term}%"
        query = select(self.model).where(
            (self.model.tenant_name.ilike(search_pattern)) |
            (self.model.domain.ilike(search_pattern)) |
            (self.model.email.ilike(search_pattern))
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_tenant_stats(self, db: AsyncSession) -> Dict[str, int]:
        """Get tenant statistics."""
        # Total tenants
        total_query = select(self.model)
        total_result = await db.execute(total_query)
        total_count = len(total_result.scalars().all())
        
        # Active tenants
        active_query = select(self.model).where(self.model.is_active == True)
        active_result = await db.execute(active_query)
        active_count = len(active_result.scalars().all())
        
        # Provisioned tenants
        provisioned_query = select(self.model).where(self.model.schema_provisioned == True)
        provisioned_result = await db.execute(provisioned_query)
        provisioned_count = len(provisioned_result.scalars().all())
        
        # Migrated tenants
        migrated_query = select(self.model).where(self.model.migrations_applied == True)
        migrated_result = await db.execute(migrated_query)
        migrated_count = len(migrated_result.scalars().all())
        
        return {
            'total': total_count,
            'active': active_count,
            'provisioned': provisioned_count,
            'migrated': migrated_count,
            'inactive': total_count - active_count,
            'unprovisioned': total_count - provisioned_count,
            'unmigrated': provisioned_count - migrated_count
        }