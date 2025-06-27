import asyncpg
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from uuid import UUID
from app.config.settings import get_settings
from app.database.tenant_context import TenantContext
from app.security.tenant_context import get_current_tenant_id

settings = get_settings()

class ConnectionManager:
    """Manages database connections with tenant context support"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def initialize(cls):
        """Initialize the connection pool"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
    
    @classmethod
    async def close(cls):
        """Close the connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
    
    @classmethod
    @asynccontextmanager
    async def get_connection(cls, tenant_id: Optional[UUID] = None):
        """Get a connection from the pool with tenant schema set
        
        Args:
            tenant_id: Optional tenant ID to set schema context
            
        Yields:
            Database connection with proper schema context
        """
        if cls._pool is None:
            await cls.initialize()
            
        # If tenant_id not provided, try to get from current context
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
            
        async with cls._pool.acquire() as conn:
            if tenant_id:
                schema_name = TenantContext.get_schema_name(str(tenant_id))
                await conn.execute(f"SET search_path TO {schema_name}, public")
            try:
                yield conn
            finally:
                # Reset search path to public when done
                if tenant_id:
                    await conn.execute("SET search_path TO public")
    
    @classmethod
    async def execute_transaction(cls, 
                                 callback, 
                                 tenant_id: Optional[UUID] = None, 
                                 *args, 
                                 **kwargs):
        """Execute a callback within a transaction
        
        Args:
            callback: Async function that takes a connection as first argument
            tenant_id: Optional tenant ID to set schema context
            *args: Additional arguments to pass to callback
            **kwargs: Additional keyword arguments to pass to callback
            
        Returns:
            Result of the callback
        """
        async with cls.get_connection(tenant_id) as conn:
            async with conn.transaction():
                return await callback(conn, *args, **kwargs)