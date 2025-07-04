from typing import List, Optional, Dict, Any
import os
import subprocess
import asyncio
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.database.repositories.tenant import TenantRepository
from app.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantInDB, 
    TenantSchemaProvision, TenantMigrationRequest, 
    TenantMigrationStatus, TenantProvisionResponse
)

logger = logging.getLogger(__name__)

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
    
    async def create_tenant_with_schema(
        self, db: AsyncSession, tenant_in: TenantCreate
    ) -> TenantProvisionResponse:
        """Create a new tenant with optional schema provisioning and migrations."""
        # Create tenant record first
        tenant_data = tenant_in.dict(exclude={'provision_schema', 'run_migrations'})
        tenant_data["api_key"] = self._generate_api_key()
        tenant_data["schema_name"] = tenant_in.domain  # Use domain as schema name
        
        db_tenant = await self.repository.create(db, tenant_data)
        tenant = TenantInDB.from_orm(db_tenant)
        
        schema_created = False
        migrations_applied = False
        migration_status = None
        message = "Tenant created successfully"
        
        try:
            # Provision schema if requested
            if tenant_in.provision_schema:
                schema_created = await self._create_tenant_schema(db, tenant.schema_name)
                if schema_created:
                    # Update tenant record
                    await self.repository.update(
                        db, id=tenant.id, obj_in={"schema_provisioned": True}
                    )
                    message += ", schema provisioned"
                    
                    # Run migrations if requested
                    if tenant_in.run_migrations:
                        migrations_applied = await self._run_tenant_migrations(
                            tenant.schema_name
                        )
                        if migrations_applied:
                            await self.repository.update(
                                db, id=tenant.id, obj_in={"migrations_applied": True}
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
                await self.repository.update(
                    db, id=tenant.id, obj_in={"migrations_applied": True}
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
                return True
            else:
                logger.error(
                    f"Migration failed for schema {schema_name}: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error running migrations for schema {schema_name}: {str(e)}")
            return False
    
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
                result = await db.execute(
                    text(
                        "SELECT version_num FROM {}.alembic_version ORDER BY version_num DESC LIMIT 1".format(schema_name)
                    )
                )
                row = result.fetchone()
                if row:
                    current_revision = row[0]
                    migrations_applied = True
                
                # Get pending migrations by running alembic current command
                # This is a simplified approach - in production you might want
                # to implement a more sophisticated migration tracking system
                
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