import asyncio
import uuid
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.services.multi_tenant_service import MultiTenantService
from app.api.schemas.tenant import (
    BatchTenantCreate, BatchProvisioningResponse, TenantProvisioningResult,
    BatchProvisioningStatus, TenantProvisioningConfig, TenantBulkUpdate,
    BulkUpdateResponse
)
from app.api.schemas.tenant import TenantCreate, TenantInDB


logger = logging.getLogger(__name__)


class BatchTenantService:
    """Service for scalable batch tenant provisioning and management."""
    
    def __init__(self):
        self.tenant_service = MultiTenantService()
        self.active_batches: Dict[str, BatchProvisioningResponse] = {}
        self.config = TenantProvisioningConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_operations)
    
    def update_config(self, config: TenantProvisioningConfig):
        """Update the provisioning configuration."""
        self.config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent_operations)
    
    async def create_tenants_batch(
        self, 
        batch_request: BatchTenantCreate,
        db: AsyncSession
    ) -> BatchProvisioningResponse:
        """Create multiple tenants in batch with optional parallel processing."""
        batch_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        # Initialize batch response
        batch_response = BatchProvisioningResponse(
            batch_id=batch_id,
            status=BatchProvisioningStatus.IN_PROGRESS,
            total_tenants=len(batch_request.tenants),
            started_at=started_at
        )
        
        # Store batch in active batches for status tracking
        self.active_batches[batch_id] = batch_response
        
        try:
            if batch_request.parallel_processing:
                results = await self._process_tenants_parallel(
                    batch_request, db, batch_id
                )
            else:
                results = await self._process_tenants_sequential(
                    batch_request, db, batch_id
                )
            
            # Update batch response with results
            batch_response.results = results
            batch_response.successful_tenants = sum(1 for r in results if r.success)
            batch_response.failed_tenants = sum(1 for r in results if not r.success)
            batch_response.completed_at = datetime.utcnow()
            batch_response.total_processing_time_seconds = (
                batch_response.completed_at - batch_response.started_at
            ).total_seconds()
            
            # Determine final status
            if batch_response.failed_tenants == 0:
                batch_response.status = BatchProvisioningStatus.COMPLETED
            elif batch_response.successful_tenants == 0:
                batch_response.status = BatchProvisioningStatus.FAILED
                batch_response.error_summary = "All tenant provisioning operations failed"
            else:
                batch_response.status = BatchProvisioningStatus.PARTIAL_SUCCESS
                batch_response.error_summary = f"{batch_response.failed_tenants} out of {batch_response.total_tenants} operations failed"
            
            logger.info(
                f"Batch {batch_id} completed: {batch_response.successful_tenants}/{batch_response.total_tenants} successful"
            )
            
        except Exception as e:
            logger.error(f"Batch {batch_id} failed with error: {str(e)}")
            batch_response.status = BatchProvisioningStatus.FAILED
            batch_response.error_summary = f"Batch operation failed: {str(e)}"
            batch_response.completed_at = datetime.utcnow()
        
        return batch_response
    
    async def _process_tenants_parallel(
        self, 
        batch_request: BatchTenantCreate, 
        db: AsyncSession,
        batch_id: str
    ) -> List[TenantProvisioningResult]:
        """Process tenants in parallel with concurrency control."""
        semaphore = asyncio.Semaphore(batch_request.max_concurrent)
        
        async def process_single_tenant(tenant_data: TenantCreate) -> TenantProvisioningResult:
            async with semaphore:
                return await self._provision_single_tenant(
                    tenant_data, db, batch_request, batch_id
                )
        
        # Create tasks for all tenants
        tasks = [
            process_single_tenant(tenant_data) 
            for tenant_data in batch_request.tenants
        ]
        
        # Execute all tasks and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Tenant {i} failed with exception: {str(result)}")
                processed_results.append(
                    TenantProvisioningResult(
                        tenant_name=batch_request.tenants[i].tenant_name,
                        domain=batch_request.tenants[i].domain,
                        success=False,
                        error_message=f"Exception occurred: {str(result)}"
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_tenants_sequential(
        self, 
        batch_request: BatchTenantCreate, 
        db: AsyncSession,
        batch_id: str
    ) -> List[TenantProvisioningResult]:
        """Process tenants sequentially."""
        results = []
        
        for tenant_data in batch_request.tenants:
            if not batch_request.continue_on_error and any(not r.success for r in results):
                # Stop processing if continue_on_error is False and we have failures
                logger.info(f"Stopping batch {batch_id} due to previous failures")
                break
            
            result = await self._provision_single_tenant(
                tenant_data, db, batch_request, batch_id
            )
            results.append(result)
            
            # Update batch status in active_batches
            if batch_id in self.active_batches:
                self.active_batches[batch_id].results = results
                self.active_batches[batch_id].successful_tenants = sum(1 for r in results if r.success)
                self.active_batches[batch_id].failed_tenants = sum(1 for r in results if not r.success)
        
        return results
    
    async def _provision_single_tenant(
        self, 
        tenant_data: TenantCreate, 
        db: AsyncSession,
        batch_request: BatchTenantCreate,
        batch_id: str
    ) -> TenantProvisioningResult:
        """Provision a single tenant with retry logic."""
        start_time = time.time()
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                logger.info(
                    f"Batch {batch_id}: Provisioning tenant '{tenant_data.tenant_name}' (attempt {attempt + 1})"
                )
                
                # Create tenant
                created_tenant = await self.tenant_service.create_tenant(db, tenant_data)
                
                result = TenantProvisioningResult(
                    tenant_name=tenant_data.tenant_name,
                    domain=tenant_data.domain,
                    success=True,
                    tenant_id=created_tenant.id,
                    schema_name=created_tenant.schema_name,
                    api_key=created_tenant.api_key,
                    schema_created=created_tenant.schema_provisioned,
                    migrations_applied=created_tenant.migrations_applied,
                    processing_time_seconds=time.time() - start_time
                )
                
                logger.info(
                    f"Batch {batch_id}: Successfully provisioned tenant '{tenant_data.tenant_name}'"
                )
                return result
                
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Batch {batch_id}: Attempt {attempt + 1} failed for tenant '{tenant_data.tenant_name}': {error_msg}"
                )
                
                if attempt < self.config.retry_attempts:
                    await asyncio.sleep(self.config.retry_delay_seconds)
                    continue
                else:
                    # Final attempt failed
                    return TenantProvisioningResult(
                        tenant_name=tenant_data.tenant_name,
                        domain=tenant_data.domain,
                        success=False,
                        error_message=error_msg,
                        processing_time_seconds=time.time() - start_time
                    )
    
    async def get_batch_status(self, batch_id: str) -> Optional[BatchProvisioningResponse]:
        """Get the status of a batch operation."""
        return self.active_batches.get(batch_id)
    
    async def list_active_batches(self) -> List[BatchProvisioningResponse]:
        """List all active batch operations."""
        return list(self.active_batches.values())
    
    async def cleanup_completed_batches(self, max_age_hours: int = 24):
        """Clean up completed batch operations older than specified hours."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for batch_id, batch_response in self.active_batches.items():
            if (
                batch_response.status in [BatchProvisioningStatus.COMPLETED, BatchProvisioningStatus.FAILED, BatchProvisioningStatus.PARTIAL_SUCCESS]
                and batch_response.completed_at
                and batch_response.completed_at.timestamp() < cutoff_time
            ):
                to_remove.append(batch_id)
        
        for batch_id in to_remove:
            del self.active_batches[batch_id]
            logger.info(f"Cleaned up completed batch: {batch_id}")
    
    async def bulk_update_tenants(
        self, 
        bulk_update: TenantBulkUpdate, 
        db: AsyncSession
    ) -> BulkUpdateResponse:
        """Perform bulk updates on multiple tenants."""
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        results = []
        successful_updates = 0
        failed_updates = 0
        
        logger.info(f"Starting bulk update {batch_id} for {len(bulk_update.tenant_ids)} tenants")
        
        for tenant_id in bulk_update.tenant_ids:
            try:
                # Update tenant
                updated_tenant = await self.tenant_service.update_tenant(
                    db, str(tenant_id), bulk_update.update_data
                )
                
                if updated_tenant:
                    result = {
                        "tenant_id": tenant_id,
                        "success": True,
                        "updated_fields": list(bulk_update.update_data.keys())
                    }
                    successful_updates += 1
                else:
                    result = {
                        "tenant_id": tenant_id,
                        "success": False,
                        "error": "Tenant not found"
                    }
                    failed_updates += 1
                
                # Apply migrations if requested
                if bulk_update.apply_migrations and updated_tenant:
                    try:
                        migration_result = await self.tenant_service.run_tenant_migrations(
                            db, {"tenant_id": str(tenant_id)}
                        )
                        result["migrations_applied"] = migration_result.success
                    except Exception as e:
                        result["migration_error"] = str(e)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Bulk update failed for tenant {tenant_id}: {str(e)}")
                results.append({
                    "tenant_id": tenant_id,
                    "success": False,
                    "error": str(e)
                })
                failed_updates += 1
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Bulk update {batch_id} completed: {successful_updates}/{len(bulk_update.tenant_ids)} successful"
        )
        
        return BulkUpdateResponse(
            batch_id=batch_id,
            total_tenants=len(bulk_update.tenant_ids),
            successful_updates=successful_updates,
            failed_updates=failed_updates,
            results=results,
            processing_time_seconds=processing_time
        )
    
    async def validate_tenant_data(self, tenants: List[TenantCreate]) -> List[str]:
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
    
    async def estimate_batch_time(self, tenant_count: int, parallel: bool = True) -> float:
        """Estimate the time required for batch processing."""
        # Base time per tenant (in seconds)
        base_time_per_tenant = 10.0  # Estimated time for schema creation + migrations
        
        if parallel:
            # With parallel processing, time is roughly: total_time / max_concurrent
            estimated_time = (tenant_count * base_time_per_tenant) / self.config.max_concurrent_operations
        else:
            # Sequential processing
            estimated_time = tenant_count * base_time_per_tenant
        
        # Add some buffer for overhead
        return estimated_time * 1.2