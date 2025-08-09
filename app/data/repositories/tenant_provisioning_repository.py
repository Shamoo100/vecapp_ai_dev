"""
Tenant Provisioning Repository

Simplified implementation for AI service focusing on:
- Tenant registry management
- Schema provisioning and migrations
- Tenant data copying to isolated schemas
"""

import os
import subprocess
import asyncio
import secrets
import string
from typing import List, Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from datetime import datetime
import logging

from app.database.repositories.base_repository import BaseRepository
from app.database.models.public.tenant_registry import TenantRegistry
from app.api.schemas.tenant import (
    TenantRegistryCreate, TenantRegistryUpdate, TenantRegistryInDB,
    TenantMigrationStatus
)
from app.data.interfaces.tenant_provisioning_interface import ITenantProvisioningRepository

logger = logging.getLogger(__name__)


class TenantProvisioningRepository:
    """Simplified repository implementation for tenant provisioning operations."""
    
    def __init__(self):
        """Initialize the repository with the base tenant repository."""
        self.tenant_repository = BaseRepository(TenantRegistry)
    
    # ==================== BASIC CRUD OPERATIONS ====================
    
    async def create_tenant(self, db: AsyncSession, tenant_data: Dict[str, Any]) -> TenantRegistryInDB:
        """Create a new tenant in the registry."""
        # Generate API key and schema name if not provided
        if not tenant_data.get('api_key'):
            tenant_data["api_key"] = self._generate_api_key()
        
        if not tenant_data.get('schema_name'):
            tenant_data['schema_name'] = self._generate_schema_name(tenant_data['domain'])
        
        db_tenant = await self.tenant_repository.create(db, tenant_data)
        return TenantRegistryInDB.model_validate(db_tenant)
    
    async def get_tenant_by_id(self, db: AsyncSession, tenant_id: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by ID."""
        try:
            # Convert string tenant_id to integer for database query
            tenant_id_int = int(tenant_id)
            db_tenant = await self.tenant_repository.get(db, tenant_id_int)
            if db_tenant:
                return TenantRegistryInDB.model_validate(db_tenant)
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid tenant_id format: {tenant_id}. Must be a valid integer.")
            return None
    
    async def get_tenant_by_domain(self, db: AsyncSession, domain: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by domain."""
        result = await db.execute(
            select(TenantRegistry).where(TenantRegistry.domain == domain)
        )
        db_tenant = result.scalars().first()
        if db_tenant:
            return TenantRegistryInDB.model_validate(db_tenant)
        return None
    
    async def get_tenant_by_api_key(self, db: AsyncSession, api_key: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by API key."""
        result = await db.execute(
            select(TenantRegistry).where(TenantRegistry.api_key == api_key)
        )
        db_tenant = result.scalars().first()
        if db_tenant:
            return TenantRegistryInDB.model_validate(db_tenant)
        return None
    
    async def get_tenants(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[TenantRegistryInDB]:
        """Get multiple tenants with optional filtering."""
        db_tenants = await self.tenant_repository.get_multi(
            db, skip=skip, limit=limit, filters=filters, tenant_id=None
        )
        return [TenantRegistryInDB.model_validate(tenant) for tenant in db_tenants]
    
    async def update_tenant(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[TenantRegistryInDB]:
        """Update a tenant."""
        try:
            # Convert string tenant_id to integer for database query
            tenant_id_int = int(tenant_id)
            db_tenant = await self.tenant_repository.update(db, id=tenant_id_int, obj_in=update_data, tenant_id=None)
            if db_tenant:
                return TenantRegistryInDB.model_validate(db_tenant)
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid tenant_id format: {tenant_id}. Must be a valid integer.")
            return None

    async def delete_tenant(self, db: AsyncSession, tenant_id: str) -> bool:
        """Delete a tenant."""
        tenant = await self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return False
        
        try:
            # Convert string tenant_id to integer for database query
            tenant_id_int = int(tenant_id)
            
            # Drop the tenant schema if it exists
            if tenant.schema_provisioned:
                await self.drop_tenant_schema(db, tenant.schema_name)
            
            # Delete the tenant registry entry
            success = await self.tenant_repository.delete(db, id=tenant_id_int, tenant_id=None)
            return success
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid tenant_id format: {tenant_id}. Must be a valid integer.")
            return False
        except Exception as e:
            logger.error(f"Error deleting tenant {tenant_id}: {str(e)}")
            return False
    
    # ==================== SCHEMA MANAGEMENT ====================
    
    async def create_tenant_schema(self, db: AsyncSession, schema_name: str) -> bool:
        """Create a database schema for the tenant."""
        try:
            await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            await db.commit()
            logger.info(f"Created schema: {schema_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {str(e)}")
            await db.rollback()
            return False
    
    async def drop_tenant_schema(self, db: AsyncSession, schema_name: str) -> bool:
        """Drop a tenant's database schema."""
        try:
            await db.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            await db.commit()
            logger.info(f"Dropped schema: {schema_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to drop schema {schema_name}: {str(e)}")
            await db.rollback()
            return False
    
    async def schema_exists(self, db: AsyncSession, schema_name: str) -> bool:
        """Check if a schema exists."""
        try:
            result = await db.execute(
                text(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name"
                ),
                {"schema_name": schema_name}
            )
            return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking schema existence {schema_name}: {str(e)}")
            return False
    
    async def update_schema_status(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        schema_provisioned: Optional[bool] = None,
        migrations_applied: Optional[bool] = None
    ) -> bool:
        """Update tenant schema status."""
        try:
            # Convert string tenant_id to integer for database query
            tenant_id_int = int(tenant_id)
            
            update_data = {}
            if schema_provisioned is not None:
                update_data['schema_provisioned'] = schema_provisioned
            if migrations_applied is not None:
                update_data['migrations_applied'] = migrations_applied
            
            if update_data:
                await self.tenant_repository.update(db, id=tenant_id_int, obj_in=update_data, tenant_id=None)
                return True
            return False
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid tenant_id format: {tenant_id}. Must be a valid integer.")
            return False
        except Exception as e:
            logger.error(f"Error updating schema status for tenant {tenant_id}: {str(e)}")
            return False
    
    # ==================== MIGRATION MANAGEMENT ====================
    
    async def init_tenant_migrations(self, schema_name: str) -> bool:
        """Initialize migrations for a specific tenant schema."""
        try:
            # Use the proper migration script to initialize tenant migrations
            cmd = [
                "python", "migrate.py", 
                "init-tenant", "--schema", schema_name
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Migrations initialized successfully for schema: {schema_name}")
                logger.debug(f"Migration init output: {stdout.decode()}")
                return True
            else:
                logger.error(
                    f"Migration initialization failed for schema {schema_name}: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error initializing migrations for schema {schema_name}: {str(e)}")
            return False

    async def run_tenant_migrations(
        self, 
        schema_name: str, 
        target_revision: str = "head"
    ) -> bool:
        """Run migrations for a specific tenant schema using the proper migration script."""
        try:
            # Use the proper migration script instead of direct alembic command
            cmd = [
                "python", "migrate.py", 
                "upgrade-tenant", "--schema", schema_name
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Migrations applied successfully for schema: {schema_name}")
                logger.debug(f"Migration output: {stdout.decode()}")
                return True
            else:
                logger.error(
                    f"Migration failed for schema {schema_name}: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error running migrations for schema {schema_name}: {str(e)}")
            return False

    async def get_current_revision(
        self, 
        db: AsyncSession, 
        schema_name: str
    ) -> Optional[str]:
        """Get the current migration revision for a tenant schema."""
        try:
            result = await db.execute(
                text(
                    f"SELECT version_num FROM {schema_name}.alembic_version "
                    "ORDER BY version_num DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.debug(f"Could not get current revision for {schema_name}: {str(e)}")
            return None
    
    async def get_migration_status(
        self, 
        db: AsyncSession, 
        schema_name: str,
        tenant_id: Optional[int] = None
    ) -> TenantMigrationStatus:
        """Get the current migration status for a tenant schema."""
        current_revision = None
        pending_migrations = []
        schema_provisioned = await self.schema_exists(db, schema_name)
        migrations_applied = False
        
        if schema_provisioned:
            try:
                current_revision = await self.get_current_revision(db, schema_name)
                if current_revision:
                    migrations_applied = True
                
            except Exception as e:
                logger.debug(f"Could not get migration status for {schema_name}: {str(e)}")
        
        return TenantMigrationStatus(
            tenant_id=tenant_id or 0,  # Use provided tenant_id or default to 0
            schema_name=schema_name,
            current_revision=current_revision,
            pending_migrations=pending_migrations,
            schema_provisioned=schema_provisioned,
            migrations_applied=migrations_applied
        )
    
    # ==================== TENANT DATA MANAGEMENT ====================
    
    async def insert_tenant_data_copy(
        self, 
        db: AsyncSession, 
        tenant: TenantRegistryInDB
    ) -> bool:
        """
        Copy tenant data from registry to isolated schema.
        
        This creates a copy of the tenant registry data in the tenant's
        isolated schema, linking it via registry_id for data integrity.
        
        Note: This method does NOT commit/rollback - transaction management
        is handled by the calling service layer.
        """
        try:
            # Set schema context to the tenant's isolated schema
            await db.execute(text(f"SET search_path TO {tenant.schema_name}"))
            
            # Prepare tenant data for insertion into isolated schema
            tenant_data = {
                'id': tenant.id,  # Use same ID as registry
                'tenant_name': tenant.tenant_name,
                'tenant_type': tenant.tenant_type,
                'domain': tenant.domain,
                'is_active': tenant.is_active,
                'email': tenant.email,
                'phone': tenant.phone,
                'website': tenant.website,
                'social_links': tenant.social_links,
                'tenant_address': tenant.tenant_address,
                'tenant_city': tenant.tenant_city,
                'tenant_state': tenant.tenant_state,
                'tenant_country': tenant.tenant_country,
                'tenant_country_code': tenant.tenant_country_code,
                'zip': tenant.zip,
                'landmark': tenant.tenant_timezone,
                'tenant_timezone': tenant.tenant_timezone,
                'parish_name': tenant.parish_name,
                'branch': tenant.branch,
                'logo_url': tenant.logo_url,
                'tenant_head': tenant.tenant_head,
                'tenant_status': tenant.tenant_status,
                'adult_consent': tenant.adult_consent,
                'member_data_retention_period': tenant.member_data_retention_period,
                'team_deletion_grace_period': tenant.team_deletion_grace_period,
                'group_deletion_grace_period': tenant.group_deletion_grace_period,
                'registry_id': tenant.id,  # Critical linkage to registry
                'tenant_date_created': tenant.tenant_date_created,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert tenant data into the isolated schema's tenants table
            await db.execute(
                text(f"""
                    INSERT INTO {tenant.schema_name}.tenants (
                        id, tenant_name, tenant_type, domain, is_active,
                        email, phone, website, social_links,
                        tenant_address, tenant_city, tenant_state, tenant_country,
                        tenant_country_code, zip, landmark, tenant_timezone,
                        parish_name, branch, logo_url, tenant_head, tenant_status,
                        adult_consent, member_data_retention_period,
                        team_deletion_grace_period, group_deletion_grace_period,
                        registry_id, tenant_date_created, created_at, updated_at
                    )
                    VALUES (
                        :id, :tenant_name, :tenant_type, :domain, :is_active,
                        :email, :phone, :website, :social_links,
                        :tenant_address, :tenant_city, :tenant_state, :tenant_country,
                        :tenant_country_code, :zip, :landmark, :tenant_timezone,
                        :parish_name, :branch, :logo_url, :tenant_head, :tenant_status,
                        :adult_consent, :member_data_retention_period,
                        :team_deletion_grace_period, :group_deletion_grace_period,
                        :registry_id, :tenant_date_created, :created_at, :updated_at
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        tenant_name = EXCLUDED.tenant_name,
                        domain = EXCLUDED.domain,
                        is_active = EXCLUDED.is_active,
                        updated_at = EXCLUDED.updated_at
                """),
                tenant_data
            )
            
            # Reset schema context back to public
            await db.execute(text("SET search_path TO public"))
            
            logger.info(f"Tenant data copied to isolated schema for tenant {tenant.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy tenant data for tenant {tenant.id}: {str(e)}")
            # Reset schema context on error
            try:
                await db.execute(text("SET search_path TO public"))
            except:
                pass  # Ignore errors when resetting schema context
            raise  # Re-raise the original exception for proper error handling
    
    # ==================== BATCH OPERATIONS ====================
    
    async def validate_tenant_batch_data(self, tenants: List[TenantRegistryCreate]) -> List[str]:
        """Validate tenant data before batch processing."""
        errors = []
        domains = set()
        
        for i, tenant in enumerate(tenants):
            # Check for duplicate domains in the batch
            if tenant.domain in domains:
                errors.append(f"Tenant {i}: Duplicate domain '{tenant.domain}' in batch")
            domains.add(tenant.domain)
            
            # Validate domain format
            if not tenant.domain.replace('-', '').replace('_', '').replace('.', '').isalnum():
                errors.append(f"Tenant {i}: Invalid domain format '{tenant.domain}'")
            
            # Validate required fields
            if not tenant.tenant_name.strip():
                errors.append(f"Tenant {i}: Tenant name cannot be empty")
        
        return errors
    
    async def bulk_update_tenants(
        self, 
        db: AsyncSession, 
        tenant_ids: List[str], 
        update_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform bulk updates on multiple tenants."""
        results = []
        
        for tenant_id in tenant_ids:
            try:
                updated_tenant = await self.update_tenant(db, tenant_id, update_data)
                if updated_tenant:
                    results.append({
                        "tenant_id": tenant_id,
                        "success": True,
                        "updated_fields": list(update_data.keys())
                    })
                else:
                    results.append({
                        "tenant_id": tenant_id,
                        "success": False,
                        "error": "Tenant not found"
                    })
            except Exception as e:
                logger.error(f"Bulk update failed for tenant {tenant_id}: {str(e)}")
                results.append({
                    "tenant_id": tenant_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    # ==================== UTILITY OPERATIONS ====================
    
    async def get_tenant_stats(self, db: AsyncSession) -> Dict[str, int]:
        """Get tenant statistics."""
        try:
            total_result = await db.execute(select(TenantRegistry))
            total_tenants = len(total_result.scalars().all())
            
            active_result = await db.execute(
                select(TenantRegistry).where(TenantRegistry.is_active == True)
            )
            active_tenants = len(active_result.scalars().all())
            
            provisioned_result = await db.execute(
                select(TenantRegistry).where(TenantRegistry.schema_provisioned == True)
            )
            provisioned_tenants = len(provisioned_result.scalars().all())
            
            return {
                "total_tenants": total_tenants,
                "active_tenants": active_tenants,
                "provisioned_tenants": provisioned_tenants,
                "inactive_tenants": total_tenants - active_tenants
            }
        except Exception as e:
            logger.error(f"Error getting tenant stats: {str(e)}")
            return {"total_tenants": 0, "active_tenants": 0, "provisioned_tenants": 0, "inactive_tenants": 0}
    
    async def search_tenants(
        self, 
        db: AsyncSession, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TenantRegistryInDB]:
        """Search tenants by name, domain, or email."""
        try:
            result = await db.execute(
                select(TenantRegistry).where(
                    (TenantRegistry.tenant_name.ilike(f"%{search_term}%")) |
                    (TenantRegistry.domain.ilike(f"%{search_term}%")) |
                    (TenantRegistry.email.ilike(f"%{search_term}%"))
                ).offset(skip).limit(limit)
            )
            db_tenants = result.scalars().all()
            return [TenantRegistryInDB.model_validate(tenant) for tenant in db_tenants]
        except Exception as e:
            logger.error(f"Error searching tenants: {str(e)}")
            return []
    
    async def get_active_tenants(self, db: AsyncSession) -> List[TenantRegistryInDB]:
        """Get all active tenants."""
        try:
            result = await db.execute(
                select(TenantRegistry).where(TenantRegistry.is_active == True)
            )
            db_tenants = result.scalars().all()
            return [TenantRegistryInDB.model_validate(tenant) for tenant in db_tenants]
        except Exception as e:
            logger.error(f"Error getting active tenants: {str(e)}")
            return []
    
    async def get_provisioned_tenants(self, db: AsyncSession) -> List[TenantRegistryInDB]:
        """Get all tenants with provisioned schemas."""
        try:
            result = await db.execute(
                select(TenantRegistry).where(TenantRegistry.schema_provisioned == True)
            )
            db_tenants = result.scalars().all()
            return [TenantRegistryInDB.model_validate(tenant) for tenant in db_tenants]
        except Exception as e:
            logger.error(f"Error getting provisioned tenants: {str(e)}")
            return []
    
    # ==================== UTILITY METHODS ====================
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key for the tenant."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def _generate_schema_name(self, domain: str) -> str:
        """Generate a schema name from the tenant domain."""
        # Clean domain and make it schema-safe
        schema_name = domain.lower().replace('.', '_').replace('-', '_')
        # Ensure it starts with a letter
        if not schema_name[0].isalpha():
            schema_name = f"tenant_{schema_name}"
        return schema_name