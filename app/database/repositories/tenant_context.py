# app/database/repositories/tenant_context.py
from typing import Optional, AsyncContextManager, Dict, List
import asyncpg
from contextlib import asynccontextmanager
import logging
from contextvars import ContextVar
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Context variable for tenant management
tenant_context_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)

def get_current_tenant_id() -> Optional[str]:
    """Get the current tenant ID from context"""
    return tenant_context_var.get()

class TenantContext:
    """Manages tenant-specific database schema contexts"""
    _schema_cache: Dict[str, str] = {}
    
    @staticmethod
    def get_schema_name(schema: str) -> str:
        """Get normalized schema name for a tenant"""
        return schema.lower()  # Normalize to lowercase
    
    @staticmethod
    async def create_tenant_schema(schema: str) -> None:
        """Create a new schema for a tenant if it doesn't exist"""
        schema_name = TenantContext.get_schema_name(schema)
        
        # Check cache first
        if schema_name in TenantContext._schema_cache:
            return
            
        async with asyncpg.connect(settings.DATABASE_URL) as conn:
            schema_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = $1)",
                schema_name
            )
            
            if not schema_exists:
                logger.info(f"Creating new schema for tenant: {schema}")
                async with conn.transaction():
                    await conn.execute(f"CREATE SCHEMA {schema_name}")
                    await conn.execute(f"""
                        CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA {schema_name}
                    """)
                # Add to cache
                TenantContext._schema_cache[schema_name] = "exists"
    
    @staticmethod
    @asynccontextmanager
    async def tenant_connection(schema: Optional[str] = None) -> AsyncContextManager[asyncpg.Connection]:
        """Get connection with tenant schema set in search_path"""
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        try:
            if schema:
                schema_name = TenantContext.get_schema_name(schema)
                await conn.execute(f"SET search_path TO {schema_name}, public")
            yield conn
        except asyncpg.PostgresError as e:
            logger.error(f"Database connection error: {str(e)}")
            raise HTTPException(500, "Database connection failed") from e
        finally:
            await conn.close()
    
    @staticmethod
    async def list_tenant_schemas() -> List[str]:
        """List all tenant schemas in the database"""
        async with asyncpg.connect(settings.DATABASE_URL) as conn:
            schemas = await conn.fetch(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'public'"
            )
            return [record['schema_name'] for record in schemas]

class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate tenant context"""
    
    async def dispatch(self, request: Request, call_next):
        # Extract tenant ID from headers or URL path
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id and "tenants" in request.url.path:
            path_parts = request.url.path.split("/")
            if "tenants" in path_parts:
                tenant_index = path_parts.index("tenants") + 1
                if tenant_index < len(path_parts):
                    tenant_id = path_parts[tenant_index]
        
        # Validate tenant ID format
        if tenant_id and not tenant_id.isalnum():
            logger.warning(f"Invalid tenant ID format: {tenant_id}")
            tenant_id = None
            
        # Set tenant context
        token = None
        if tenant_id:
            request.state.tenant_id = tenant_id
            token = tenant_context_var.set(tenant_id)
            logger.debug(f"Set tenant context: {tenant_id}")
        
        try:
            response = await call_next(request)
            return response
        finally:
            if token:
                tenant_context_var.reset(token)

# FastAPI Dependency
async def get_tenant_id(request: Request) -> Optional[str]:
    """Dependency to inject tenant ID into routes"""
    return getattr(request.state, 'tenant_id', None) or get_current_tenant_id()