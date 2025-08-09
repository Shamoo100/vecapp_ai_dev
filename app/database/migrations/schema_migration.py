from typing import List, Dict, Any, Optional, Set
import asyncpg
import logging
from app.config.settings import get_settings
from app.database.repositories.tenant_context import TenantContext

logger = logging.getLogger(__name__)
settings = get_settings()

class SchemaMigration:
    """
    Utility for managing schema migrations across multiple tenant schemas.
    
    This class provides utilities for:
    1. Creating new tables across all tenant schemas
    2. Adding columns to existing tables across all tenant schemas
    3. Modifying columns in existing tables across all tenant schemas
    4. Migrating data between schemas
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or settings.DATABASE_URL
    
    async def list_tenant_schemas(self) -> List[str]:
        """
        List all tenant schemas in the database.
        
        Returns:
            List of tenant schema names
        """
        return await TenantContext.list_tenant_schemas()
    
    async def create_table_in_schema(self, schema: str, table_name: str, table_definition: str) -> bool:
        """
        Create a table in a specific tenant schema.
        
        Args:
            schema: The tenant schema name
            table_name: The name of the table to create
            table_definition: SQL definition of the table
            
        Returns:
            True if table was created, False if it already existed
        """
        schema_name = TenantContext.get_schema_name(schema)
        
        async with asyncpg.connect(self.connection_string) as conn:
            # Check if table exists
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = $1 AND table_name = $2
                )
                """, 
                schema_name, table_name
            )
            
            if not table_exists:
                # Create the table
                await conn.execute(f"CREATE TABLE {schema_name}.{table_name} {table_definition}")
                logger.info(f"Created table {table_name} in schema {schema_name}")
                return True
            
            return False
    
    async def add_column_to_table(self, schema: str, table_name: str, 
                                 column_name: str, column_definition: str) -> bool:
        """
        Add a column to a table in a specific tenant schema.
        
        Args:
            schema: The tenant schema name
            table_name: The name of the table to modify
            column_name: The name of the column to add
            column_definition: SQL definition of the column
            
        Returns:
            True if column was added, False if it already existed
        """
        schema_name = TenantContext.get_schema_name(schema)
        
        async with asyncpg.connect(self.connection_string) as conn:
            # Check if column exists
            column_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = $1 AND table_name = $2 AND column_name = $3
                )
                """, 
                schema_name, table_name, column_name
            )
            
            if not column_exists:
                # Add the column
                await conn.execute(
                    f"ALTER TABLE {schema_name}.{table_name} ADD COLUMN {column_name} {column_definition}"
                )
                logger.info(f"Added column {column_name} to table {table_name} in schema {schema_name}")
                return True
            
            return False
    
    async def modify_column_in_table(self, schema: str, table_name: str, 
                                    column_name: str, new_definition: str) -> bool:
        """
        Modify a column in a table in a specific tenant schema.
        
        Args:
            schema: The tenant schema name
            table_name: The name of the table to modify
            column_name: The name of the column to modify
            new_definition: New SQL definition of the column
            
        Returns:
            True if column was modified, False if it didn't exist
        """
        schema_name = TenantContext.get_schema_name(schema)
        
        async with asyncpg.connect(self.connection_string) as conn:
            # Check if column exists
            column_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = $1 AND table_name = $2 AND column_name = $3
                )
                """, 
                schema_name, table_name, column_name
            )
            
            if column_exists:
                # Modify the column
                await conn.execute(
                    f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column_name} {new_definition}"
                )
                logger.info(f"Modified column {column_name} in table {table_name} in schema {schema_name}")
                return True
            
            return False
    
    async def apply_migration_to_all_tenants(self, migration_function, *args, **kwargs) -> Dict[str, Any]:
        """
        Apply a migration function to all tenant schemas.
        
        Args:
            migration_function: Async function that performs the migration for a single schema
            *args, **kwargs: Arguments to pass to the migration function
            
        Returns:
            Dictionary with schema names and their migration results
        """
        results = {}
        schemas = await self.list_tenant_schemas()
        
        for schema in schemas:
            try:
                result = await migration_function(schema, *args, **kwargs)
                results[schema] = {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Migration failed for schema {schema}: {str(e)}")
                results[schema] = {"success": False, "error": str(e)}
        
        return results
    
    async def create_table_in_all_schemas(self, table_name: str, table_definition: str) -> Dict[str, bool]:
        """
        Create a table in all tenant schemas.
        
        Args:
            table_name: The name of the table to create
            table_definition: SQL definition of the table
            
        Returns:
            Dictionary with schema names and creation results
        """
        async def create_table_migration(schema):
            return await self.create_table_in_schema(schema, table_name, table_definition)
        
        return await self.apply_migration_to_all_tenants(create_table_migration)
    
    async def add_column_to_all_schemas(self, table_name: str, 
                                       column_name: str, column_definition: str) -> Dict[str, bool]:
        """
        Add a column to a table in all tenant schemas.
        
        Args:
            table_name: The name of the table to modify
            column_name: The name of the column to add
            column_definition: SQL definition of the column
            
        Returns:
            Dictionary with schema names and column addition results
        """
        async def add_column_migration(schema):
            return await self.add_column_to_table(schema, table_name, column_name, column_definition)
        
        return await self.apply_migration_to_all_tenants(add_column_migration)
    
    async def modify_column_in_all_schemas(self, table_name: str, 
                                         column_name: str, new_definition: str) -> Dict[str, bool]:
        """
        Modify a column in a table in all tenant schemas.
        
        Args:
            table_name: The name of the table to modify
            column_name: The name of the column to modify
            new_definition: New SQL definition of the column
            
        Returns:
            Dictionary with schema names and column modification results
        """
        async def modify_column_migration(schema):
            return await self.modify_column_in_table(schema, table_name, column_name, new_definition)
        
        return await self.apply_migration_to_all_tenants(modify_column_migration)
    
    async def migrate_tenant_data(self, tenant_id: str, tables: List[str]) -> Dict[str, int]:
        """Migrate data for a specific tenant to its schema.
        
        Args:
            tenant_id: The tenant ID to migrate data for
            tables: List of table names to migrate
            
        Returns:
            Dictionary with table names and count of migrated rows
        """
        results = {}
        schema_name = TenantContext.get_schema_name(tenant_id)
        
        # Ensure tenant schema exists
        await TenantContext.create_tenant_schema(tenant_id)
        
        async with asyncpg.connect(self.connection_string) as conn:
            # For each table, migrate data with matching tenant_id
            for table in tables:
                # Check if table exists in public schema
                table_exists = await conn.fetchval(
                    """SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = $1
                    )""", 
                    table
                )
                
                if not table_exists:
                    results[table] = 0
                    continue
                
                # Get column names for the table
                columns = await conn.fetch(
                    """SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position""",
                    table
                )
                
                column_names = [col['column_name'] for col in columns]
                
                # Skip if table doesn't have tenant_id column
                if 'tenant_id' not in column_names:
                    results[table] = 0
                    continue
                
                # Create comma-separated list of column names
                column_list = ', '.join(column_names)
                
                # Migrate data for this tenant
                migrated = await conn.execute(f"""
                    INSERT INTO {schema_name}.{table} ({column_list})
                    SELECT {column_list} FROM public.{table}
                    WHERE tenant_id = $1
                    ON CONFLICT DO NOTHING
                """, tenant_id)
                
                # Extract number of rows inserted
                if migrated:
                    count = int(migrated.split(' ')[-1])
                    results[table] = count
                else:
                    results[table] = 0
        
        return results
    
    async def list_tenants(self) -> List[str]:
        """List all tenant IDs in the database.
        
        Returns:
            List of tenant IDs found in the database
        """
        async with asyncpg.connect(self.connection_string) as conn:
            # Try to get tenant IDs from tenants table if it exists
            try:
                rows = await conn.fetch("SELECT id FROM tenants WHERE active = true")
                if rows:
                    return [str(row['id']) for row in rows]
            except Exception:
                pass
            
            # Fallback: look for tenant_id in various tables
            for table in ['users', 'organizations', 'visitors']:
                try:
                    rows = await conn.fetch(f"SELECT DISTINCT tenant_id FROM {table}")
                    if rows:
                        return [str(row['tenant_id']) for row in rows]
                except Exception:
                    continue
        
        return []
    
    async def migrate_all_tenants(self, tables: List[str]) -> Dict[str, Dict[str, int]]:
        """Migrate data for all tenants to their respective schemas.
        
        Args:
            tables: List of table names to migrate
            
        Returns:
            Dictionary with tenant IDs and their migration results
        """
        results = {}
        tenant_ids = await self.list_tenants()
        
        for tenant_id in tenant_ids:
            results[tenant_id] = await self.migrate_tenant_data(tenant_id, tables)
        
        return results