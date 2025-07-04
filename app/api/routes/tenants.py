from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db_session
from app.api.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantInDB, TenantSchemaProvision, 
    TenantMigrationRequest, TenantMigrationStatus, TenantProvisionResponse,
    TenantStatusUpdate
)
from app.services.multi_tenant_service import MultiTenantService

router = APIRouter()
tenant_service = MultiTenantService()

@router.post(
    "/", 
    response_model=TenantInDB, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Tenant",
    description="Create a new tenant in the system with optional schema provisioning and migrations."
)
async def create_tenant(
    tenant_in: TenantCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new tenant with optional schema provisioning and migrations."""
    try:
        result = await tenant_service.create_tenant(db, tenant_in)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/provision-schema", 
    response_model=TenantProvisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Provision Tenant Schema",
    description="Provision database schema for an existing tenant."
)
async def provision_tenant_schema(
    provision_request: TenantSchemaProvision,
    db: AsyncSession = Depends(get_db_session)
):
    """Provision database schema for an existing tenant."""
    try:
        result = await tenant_service.provision_tenant_schema(db, provision_request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post(
    "/run-migrations", 
    response_model=TenantMigrationStatus,
    status_code=status.HTTP_200_OK,
    summary="Run Tenant Migrations",
    description="Run database migrations for a specific tenant."
)
async def run_tenant_migrations(
    migration_request: TenantMigrationRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Run database migrations for a specific tenant."""
    try:
        result = await tenant_service.run_tenant_migrations(db, migration_request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/{tenant_id}/migration-status", 
    response_model=TenantMigrationStatus,
    summary="Get Tenant Migration Status",
    description="Get migration status for a specific tenant."
)
async def get_tenant_migration_status(
    tenant_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get migration status for a specific tenant."""
    try:
        result = await tenant_service.get_tenant_migration_status(db, tenant_id)
        result.tenant_id = tenant_id
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/{tenant_id}", 
    response_model=TenantInDB,
    summary="Get Tenant",
    description="Get a tenant by ID."
)
async def get_tenant(
    tenant_id: str, 
    db: AsyncSession = Depends(get_db_session)
):
    """Get a tenant by ID."""
    tenant = await tenant_service.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return tenant

@router.get(
    "/", 
    response_model=List[TenantInDB],
    summary="Get Tenants",
    description="Get a list of tenants with pagination."
)
async def get_tenants(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db_session)
):
    """Get multiple tenants with pagination."""
    return await tenant_service.get_tenants(db, skip=skip, limit=limit)

@router.put(
    "/{tenant_id}", 
    response_model=TenantInDB,
    summary="Update Tenant",
    description="Update a tenant's information."
)
async def update_tenant(
    tenant_id: str, 
    tenant_in: TenantUpdate, 
    db: AsyncSession = Depends(get_db_session)
):
    """Update a tenant."""
    tenant = await tenant_service.update_tenant(db, tenant_id, tenant_in)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return tenant

@router.post(
    "/{tenant_id}/provision", 
    response_model=TenantProvisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Provision Complete Tenant",
    description="Provision schema and run migrations for an existing tenant."
)
async def provision_complete_tenant(
    tenant_id: str,
    run_migrations: bool = True,
    db: AsyncSession = Depends(get_db_session)
):
    """Provision complete tenant (schema + migrations)."""
    try:
        result = await tenant_service.provision_tenant(db, tenant_id, run_migrations)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete(
    "/{tenant_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Tenant",
    description="Delete a tenant from the system."
)
async def delete_tenant(
    tenant_id: str, 
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a tenant."""
    success = await tenant_service.delete_tenant(db, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found or could not be deleted"
        )