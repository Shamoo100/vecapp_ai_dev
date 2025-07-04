from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.database.database import get_db_session
from app.api.schemas.batch_tenant import (
    BatchTenantCreate, BatchProvisioningResponse, BatchStatusRequest,
    TenantProvisioningConfig, TenantBulkUpdate, BulkUpdateResponse
)
from app.services.batch_tenant_service import BatchTenantService

logger = logging.getLogger(__name__)

router = APIRouter()
batch_service = BatchTenantService()


@router.post(
    "/batch-create",
    response_model=BatchProvisioningResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Multiple Tenants",
    description="Create multiple tenants in batch with optional parallel processing and schema provisioning."
)
async def create_tenants_batch(
    batch_request: BatchTenantCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Create multiple tenants in batch with scalable processing."""
    try:
        # Validate tenant data before processing
        validation_errors = await batch_service.validate_tenant_data(batch_request.tenants)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Validation errors found in tenant data",
                    "errors": validation_errors
                }
            )
        
        # Check for reasonable batch size
        if len(batch_request.tenants) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 50 tenants. Please split into smaller batches."
            )
        
        # Estimate processing time
        estimated_time = await batch_service.estimate_batch_time(
            len(batch_request.tenants), 
            batch_request.parallel_processing
        )
        
        logger.info(
            f"Starting batch tenant creation: {len(batch_request.tenants)} tenants, "
            f"estimated time: {estimated_time:.1f}s, parallel: {batch_request.parallel_processing}"
        )
        
        # Start batch processing
        result = await batch_service.create_tenants_batch(batch_request, db)
        
        # Add cleanup task to background
        background_tasks.add_task(batch_service.cleanup_completed_batches, max_age_hours=24)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch tenant creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.get(
    "/batch-status/{batch_id}",
    response_model=BatchProvisioningResponse,
    summary="Get Batch Status",
    description="Get the current status of a batch tenant provisioning operation."
)
async def get_batch_status(
    batch_id: str
):
    """Get the status of a batch provisioning operation."""
    try:
        result = await batch_service.get_batch_status(batch_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch operation {batch_id} not found"
            )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch status {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.get(
    "/active-batches",
    response_model=List[BatchProvisioningResponse],
    summary="List Active Batches",
    description="List all currently active batch operations."
)
async def list_active_batches():
    """List all active batch operations."""
    try:
        return await batch_service.list_active_batches()
    except Exception as e:
        logger.error(f"Error listing active batches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list active batches: {str(e)}"
        )


@router.post(
    "/bulk-update",
    response_model=BulkUpdateResponse,
    summary="Bulk Update Tenants",
    description="Update multiple tenants with the same data in bulk."
)
async def bulk_update_tenants(
    bulk_update: TenantBulkUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Perform bulk updates on multiple tenants."""
    try:
        if len(bulk_update.tenant_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bulk update cannot exceed 100 tenants. Please split into smaller batches."
            )
        
        if not bulk_update.update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update data cannot be empty"
            )
        
        logger.info(f"Starting bulk update for {len(bulk_update.tenant_ids)} tenants")
        
        result = await batch_service.bulk_update_tenants(bulk_update, db)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk update failed: {str(e)}"
        )


@router.put(
    "/config",
    summary="Update Batch Configuration",
    description="Update the configuration for batch tenant provisioning."
)
async def update_batch_config(
    config: TenantProvisioningConfig
):
    """Update batch provisioning configuration."""
    try:
        batch_service.update_config(config)
        logger.info(f"Updated batch configuration: max_concurrent={config.max_concurrent_operations}")
        return {"message": "Configuration updated successfully", "config": config}
        
    except Exception as e:
        logger.error(f"Error updating batch config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get(
    "/config",
    response_model=TenantProvisioningConfig,
    summary="Get Batch Configuration",
    description="Get the current configuration for batch tenant provisioning."
)
async def get_batch_config():
    """Get current batch provisioning configuration."""
    return batch_service.config


@router.post(
    "/validate",
    summary="Validate Tenant Data",
    description="Validate tenant data before batch processing without creating tenants."
)
async def validate_tenant_data(
    batch_request: BatchTenantCreate
):
    """Validate tenant data before batch processing."""
    try:
        validation_errors = await batch_service.validate_tenant_data(batch_request.tenants)
        
        if validation_errors:
            return {
                "valid": False,
                "errors": validation_errors,
                "error_count": len(validation_errors)
            }
        
        # Estimate processing time
        estimated_time = await batch_service.estimate_batch_time(
            len(batch_request.tenants),
            batch_request.parallel_processing
        )
        
        return {
            "valid": True,
            "tenant_count": len(batch_request.tenants),
            "estimated_processing_time_seconds": estimated_time,
            "parallel_processing": batch_request.parallel_processing,
            "max_concurrent": batch_request.max_concurrent
        }
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.delete(
    "/cleanup",
    summary="Cleanup Completed Batches",
    description="Manually trigger cleanup of completed batch operations."
)
async def cleanup_completed_batches(
    max_age_hours: int = 24
):
    """Manually trigger cleanup of completed batch operations."""
    try:
        if max_age_hours < 1 or max_age_hours > 168:  # 1 hour to 1 week
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_age_hours must be between 1 and 168 (1 week)"
            )
        
        await batch_service.cleanup_completed_batches(max_age_hours)
        return {"message": f"Cleanup completed for batches older than {max_age_hours} hours"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Batch Service Health Check",
    description="Check the health status of the batch tenant service."
)
async def health_check():
    """Health check for batch tenant service."""
    try:
        active_batches = await batch_service.list_active_batches()
        
        return {
            "status": "healthy",
            "active_batches_count": len(active_batches),
            "max_concurrent_operations": batch_service.config.max_concurrent_operations,
            "service_ready": True
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service_ready": False
        }