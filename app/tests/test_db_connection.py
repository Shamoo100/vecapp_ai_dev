"""
Database connection test script.

This script tests the database connection using the application settings.
It can be run directly or imported and used in the application startup.
"""
import asyncio
import asyncpg
import sys
from pathlib import Path
import os

# Add the parent directory to sys.path to allow importing app modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from app.config.settings import get_settings

async def test_database_connection():
    """
    Test the database connection using the application settings.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    settings = get_settings()
    print("\n=== Database Connection Test ===")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Database User: {settings.DB_USER}")
    print(f"Database Host: {settings.DB_HOST}")
    print(f"Database Port: {settings.DB_PORT}")
    print(f"Database Name: {settings.DB_NAME}")
    
    try:
        # Create a connection pool
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=settings.DB_MIN_CONNECTIONS,
            max_size=settings.DB_MAX_CONNECTIONS,
            command_timeout=settings.DB_COMMAND_TIMEOUT,
            max_inactive_connection_lifetime=settings.DB_MAX_INACTIVE_CONNECTION_LIFETIME
        )
        
        # Test the connection by executing a simple query
        async with pool.acquire() as conn:
            version = await conn.fetchval("SELECT version();")
            print(f"\n✅ Connection successful!")
            print(f"PostgreSQL version: {version}")
            
            # Test schema access
            try:
                # List all schemas
                schemas = await conn.fetch("SELECT schema_name FROM information_schema.schemata;")
                print(f"\nAvailable schemas:")
                for schema in schemas:
                    print(f"  - {schema['schema_name']}")
                
                # List tables in public schema
                tables = await conn.fetch(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
                )
                print(f"\nTables in public schema:")
                if tables:
                    for table in tables:
                        print(f"  - {table['table_name']}")
                else:
                    print("  No tables found in public schema")
            except Exception as e:
                print(f"⚠️ Schema test error: {str(e)}")
        
        # Close the pool
        await pool.close()
        return True
        
    except asyncpg.PostgresError as e:
        print(f"\n❌ Connection failed: {str(e)}")
        
        # Provide helpful troubleshooting information
        print("\nTroubleshooting steps:")
        print("1. Check if PostgreSQL is running:")
        print("   $ pg_isready")
        print(f"2. Verify the database '{settings.DB_NAME}' exists:")
        print(f"   $ psql -U {settings.DB_USER} -c '\\l'")
        print("3. Check user permissions:")
        print(f"   $ psql -U {settings.DB_USER} -c '\\du'")
        print("4. Verify connection parameters in .env file")
        print("5. Try connecting manually:")
        print(f"   $ psql -U {settings.DB_USER} -h {settings.DB_HOST} -p {settings.DB_PORT} -d {settings.DB_NAME}")
        
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

def run_test():
    """Run the database connection test."""
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(test_database_connection())
    return success

if __name__ == "__main__":
    success = run_test()
    if not success:
        sys.exit(1)  # Exit with error code if connection failed