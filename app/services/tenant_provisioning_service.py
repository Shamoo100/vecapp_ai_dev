"""
Tenant Provisioning Service

Simplified implementation for AI service that focuses on:
1. Creating tenant registry entry
2. Generating schema name
3. Creating database schema
4. Running all migrations
5. Inserting tenant data copy into isolated schema
6. Syncing auth data from external service
"""

import asyncio
import uuid
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.tenant_provisioning_repository import TenantProvisioningRepository
from app.services.external_auth_sync_service import ExternalAuthSyncService
from app.api.schemas.tenant import (
    TenantRegistryCreate, TenantRegistryUpdate, TenantRegistryInDB,
    TenantSchemaProvision, TenantMigrationRequest, TenantMigrationStatus,
    TenantProvisionResponse, BatchTenantCreate, BatchProvisioningResponse,
    TenantProvisioningResult, BatchProvisioningStatus, TenantProvisioningConfig,
    TenantBulkUpdate, BulkUpdateResponse, AccountInformation, ChurchInformation,
    SubscriptionDetails
)

logger = logging.getLogger(__name__)


class TenantProvisioningService:
    """
    Simplified tenant provisioning service for AI service.
    
    Handles:
    - Tenant registry creation
    - Schema provisioning and migrations
    - Tenant data copying to isolated schema
    - Auth data synchronization from external service
    - No admin user creation (header-based auth)
    - No person/family data management (handled by Member Service)
    """
    
    def __init__(self):
        """Initialize the service with repository."""
        self.repository = TenantProvisioningRepository()
        self.active_batches: Dict[str, BatchProvisioningResponse] = {}
        self.config = TenantProvisioningConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_operations)
    
    # ==================== SINGLE TENANT OPERATIONS ====================
    
    async def create_tenant(self, db: AsyncSession, tenant_in: TenantRegistryCreate) -> TenantRegistryInDB:
        """Create a new tenant registry entry."""
        # Convert nested Pydantic model to flat dict for TenantRegistry model
        tenant_data = self._flatten_tenant_data(tenant_in)
        
        # Generate schema_name from domain if not provided
        if not tenant_data.get('schema_name'):
            tenant_data['schema_name'] = self._generate_schema_name(tenant_data['domain'])
        
        # Remove API-only fields that shouldn't be stored
        tenant_data.pop('provision_schema', None)
        tenant_data.pop('run_migrations', None)
        
        return await self.repository.create_tenant(db, tenant_data)
    
    def _flatten_tenant_data(self, tenant_in: TenantRegistryCreate) -> dict:
        """
        Flatten the nested TenantRegistryCreate structure to match TenantRegistry model fields.
        Maps frontend registration data (account_info, church_info, subscription) to database fields.
        """
        # Start with the base model dump
        data = tenant_in.model_dump()
        
        # Extract nested information
        account_info = data.pop('account_info', {})
        church_info = data.pop('church_info', {})
        subscription = data.pop('subscription', {})
        
        # Map all fields to TenantRegistry model structure
        flattened_data = {
            # Core tenant information (from church_info)
            'tenant_name': church_info.get('name'),
            'domain': church_info.get('domain'),
            'tenant_type': 'church',  # Default type
            'is_active': data.get('is_active', True),
            
            # Admin Account Information (from account_info)
            'admin_first_name': account_info.get('first_name'),
            'admin_last_name': account_info.get('last_name'),
            'admin_email': account_info.get('email'),
            'admin_phone': account_info.get('phone'),
            
            # General Contact Information (from church_info)
            'email': church_info.get('email'),  # Church general email
            'phone': church_info.get('phone'),  # Church general phone
            'website': church_info.get('website'),
            'social_links': church_info.get('social_links'),
            
            # Location Details (primary fields from church_info)
            'street_address': church_info.get('address'),
            'city': church_info.get('city'),
            'state': church_info.get('state'),
            'country': church_info.get('country'),
            'zip': church_info.get('zip'),
            'timezone': church_info.get('timezone'),
            
            # Legacy location fields (for backward compatibility)
            'tenant_address': church_info.get('address'),
            'tenant_city': church_info.get('city'),
            'tenant_state': church_info.get('state'),
            'tenant_country': church_info.get('country'),
            'tenant_timezone': church_info.get('timezone'),
            
            # Church Specific Fields (from church_info)
            'church_size': church_info.get('size'),  # Maps to church_size field
            'parish_name': church_info.get('name'),  # Use church name as parish name
            'branch': church_info.get('branch'),
            'logo_url': church_info.get('logo_url'),
            
            # Subscription Information (from subscription)
            'subscription_type': subscription.get('type'),  # basic, premium, enterprise
            'subscription_plan': subscription.get('plan'),
            'subscription_amount': subscription.get('amount'),
            'subscription_date': subscription.get('date'),  # When subscription was created
            'subscription_start_date': subscription.get('start_date'),
            'subscription_end_date': subscription.get('end_date'),
            'subscription_status': subscription.get('status', 'active'),
            
            # API control fields (from base data)
            'provision_schema': data.get('provision_schema', False),
            'run_migrations': data.get('run_migrations', False),
        }
        
        # Add any remaining fields from the base data that weren't explicitly mapped
        for key, value in data.items():
            if key not in flattened_data and key not in ['account_info', 'church_info', 'subscription']:
                flattened_data[key] = value
        
        # Remove None values to avoid overwriting defaults
        flattened_data = {k: v for k, v in flattened_data.items() if v is not None}
        
        return flattened_data

    async def get_tenant(self, db: AsyncSession, tenant_id: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by ID."""
        return await self.repository.get_tenant_by_id(db, tenant_id)
    
    async def get_tenant_by_domain(self, db: AsyncSession, domain: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by domain."""
        return await self.repository.get_tenant_by_domain(db, domain)
    
    async def get_tenant_by_api_key(self, db: AsyncSession, api_key: str) -> Optional[TenantRegistryInDB]:
        """Get a tenant by API key."""
        return await self.repository.get_tenant_by_api_key(db, api_key)
    
    async def get_tenants(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[TenantRegistryInDB]:
        """Get multiple tenants."""
        return await self.repository.get_tenants(db, skip=skip, limit=limit)
    
    async def update_tenant(
        self, db: AsyncSession, tenant_id: str, tenant_in: TenantRegistryUpdate
    ) -> Optional[TenantRegistryInDB]:
        """Update a tenant."""
        tenant_data = tenant_in.model_dump(exclude_unset=True)
        return await self.repository.update_tenant(db, tenant_id, tenant_data)
    
    async def delete_tenant(self, db: AsyncSession, tenant_id: str) -> bool:
        """Delete a tenant and its schema."""
        return await self.repository.delete_tenant(db, tenant_id)
    
    # ==================== SIMPLIFIED TENANT PROVISIONING ====================
    
    async def provision_tenant(
        self, db: AsyncSession, tenant_data: TenantRegistryCreate
    ) -> TenantProvisionResponse:
        """
        Complete tenant provisioning flow:
        1. Create tenant registry entry
        2. Generate schema name
        3. Create database schema
        4. Run all migrations
        5. Insert tenant data copy into isolated schema
        6. Sync auth data from external service
        """
        start_time = time.time()
        schema_created = False
        migrations_applied = False
        tenant_data_copied = False
        auth_synced = False
        message = "Tenant created successfully"
        tenant = None
        errors = []
        
        try:
            # Step 1: Create the tenant registry entry
            tenant = await self.create_tenant(db, tenant_data)
            logger.info(f"Created tenant registry entry: {tenant.tenant_name} ({tenant.id})")
            
            # Step 2 & 3: Create schema if requested
            if tenant_data.provision_schema:
                schema_created = await self._provision_schema(db, tenant)
                if schema_created:
                    message = "Tenant and schema created successfully"
                    logger.info(f"Created schema: {tenant.schema_name}")
                else:
                    message = "Tenant created, but schema creation failed"
                    errors.append(f"Schema creation failed for: {tenant.schema_name}")
                    logger.error(f"Schema creation failed for: {tenant.schema_name}")
            
            # Step 4: Run migrations if requested and schema was created
            if tenant_data.run_migrations and schema_created:
                migrations_applied = await self._apply_migrations(db, tenant)
                if migrations_applied:
                    message = "Tenant schema and migrations completed"
                    logger.info(f"Migrations applied for: {tenant.schema_name}")
                else:
                    message = "Tenant and schema created, but migrations failed"
                    errors.append(f"Migrations failed for: {tenant.schema_name}")
                    logger.error(f"Migrations failed for: {tenant.schema_name}")
            
            # Step 5: Copy tenant data to isolated schema
            if migrations_applied:
                tenant_data_copied = await self._copy_tenant_data(db, tenant)
                if tenant_data_copied:
                    message = "Tenant data copied to isolated schema"
                    logger.info(f"Tenant data copied to isolated schema: {tenant.schema_name}")
                else:
                    message = "Tenant provisioned but data copy failed"
                    errors.append(f"Tenant data copy failed for: {tenant.schema_name}")
                    logger.error(f"Tenant data copy failed for: {tenant.schema_name}")
            
            # Step 6: Sync auth data from external service
            if tenant_data_copied:
                auth_synced = await self._sync_auth_data(db, tenant)
                if auth_synced:
                    message = "Tenant fully provisioned with auth sync completed"
                    logger.info(f"Auth data synced for tenant: {tenant.schema_name}")
                else:
                    message = "Tenant provisioned but auth sync failed"
                    errors.append(f"Auth sync failed for: {tenant.schema_name}")
                    logger.error(f"Auth sync failed for: {tenant.schema_name}")
            
            # Commit the transaction
            await db.commit()
            
            # Calculate provisioning time
            provisioning_time = time.time() - start_time
            
            # Return response matching TenantProvisionResponse schema
            return TenantProvisionResponse(
                tenant_id=tenant.id,
                schema_name=tenant.schema_name,
                schema_provisioned=schema_created,
                migrations_applied=migrations_applied,
                data_copied=tenant_data_copied,
                auth_synced=auth_synced,
                api_key=tenant.api_key,
                provisioning_time=provisioning_time,
                errors=errors if errors else None
            )
            
        except Exception as e:
            logger.error(f"Error provisioning tenant: {str(e)}")
            # Check if session has rollback method before calling it
            if hasattr(db, 'rollback'):
                await db.rollback()
            raise ValueError(f"Failed to provision tenant: {str(e)}")
    
    # ==================== BATCH OPERATIONS ====================
    
    async def process_batch_tenants(
        self, db: AsyncSession, batch_data: BatchTenantCreate
    ) -> BatchProvisioningResponse:
        """Process multiple tenants in batch."""
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize batch response
        batch_response = BatchProvisioningResponse(
            batch_id=batch_id,
            total_tenants=len(batch_data.tenants),
            status=BatchProvisioningStatus.PROCESSING,
            results=[],
            started_at=datetime.utcnow(),
            estimated_completion=None
        )
        
        self.active_batches[batch_id] = batch_response
        
        try:
            # Validate batch data
            validation_errors = await self.repository.validate_tenant_batch_data(batch_data.tenants)
            if validation_errors:
                batch_response.status = BatchProvisioningStatus.FAILED
                batch_response.errors = validation_errors
                return batch_response
            
            # Process tenants concurrently
            tasks = []
            for tenant_data in batch_data.tenants:
                task = self._process_single_tenant(db, tenant_data, batch_data.config)
                tasks.append(task)
            
            # Execute with concurrency limit
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    batch_response.results.append(
                        TenantProvisioningResult(
                            tenant_data=batch_data.tenants[i],
                            success=False,
                            error=str(result)
                        )
                    )
                else:
                    batch_response.results.append(result)
            
            # Update batch status
            successful_count = sum(1 for r in batch_response.results if r.success)
            batch_response.successful_count = successful_count
            batch_response.failed_count = len(batch_response.results) - successful_count
            batch_response.status = BatchProvisioningStatus.COMPLETED
            batch_response.completed_at = datetime.utcnow()
            batch_response.processing_time = time.time() - start_time
            
            return batch_response
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            batch_response.status = BatchProvisioningStatus.FAILED
            batch_response.errors = [str(e)]
            return batch_response
    
    async def _process_single_tenant(
        self, db: AsyncSession, tenant_data: TenantRegistryCreate, config: TenantProvisioningConfig
    ) -> TenantProvisioningResult:
        """Process a single tenant within a batch."""
        async with self._semaphore:
            try:
                provision_result = await self.provision_tenant(db, tenant_data)
                
                return TenantProvisioningResult(
                    tenant_data=tenant_data,
                    tenant=provision_result.tenant,
                    success=True,
                    schema_created=provision_result.schema_created,
                    migrations_applied=provision_result.migrations_applied,
                    message=provision_result.message
                )
                
            except Exception as e:
                logger.error(f"Failed to process tenant {tenant_data.tenant_name}: {str(e)}")
                return TenantProvisioningResult(
                    tenant_data=tenant_data,
                    success=False,
                    error=str(e)
                )
    
    # ==================== UTILITY OPERATIONS ====================
    
    async def search_tenants(
        self, db: AsyncSession, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[TenantRegistryInDB]:
        """Search tenants by name, domain, or email."""
        return await self.repository.search_tenants(db, search_term, skip, limit)
    
    async def get_active_tenants(self, db: AsyncSession) -> List[TenantRegistryInDB]:
        """Get all active tenants."""
        return await self.repository.get_active_tenants(db)
    
    async def get_provisioned_tenants(self, db: AsyncSession) -> List[TenantRegistryInDB]:
        """Get all tenants with provisioned schemas."""
        return await self.repository.get_provisioned_tenants(db)
    
    async def get_tenant_stats(self, db: AsyncSession) -> Dict[str, int]:
        """Get tenant statistics."""
        return await self.repository.get_tenant_stats(db)
    
    async def get_batch_status(self, batch_id: str) -> Optional[BatchProvisioningResponse]:
        """Get the status of a batch operation."""
        return self.active_batches.get(batch_id)
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    async def _provision_schema(self, db: AsyncSession, tenant: TenantRegistryInDB) -> bool:
        """Provision database schema for tenant."""
        try:
            schema_created = await self.repository.create_tenant_schema(db, tenant.schema_name)
            if schema_created:
                await self.repository.update_schema_status(
                    db, tenant.id, schema_provisioned=True
                )
            return schema_created
        except Exception as e:
            logger.error(f"Schema provisioning failed for tenant {tenant.id}: {str(e)}")
            return False
    
    async def _apply_migrations(self, db: AsyncSession, tenant: TenantRegistryInDB) -> bool:
        """Apply database migrations for tenant."""
        try:
            # First initialize the tenant migrations
            init_success = await self.repository.init_tenant_migrations(tenant.schema_name)
            if not init_success:
                logger.error(f"Failed to initialize migrations for tenant {tenant.id}")
                return False
            
            # Then run the migrations
            migrations_applied = await self.repository.run_tenant_migrations(tenant.schema_name)
            if migrations_applied:
                await self.repository.update_schema_status(
                    db, tenant.id, migrations_applied=True
                )
            return migrations_applied
        except Exception as e:
            logger.error(f"Migration failed for tenant {tenant.id}: {str(e)}")
            return False
    
    async def _copy_tenant_data(self, db: AsyncSession, tenant: TenantRegistryInDB) -> bool:
        """Copy tenant data from registry to isolated schema."""
        try:
            return await self.repository.insert_tenant_data_copy(db, tenant)
        except Exception as e:
            logger.error(f"Tenant data copy failed for tenant {tenant.id}: {str(e)}")
            return False
    
    async def _sync_auth_data(self, tenant_id: int, schema_name: str) -> Dict[str, Any]:
        """
        Sync authentication data from external Auth Service to tenant schema using atomic batch pattern.
        
        Args:
            tenant_id: Tenant registry ID
            schema_name: Target schema name for sync
            
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info(f"Starting atomic batch auth sync for tenant {tenant_id} in schema {schema_name}")
            
            # Initialize sync service for this tenant's schema
            sync_service = ExternalAuthSyncService(schema_name)
            await sync_service.initialize()
            
            try:
                # Validate connection to Auth Service
                if not await sync_service.validate_auth_service_connection():
                    logger.error(f"Cannot connect to Auth Service for tenant {tenant_id}")
                    return {
                        'success': False,
                        'message': 'Failed to connect to Auth Service',
                        'users_synced': 0,
                        'errors': ['Auth Service connection failed']
                    }
                
                # Use atomic batch sync pattern
                sync_result = await sync_service.sync_auth_data_atomic_batch()
                
                if sync_result.get('success'):
                    logger.info(f"Auth sync completed for tenant {tenant_id}: {sync_result.get('synced_users', 0)} users synced")
                else:
                    logger.error(f"Auth sync failed for tenant {tenant_id}: {sync_result.get('errors', [])}")
                
                return sync_result
                
            finally:
                await sync_service.close()
                
        except Exception as e:
            error_msg = f"Auth sync failed for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'users_synced': 0,
                'errors': [error_msg]
            }
    
    def _generate_schema_name(self, domain: str) -> str:
        """Generate a schema name from the tenant domain."""
        # Clean domain and make it schema-safe
        schema_name = domain.lower().replace('.', '_').replace('-', '_')
        # Ensure it starts with a letter
        if not schema_name[0].isalpha():
            schema_name = f"tenant_{schema_name}"
        return schema_name
    
    def create_isolated_tenant_from_registry(self, registry_tenant: TenantRegistryInDB) -> dict:
        """
        Create isolated tenant data from central registry data.
        Maps TenantRegistry fields to isolated Tenant model fields.
        """
        isolated_tenant_data = {
            # Core tenant information
            'tenant_registry_id': registry_tenant.id,
            'tenant_name': registry_tenant.tenant_name,
            'tenant_type': registry_tenant.tenant_type,
            'domain': registry_tenant.domain,
            'is_active': registry_tenant.is_active,
            
            # Admin Account Information
            'admin_first_name': registry_tenant.admin_first_name,
            'admin_last_name': registry_tenant.admin_last_name,
            'admin_email': registry_tenant.admin_email,
            'admin_phone': registry_tenant.admin_phone,
            
            # Contact Information
            'email': registry_tenant.email,
            'phone': registry_tenant.phone,
            'website': registry_tenant.website,
            'social_links': registry_tenant.social_links,
            
            # Location Details (primary fields)
            'street_address': registry_tenant.street_address,
            'city': registry_tenant.city,
            'state': registry_tenant.state,
            'country': registry_tenant.country,
            'tenant_country_code': registry_tenant.tenant_country_code,
            'zip': registry_tenant.zip,
            'landmark': registry_tenant.landmark,
            'timezone': registry_tenant.timezone,
            
            # Legacy location fields (for backward compatibility)
            'tenant_address': registry_tenant.tenant_address,
            'tenant_city': registry_tenant.tenant_city,
            'tenant_state': registry_tenant.tenant_state,
            'tenant_country': registry_tenant.tenant_country,
            'tenant_timezone': registry_tenant.tenant_timezone,
            
            # Church Specific Fields
            'church_size': registry_tenant.church_size,
            'parish_name': registry_tenant.parish_name,
            'branch': registry_tenant.branch,
            'logo_url': registry_tenant.logo_url,
            'tenant_head': registry_tenant.tenant_head,
            'tenant_status': registry_tenant.tenant_status,
            
            # Configuration (copy from registry)
            'adult_consent': registry_tenant.adult_consent,
            'member_data_retention_period': registry_tenant.member_data_retention_period,
            'team_deletion_grace_period': registry_tenant.team_deletion_grace_period,
            'group_deletion_grace_period': registry_tenant.group_deletion_grace_period,
            
            # Subscription Information
            'subscription_type': registry_tenant.subscription_type,
            'subscription_plan': registry_tenant.subscription_plan,
            'subscription_status': registry_tenant.subscription_status,
            'subscription_amount': registry_tenant.subscription_amount,
            'subscription_date': registry_tenant.subscription_date,
            'subscription_start_date': registry_tenant.subscription_start_date,
            'subscription_end_date': registry_tenant.subscription_end_date,
            
            # Timestamps
            'tenant_date_created': registry_tenant.tenant_date_created,
        }
        
        # Remove None values to avoid database constraint issues
        isolated_tenant_data = {k: v for k, v in isolated_tenant_data.items() if v is not None}
        
        return isolated_tenant_data