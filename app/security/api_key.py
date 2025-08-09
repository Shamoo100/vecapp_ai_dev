from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.connection import DatabaseConnection
from app.data.repositories.tenant_provisioning_repository import TenantProvisioningRepository
from app.api.schemas.tenant import TenantRegistryInDB

api_key_header = APIKeyHeader(name="X-API-Key")

async def get_current_tenant(
    api_key: str = Depends(api_key_header),
    database: DatabaseConnection = Depends()
) -> TenantRegistryInDB:
    """Get current tenant from API key"""
    async with database.get_session() as db:
        tenant_repo = TenantProvisioningRepository()
        tenant = await tenant_repo.get_tenant_by_api_key(db, api_key)
        if not tenant:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        return tenant

async def verify_api_key(
    api_key: str = Depends(api_key_header)
) -> str:
    """Verify API key is valid"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    return api_key