"""
Tenant management API routes for AI Service.

Simplified routes focusing ONLY on:
- Tenant provisioning API (create and provision in one step)
- Basic health check

All other APIs are commented out to focus on simplified tenant provisioning.
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# Database dependencies
from app.database.repositories.connection import get_db_dependency
from app.database.repositories.dependencies import get_public_db, get_tenant_db

# Create dependency objects locally
PublicDB = Depends(get_public_db)
TenantDB = Depends(get_tenant_db)

# Schema imports
from app.api.schemas.tenant import (
    TenantRegistryCreate,
    TenantRegistryResponse,
    TenantRegistryUpdate,
    TenantRegistryInDB,
    TenantDeletionResponse,
    AuthSyncResponse,
    TenantSchemaProvision,
    TenantMigrationRequest,
    TenantMigrationStatus,
    BatchTenantCreate,
    BatchProvisioningResponse,
    TenantBulkUpdate
)

# Service imports
from app.services.tenant_provisioning_service import TenantProvisioningService

# Security imports - using the correct functions from auth.py
from app.security.auth import (
    get_current_user,
    get_current_tenant,
    require_authentication,
    require_tenant_context,
    require_role
)
from app.security.api_key import verify_api_key

# Initialize router
router = APIRouter()

# Initialize service
tenant_service = TenantProvisioningService()

# ============================================================================
# SIMPLIFIED TENANT PROVISIONING API (ACTIVE)
# ============================================================================

@router.post(
    "/provision",
    response_model=TenantRegistryResponse,
    status_code=201,
    summary="Provision New Tenant",
    description="Creates a new tenant with schema, database setup, and initial configuration"
)
async def provision_tenant(
    tenant_data: TenantRegistryCreate,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Create a new tenant with simplified provisioning including:
    - Tenant registry entry creation
    - Database schema provisioning
    - Running all migrations
    - Copying tenant data to isolated schema
    
    Note: This AI service does not create admin users (uses header-based auth)
    and does not manage person/family data (handled by Member Service).
    """
    try:
        # Ensure provisioning flags are set
        tenant_data.provision_schema = True
        tenant_data.run_migrations = True
        
        result = await tenant_service.provision_tenant(db, tenant_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to provision tenant: {str(e)}")

@router.post(
    "/{tenant_id}/sync-auth",
    response_model=AuthSyncResponse,
    summary="Sync Auth Data",
    description="Synchronize authentication data from external Auth Service to tenant schema using atomic batch pattern"
)
async def sync_tenant_auth_data(
    tenant_id: int,
    db: AsyncSession = PublicDB
):
    """
    Synchronize authentication data for a specific tenant using atomic batch pattern.
    
    This endpoint:
    - Fetches users from the external Auth Service
    - Validates all user data before syncing
    - Performs atomic batch sync (all or nothing)
    - Returns detailed sync statistics
    """
    try:
        # Get tenant information
        tenant = await tenant_service.get_tenant(db, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        if not tenant.schema_provisioned:
            raise HTTPException(
                status_code=400, 
                detail="Tenant schema must be provisioned before syncing auth data"
            )
        
        # Perform atomic batch auth sync
        sync_result = await tenant_service._sync_auth_data(tenant_id, tenant.schema_name)
        
        # Return detailed sync results
        return {
            "tenant_id": tenant_id,
            "schema_name": tenant.schema_name,
            "sync_pattern": "Atomic Batch",
            "success": sync_result.get('success', False),
            "total_users": sync_result.get('total_users', 0),
            "validated_users": sync_result.get('validated_users', 0),
            "synced_users": sync_result.get('synced_users', 0),
            "failed_users": sync_result.get('failed_users', 0),
            "validation_time": sync_result.get('validation_time', 0),
            "sync_time": sync_result.get('sync_time', 0),
            "total_time": sync_result.get('total_time', 0),
            "errors": sync_result.get('errors', []),
            "message": sync_result.get('message', 'Auth sync completed')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to sync auth data for tenant {tenant_id}: {str(e)}"
        )


@router.post(
    "/provision-with-auth",
    response_model=TenantRegistryResponse,
    status_code=201,
    summary="Provision New Tenant with Auth Sync",
    description="Creates a new tenant with schema, database setup, and automatic auth data synchronization"
)
async def provision_tenant_with_auth_sync(
    tenant_data: TenantRegistryCreate,
    db: AsyncSession = PublicDB
):
    """
    Create a new tenant with complete provisioning including:
    - Tenant registry entry creation
    - Database schema provisioning
    - Running all migrations
    - Copying tenant data to isolated schema
    - Atomic batch auth data synchronization
    
    This is the recommended endpoint for full tenant setup.
    """
    try:
        # Ensure provisioning flags are set
        tenant_data.provision_schema = True
        tenant_data.run_migrations = True
        
        # Provision the tenant
        result = await tenant_service.provision_tenant(db, tenant_data)
        
        # If provisioning was successful, sync auth data
        if result.schema_provisioned:
            logger.info(f"Starting auth sync for newly provisioned tenant {result.id}")
            
            # Perform atomic batch auth sync
            sync_result = await tenant_service._sync_auth_data(result.id, result.schema_name)
            
            # Add sync results to the response
            result.auth_synced = sync_result.get('success', False)
            if not result.auth_synced:
                logger.warning(f"Auth sync failed for tenant {result.id}: {sync_result.get('errors', [])}")
                # Add sync errors to provisioning errors
                if not result.errors:
                    result.errors = []
                result.errors.extend([f"Auth sync: {error}" for error in sync_result.get('errors', [])])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to provision tenant with auth sync: {str(e)}")


@router.get(
    "/health",
    summary="Tenant System Health Check",
    description="Checks the health of the tenant management system"
)
async def health_check(
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Health check endpoint for the tenant system.
    Can be used by monitoring systems.
    """
    try:
        # Basic health check - get tenant stats
        stats = await tenant_service.get_tenant_stats(db)
        
        health_status = {
            "status": "healthy",
            "tenant_count": stats.get("total_tenants", 0),
            "provisioned_count": stats.get("provisioned_tenants", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Tenant system unhealthy: {str(e)}"
        )


# ============================================================================
# TENANT MANAGEMENT OPERATIONS (ACTIVE)
# ============================================================================

@router.get(
    "",
    response_model=List[TenantRegistryInDB],
    summary="List Tenants",
    description="Get a list of all tenants with optional filtering."
)
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    search: Optional[str] = None,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Get a paginated list of tenants.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **active_only**: Filter to only active tenants
    - **search**: Search term for tenant name or domain
    """
    try:
        if search:
            tenants = await tenant_service.search_tenants(
                db, search_term=search, skip=skip, limit=limit
            )
        else:
            if active_only:
                tenants = await tenant_service.get_active_tenants(db)
            else:
                tenants = await tenant_service.get_tenants(db, skip=skip, limit=limit)
        
        return tenants
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tenants: {str(e)}")


@router.get(
    "/stats",
    summary="Tenant Statistics",
    description="Get overall tenant system statistics."
)
async def get_tenant_stats(
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Get comprehensive tenant system statistics including:
    - Total tenant count
    - Active tenants
    - Provisioned schemas
    - Migration status summary
    """
    try:
        stats = await tenant_service.get_tenant_stats(db)
        stats["last_updated"] = datetime.utcnow().isoformat()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant stats: {str(e)}")


@router.get(
    "/{tenant_identifier}",
    response_model=TenantRegistryInDB,
    summary="Get Tenant",
    description="Get a specific tenant by ID, domain, or schema name."
)
async def get_tenant(
    tenant_identifier: str,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Get detailed information about a specific tenant.
    
    The tenant_identifier can be:
    - Tenant ID (integer as string)
    - Domain name (e.g., 'example.com')
    - Schema name (e.g., 'tenant_123')
    """
    try:
        tenant = None
        
        # Try to get by ID first (if it's numeric)
        if tenant_identifier.isdigit():
            tenant = await tenant_service.get_tenant(db, tenant_identifier)
        
        # If not found or not numeric, try by domain
        if not tenant:
            tenant = await tenant_service.get_tenant_by_domain(db, tenant_identifier)
        
        # If still not found, try by schema name
        if not tenant:
            tenant = await tenant_service.get_tenant_by_schema_name(db, tenant_identifier)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return tenant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant: {str(e)}")


@router.get(
    "/by-domain/{domain}",
    response_model=TenantRegistryInDB,
    summary="Get Tenant by Domain",
    description="Get a tenant by their domain name."
)
async def get_tenant_by_domain(
    domain: str,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Get tenant information by domain name.
    Useful for domain-based tenant resolution.
    """
    try:
        tenant = await tenant_service.get_tenant_by_domain(db, domain)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant: {str(e)}")


@router.get(
    "/by-schema/{schema_name}",
    response_model=TenantRegistryInDB,
    summary="Get Tenant by Schema Name",
    description="Get a tenant by their schema name."
)
async def get_tenant_by_schema_name(
    schema_name: str,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Get tenant information by schema name.
    Useful for schema-based tenant resolution.
    """
    try:
        tenant = await tenant_service.get_tenant_by_schema_name(db, schema_name)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant: {str(e)}")


@router.put(
    "/{tenant_id}",
    response_model=TenantRegistryInDB,
    summary="Update Tenant",
    description="Update tenant information."
)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantRegistryUpdate,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Update tenant information. This only updates the tenant record,
    not the database schema or migrations.
    """
    try:
        tenant = await tenant_service.update_tenant(db, str(tenant_id), tenant_data)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tenant: {str(e)}")


@router.delete(
    "/{tenant_id}",
    response_model=TenantDeletionResponse,
    summary="Delete Tenant",
    description="Delete a tenant and its schema completely (opposite of provision)."
)
async def delete_tenant(
    tenant_id: int,
    confirm: bool = False,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Delete a tenant record and its associated schema completely.
    This is the opposite of the provision operation.
    
    - **confirm**: Must be True to confirm the destructive operation
    
    ⚠️ **Warning**: This operation is irreversible and will destroy all tenant data!
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to delete tenant and all associated data"
        )
    
    try:
        # Check if tenant exists and get details
        tenant = await tenant_service.get_tenant(db, str(tenant_id))
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Store tenant details before deletion
        schema_name = getattr(tenant, 'schema_name', None)
        schema_provisioned = getattr(tenant, 'schema_provisioned', False)
        
        # Delete tenant (includes schema dropping and all data cleanup)
        success = await tenant_service.delete_tenant(db, str(tenant_id))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete tenant")
        
        # Return structured response
        return TenantDeletionResponse(
            message="Tenant deleted successfully",
            tenant_id=str(tenant_id),
            schema_name=schema_name,
            schema_dropped=schema_provisioned,
            deleted_at=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tenant: {str(e)}")


# ============================================================================
# UTILITY OPERATIONS (ACTIVE)
# ============================================================================

@router.get(
    "/search/{search_term}",
    response_model=List[TenantRegistryInDB],
    summary="Search Tenants",
    description="Search tenants by name, domain, or email."
)
async def search_tenants(
    search_term: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Search tenants by name, domain, or email.
    """
    try:
        tenants = await tenant_service.search_tenants(
            db, search_term=search_term, skip=skip, limit=limit
        )
        return tenants
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search tenants: {str(e)}")


@router.get(
    "/active",
    response_model=List[TenantRegistryInDB],
    summary="Get Active Tenants",
    description="Get all active tenants."
)
async def get_active_tenants(
    db: AsyncSession = PublicDB  # Clean - no query parameters exposed
):
    """
    Get all active tenants.
    """
    try:
        tenants = await tenant_service.get_active_tenants(db)
        return tenants
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active tenants: {str(e)}")


# ============================================================================
# COMMENTED OUT APIS - SCHEMA OPERATIONS (LEAVE COMMENTED)
# ============================================================================

# @router.post(
#     "/{tenant_id}/provision-schema",
#     response_model=TenantProvisionResponse,
#     summary="Provision Tenant Schema",
#     description="Provision database schema for an existing tenant."
# )
# async def provision_tenant_schema(
#     tenant_id: int,
#     force_recreate: bool = False,
#     db: AsyncSession = Depends(get_db_dependency)
# ):
#     """
#     Provision database schema for an existing tenant.
#     
#     - **force_recreate**: If True, drops and recreates the schema if it exists
#     
#     ⚠️ **Warning**: force_recreate will destroy all existing data in the schema!
#     """
#     try:
#         # Get tenant
#         tenant = await tenant_service.get_tenant(db, str(tenant_id))
#         if not tenant:
#             raise HTTPException(status_code=404, detail="Tenant not found")
#         
#         # Create tenant data for provisioning
#         tenant_data = TenantRegistryCreate(
#             tenant_name=tenant.tenant_name,
#             domain=tenant.domain,
#             provision_schema=True,
#             run_migrations=True
#         )
#         
#         # If force recreate, drop schema first
#         if force_recreate and tenant.schema_provisioned:
#             await tenant_service.repository.drop_tenant_schema(db, tenant.schema_name)
#             await tenant_service.repository.update_schema_status(
#                 db, tenant.id, schema_provisioned=False, migrations_applied=False
#             )
#         
#         result = await tenant_service.provision_tenant(db, tenant_data)
#         return result
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to provision schema: {str(e)}")

# ... rest of schema operations remain commented ...


