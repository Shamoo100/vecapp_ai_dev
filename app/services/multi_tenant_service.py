"""Enhanced multi-tenant service with per-tenant versioning support."""

import os
import subprocess
import asyncio
import secrets
import string
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import logging

from app.database.repositories.tenant import TenantRepository
from app.database.models.public.tenant_registry import TenantRegistry
from app.api.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantInDB,
    TenantSchemaProvision, TenantMigrationRequest,
    TenantMigrationStatus, TenantProvisionResponse
)

logger = logging.getLogger(__name__)


class MultiTenantService:
    """Enhanced service for multi-tenant operations with per-tenant versioning."""
    
    def __init__(self):
        self.repository = TenantRepository()
    
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
    
    async def create_tenant(self, db: AsyncSession, tenant_in: TenantCreate) -> TenantInDB:
        """Create a new tenant in the registry."""
        # Use custom schema name if provided, otherwise generate from domain
        schema_name = tenant_in.schema_name if tenant_in.schema_name else self._generate_schema_name(tenant_in.domain)
        api_key = self._generate_api_key()
        
        # Prepare tenant registry data
        tenant_data = {
            "tenant_name": tenant_in.tenant_name,
            "tenant_type": getattr(tenant_in, 'tenant_type', 'church'),
            "domain": tenant_in.domain,
            "is_active": tenant_in.is_active,
            
            # Contact Information
            "email": tenant_in.email,
            "phone": tenant_in.phone,
            "website": getattr(tenant_in, 'website', None),
            
            # Location Details
            "tenant_address": tenant_in.tenant_address,
            "tenant_city": tenant_in.tenant_city,
            "tenant_state": tenant_in.tenant_state,
            "tenant_country": tenant_in.tenant_country,
            "tenant_country_code": getattr(tenant_in, 'tenant_country_code', None),
            "zip": tenant_in.zip,
            "landmark": getattr(tenant_in, 'landmark', None),
            "tenant_timezone": getattr(tenant_in, 'tenant_timezone', None),
            
            # Church Specific Fields
            "parish_name": getattr(tenant_in, 'parish_name', None),
            "branch": getattr(tenant_in, 'branch', None),
            "logo_url": getattr(tenant_in, 'logo_url', None),
            "tenant_head": getattr(tenant_in, 'tenant_head', None),
            "tenant_status": getattr(tenant_in, 'tenant_status', None),
            
            # Schema Management
            "schema_name": schema_name,
            "api_key": api_key,
            "schema_provisioned": False,
            "migrations_applied": False
        }
        
        # Create tenant registry entry
        db_tenant = await self.repository.create(db, tenant_data)
        
        # If auto-provisioning is requested, provision the schema
        if tenant_in.provision_schema:
            try:
                await self._provision_tenant_schema(db, db_tenant, tenant_in.run_migrations)
            except Exception as e:
                logger.error(f"Failed to auto-provision tenant {db_tenant.id}: {str(e)}")
                # Don't fail the tenant creation, just log the error
        
        return TenantInDB.from_orm(db_tenant)
    
    async def get_tenant(self, db: AsyncSession, tenant_id: str) -> Optional[TenantInDB]:
        """Get a tenant by ID."""
        db_tenant = await self.repository.get(db, tenant_id)
        if db_tenant:
            return TenantInDB.from_orm(db_tenant)
        return None
    
    async def get_tenant_by_domain(self, db: AsyncSession, domain: str) -> Optional[TenantInDB]:
        """Get a tenant by domain."""
        result = await db.execute(
            select(TenantRegistry).where(TenantRegistry.domain == domain)
        )
        db_tenant = result.scalar_one_or_none()
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
        """Update an existing tenant."""
        update_data = tenant_in.dict(exclude_unset=True)
        db_tenant = await self.repository.update(db, id=tenant_id, obj_in=update_data)
        if db_tenant:
            return TenantInDB.from_orm(db_tenant)
        return None
    
    async def delete_tenant(self, db: AsyncSession, tenant_id: str) -> bool:
        """Delete a tenant and its schema."""
        tenant = await self.get_tenant(db, tenant_id)
        if not tenant:
            return False
        
        try:
            # Drop the tenant schema if it exists
            if tenant.schema_provisioned:
                await self._drop_tenant_schema(db, tenant.schema_name)
            
            # Delete the tenant registry entry
            await self.repository.delete(db, id=tenant_id)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting tenant {tenant_id}: {str(e)}")
            return False
    
    async def provision_tenant(
        self, db: AsyncSession, tenant_id: str, run_migrations: bool = True
    ) -> TenantProvisionResponse:
        """Provision a complete tenant (schema + migrations)."""
        tenant = await self.get_tenant(db, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        schema_created = False
        migrations_applied = False
        message = "Tenant provisioning started"
        migration_status = None
        
        try:
            # Provision schema
            schema_created = await self._provision_tenant_schema(db, tenant, run_migrations)
            
            if schema_created:
                message = "Schema created successfully"
                
                if run_migrations:
                    # Run migrations
                    migrations_applied = await self._run_tenant_migrations(
                        tenant.schema_name, "head"
                    )
                    
                    if migrations_applied:
                        # Update tenant registry
                        await self.repository.update(
                            db, id=tenant.id, 
                            obj_in={"migrations_applied": True}
                        )
                        message += ", migrations applied"
            
            # Get migration status
            migration_status = await self._get_migration_status(db, tenant.schema_name)
            
        except Exception as e:
            logger.error(f"Error provisioning tenant {tenant.id}: {str(e)}")
            message += f", but encountered error: {str(e)}"
        
        # Refresh tenant data
        updated_tenant = await self.get_tenant(db, tenant.id)
        
        return TenantProvisionResponse(
            tenant=updated_tenant,
            schema_created=schema_created,
            migrations_applied=migrations_applied,
            migration_status=migration_status,
            message=message
        )
    
    async def provision_tenant_schema(
        self, db: AsyncSession, provision_request: TenantSchemaProvision
    ) -> TenantProvisionResponse:
        """Provision schema for an existing tenant."""
        tenant = await self.get_tenant(db, provision_request.tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {provision_request.tenant_id} not found")
        
        schema_created = False
        migrations_applied = False
        message = "Schema provisioning started"
        
        try:
            # Check if schema exists
            schema_exists = await self._schema_exists(db, tenant.schema_name)
            
            if schema_exists and not provision_request.force_recreate:
                message = "Schema already exists"
            else:
                if schema_exists and provision_request.force_recreate:
                    await self._drop_tenant_schema(db, tenant.schema_name)
                    message = "Existing schema dropped, "
                
                schema_created = await self._create_tenant_schema(db, tenant.schema_name)
                if schema_created:
                    await self.repository.update(
                        db, id=tenant.id, obj_in={"schema_provisioned": True}
                    )
                    message += "schema created successfully"
        
        except Exception as e:
            logger.error(f"Error provisioning schema for tenant {tenant.id}: {str(e)}")
            message = f"Schema provisioning failed: {str(e)}"
        
        migration_status = await self._get_migration_status(db, tenant.schema_name)
        updated_tenant = await self.get_tenant(db, tenant.id)
        
        return TenantProvisionResponse(
            tenant=updated_tenant,
            schema_created=schema_created,
            migrations_applied=migrations_applied,
            migration_status=migration_status,
            message=message
        )
    
    async def run_tenant_migrations(
        self, db: AsyncSession, migration_request: TenantMigrationRequest
    ) -> TenantMigrationStatus:
        """Run migrations for a specific tenant."""
        tenant = await self.get_tenant(db, migration_request.tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {migration_request.tenant_id} not found")
        
        # Check if schema is provisioned
        if not tenant.schema_provisioned and not migration_request.force:
            raise ValueError("Schema not provisioned. Use force=True to override.")
        
        try:
            target = migration_request.target_revision or "head"
            success = await self._run_tenant_migrations(tenant.schema_name, target)
            
            if success:
                # Get current revision after migration
                current_revision = await self._get_current_revision(db, tenant.schema_name)
                
                # Update tenant registry
                await self.repository.update(
                    db, id=tenant.id, 
                    obj_in={
                        "migrations_applied": True,
                        "current_migration_revision": current_revision
                    }
                )
        
        except Exception as e:
            logger.error(f"Error running migrations for tenant {tenant.id}: {str(e)}")
            raise
        
        return await self._get_migration_status(db, tenant.schema_name)
    
    async def get_tenant_migration_status(
        self, db: AsyncSession, tenant_id: str
    ) -> TenantMigrationStatus:
        """Get migration status for a tenant."""
        tenant = await self.get_tenant(db, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        return await self._get_migration_status(db, tenant.schema_name)
    
    async def _provision_tenant_schema(
        self, db: AsyncSession, tenant: TenantInDB, run_migrations: bool = True
    ) -> bool:
        """Provision a tenant's schema and optionally run migrations."""
        try:
            # Create schema
            schema_created = await self._create_tenant_schema(db, tenant.schema_name)
            
            if schema_created:
                migrations_success = True
                
                # Run migrations if requested
                if run_migrations:
                    logger.info(f"Running migrations for tenant schema: {tenant.schema_name}")
                    migrations_success = await self._run_tenant_migrations(tenant.schema_name)
                    
                    if not migrations_success:
                        logger.error(f"Migrations failed for tenant {tenant.id}")
                        # Don't fail the entire provisioning, but log the issue
                
                # Update tenant registry
                update_data = {
                    "schema_provisioned": True,
                    "migrations_applied": migrations_success
                }
                
                if migrations_success:
                    # Get the current migration revision
                    try:
                        current_revision = await self._get_current_revision(db, tenant.schema_name)
                        if current_revision:
                            update_data["current_migration_revision"] = current_revision
                    except Exception as e:
                        logger.debug(f"Could not get current revision: {str(e)}")
                
                await self.repository.update(db, id=tenant.id, obj_in=update_data)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error provisioning schema for tenant {tenant.id}: {str(e)}")
            return False
    
    async def _create_tenant_schema(self, db: AsyncSession, schema_name: str) -> bool:
        """Create a new database schema for the tenant."""
        try:
            await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            await db.commit()
            logger.info(f"Created schema: {schema_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {str(e)}")
            await db.rollback()
            return False
    
    async def _drop_tenant_schema(self, db: AsyncSession, schema_name: str) -> bool:
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
    
    async def _schema_exists(self, db: AsyncSession, schema_name: str) -> bool:
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
    
    async def _run_tenant_migrations(
        self, schema_name: str, target_revision: str = "head"
    ) -> bool:
        """Run Alembic migrations for a specific tenant schema."""
        try:
            # Run alembic upgrade command for the specific tenant
            cmd = [
                "alembic", "-x", f"tenant={schema_name}", 
                "upgrade", target_revision
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
    
    async def _get_current_revision(self, db: AsyncSession, schema_name: str) -> Optional[str]:
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
    
    async def _get_migration_status(
        self, db: AsyncSession, schema_name: str
    ) -> TenantMigrationStatus:
        """Get the current migration status for a tenant schema."""
        current_revision = None
        pending_migrations = []
        schema_provisioned = await self._schema_exists(db, schema_name)
        migrations_applied = False
        
        if schema_provisioned:
            try:
                # Check if alembic_version table exists in the schema
                current_revision = await self._get_current_revision(db, schema_name)
                if current_revision:
                    migrations_applied = True
                
                # Get pending migrations using alembic command
                try:
                    cmd = [
                        "alembic", "-x", f"tenant={schema_name}", 
                        "current", "--verbose"
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=os.getcwd()
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        # Parse output to determine pending migrations
                        # This is a simplified approach
                        output = stdout.decode()
                        if "(head)" not in output and current_revision:
                            # There might be pending migrations
                            # In a production system, you'd want more sophisticated parsing
                            pass
                    
                except Exception as e:
                    logger.debug(f"Could not check pending migrations for {schema_name}: {str(e)}")
                
            except Exception as e:
                logger.debug(f"Could not get migration status for {schema_name}: {str(e)}")
        
        return TenantMigrationStatus(
            tenant_id="",  # Will be set by caller
            schema_name=schema_name,
            current_revision=current_revision,
            pending_migrations=pending_migrations,
            schema_provisioned=schema_provisioned,
            migrations_applied=migrations_applied
        )