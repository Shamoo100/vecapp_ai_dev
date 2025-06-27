from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db_session
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantInDB
from app.services.tenant_service import TenantService

router = APIRouter()
tenant_service = TenantService()

@router.post(
    "/", 
    response_model=TenantInDB, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Tenant",
    description="Create a new tenant in the system."
)
async def create_tenant(
    tenant_in: TenantCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new tenant."""
    return await tenant_service.create_tenant(db, tenant_in)

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
    tenant = await tenant_service.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    await tenant_service.delete_tenant(db, tenant_id)