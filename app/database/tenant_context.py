from typing import Optional, AsyncContextManager, Dict, List
import asyncpg
from contextlib import asynccontextmanager
import logging
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class TenantContext:
    """
    Manages tenant-specific database schema contexts.
    In VecApp, tenants are identified by their schema name (e.g., demo, rccghge, test)
    rather than by numeric IDs.
    """
    
    _schema_cache: Dict[str, str] = {}
    
    @staticmethod
    def get_schema_name(schema: str) -> str:
        """
        Get the database schema name for a tenant.
        
        Args:
            schema: The tenant schema name (e.g., 'demo', 'rccghge', 'test')
            
        Returns:
            The database schema name
        """
        # In VecApp, we use the schema name directly instead of deriving it from a tenant ID
        return schema
    
    @staticmethod
    async def create_tenant_schema(schema: str) -> None:
        """
        Create a new schema for a tenant if it doesn't exist.
        
        Args:
            schema: The tenant schema name to create
        """
        schema_name = TenantContext.get_schema_name(schema)
        
        async with asyncpg.connect(settings.DATABASE_URL) as conn:
            # Check if schema exists
            schema_exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = $1
                )
                """, 
                schema_name
            )
            
            if not schema_exists:
                logger.info(f"Creating new schema for tenant: {schema}")
                await conn.execute(f"CREATE SCHEMA {schema_name}")
                
                # Create extension if needed
                await conn.execute(f"""
                    CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA {schema_name}
                """)
    
    @staticmethod
    @asynccontextmanager
    async def tenant_connection(schema: Optional[str] = None) -> AsyncContextManager[asyncpg.Connection]:
        """
        Get a database connection with tenant schema set.
        
        Args:
            schema: Optional tenant schema name to set schema context
            
        Returns:
            An async context manager yielding a database connection with proper schema context
        """
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        try:
            if schema:
                schema_name = TenantContext.get_schema_name(schema)
                await conn.execute(f"SET search_path TO {schema_name}, public")
            yield conn
        finally:
            await conn.close()
    
    @staticmethod
    async def list_tenant_schemas() -> List[str]:
        """
        List all tenant schemas in the database.
        
        Returns:
            List of tenant schema names
        """
        async with asyncpg.connect(settings.DATABASE_URL) as conn:
            schemas = await conn.fetch(
                """
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE $1 
                AND schema_name != 'public'
                """,
                '%'  # Match all schemas except those excluded
            )
            
            return [schema['schema_name'] for schema in schemas]