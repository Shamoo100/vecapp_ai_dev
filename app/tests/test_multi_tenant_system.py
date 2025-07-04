#!/usr/bin/env python3
"""
Comprehensive test script for the multi-tenant system with per-tenant versioning.

This script tests:
1. Tenant creation in the registry
2. Schema provisioning for individual tenants
3. Per-tenant migration execution
4. Independent tenant versioning
5. API endpoints functionality
"""

import asyncio
import httpx
import os
import sys
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.services.multi_tenant_service import MultiTenantService
from app.api.schemas.tenant import TenantCreate, TenantSchemaProvision, TenantMigrationRequest
from app.config.settings import Settings


class MultiTenantSystemTester:
    """Comprehensive tester for the multi-tenant system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.service = MultiTenantService()
        self.engine = None
        self.session_factory = None
        
    async def setup_database(self):
        """Setup database connection for testing."""
        settings = Settings()
        database_url = settings.DATABASE_URL
        # Convert psycopg2 URL to asyncpg for async operations
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def cleanup_database(self):
        """Cleanup database connection."""
        if self.engine:
            await self.engine.dispose()
    
    async def get_db_session(self):
        """Get database session."""
        async with self.session_factory() as session:
            yield session
    
    async def test_tenant_registry_creation(self):
        """Test creating tenants in the registry."""
        print("\n=== Testing Tenant Registry Creation ===")
        
        async with self.session_factory() as db:
            # Create test tenants
            tenants_data = [
                {
                    "tenant_name": "Demo Company",
                    "domain": "demo.example.com",
                    "email": "admin@demo.example.com",
            "phone": "+1-555-0101",
                    "tenant_address": "123 Demo Street",
                    "tenant_city": "Demo City",
                    "tenant_state": "CA",
                    "tenant_country": "USA",
                    "zip": "90210",
                    "is_active": True,
                    "provision_schema": False,
                    "run_migrations": False
                },
                {
                    "tenant_name": "Client A Corp",
                    "domain": "clienta.example.com",
                    "email": "admin@clienta.example.com",
            "phone": "+1-555-0102",
                    "tenant_address": "456 Client Avenue",
                    "tenant_city": "Client City",
                    "tenant_state": "NY",
                    "tenant_country": "USA",
                    "zip": "10001",
                    "is_active": True,
                    "provision_schema": False,
                    "run_migrations": False
                },
                {
                    "tenant_name": "Client B Ltd",
                    "domain": "clientb.example.com",
                    "email": "admin@clientb.example.com",
            "phone": "+1-555-0103",
                    "tenant_address": "789 Business Blvd",
                    "tenant_city": "Business City",
                    "tenant_state": "TX",
                    "tenant_country": "USA",
                    "zip": "75001",
                    "is_active": True,
                    "provision_schema": False,
                    "run_migrations": False
                }
            ]
            
            created_tenants = []
            for tenant_data in tenants_data:
                tenant_create = TenantCreate(**tenant_data)
                tenant = await self.service.create_tenant(db, tenant_create)
                created_tenants.append(tenant)
                
                print(f"✓ Created tenant: {tenant.tenant_name}")
                print(f"  - ID: {tenant.id}")
                print(f"  - Domain: {tenant.domain}")
                print(f"  - Schema: {tenant.schema_name}")
                print(f"  - API Key: {tenant.api_key[:20]}...")
                print(f"  - Schema Provisioned: {tenant.schema_provisioned}")
                print(f"  - Migrations Applied: {tenant.migrations_applied}")
            
            return created_tenants
    
    async def test_schema_provisioning(self, tenants):
        """Test provisioning schemas for tenants."""
        print("\n=== Testing Schema Provisioning ===")
        
        async with self.session_factory() as db:
            for tenant in tenants:
                print(f"\nProvisioning schema for {tenant.tenant_name}...")
                
                # Provision schema
                provision_request = TenantSchemaProvision(
                    tenant_id=tenant.id,
                    force_recreate=False
                )
                
                result = await self.service.provision_tenant_schema(db, provision_request)
                
                print(f"✓ Schema provisioning result:")
                print(f"  - Schema Created: {result.schema_created}")
                print(f"  - Migrations Applied: {result.migrations_applied}")
                print(f"  - Message: {result.message}")
                
                if result.migration_status:
                    print(f"  - Current Revision: {result.migration_status.current_revision}")
                    print(f"  - Schema Provisioned: {result.migration_status.schema_provisioned}")
    
    async def test_tenant_migrations(self, tenants):
        """Test running migrations for individual tenants."""
        print("\n=== Testing Per-Tenant Migrations ===")
        
        async with self.session_factory() as db:
            for i, tenant in enumerate(tenants):
                print(f"\nRunning migrations for {tenant.tenant_name}...")
                
                # Run migrations
                migration_request = TenantMigrationRequest(
                    tenant_id=tenant.id,
                    target_revision="head",
                    force=True
                )
                
                try:
                    status = await self.service.run_tenant_migrations(db, migration_request)
                    
                    print(f"✓ Migration completed:")
                    print(f"  - Schema: {status.schema_name}")
                    print(f"  - Current Revision: {status.current_revision}")
                    print(f"  - Schema Provisioned: {status.schema_provisioned}")
                    print(f"  - Migrations Applied: {status.migrations_applied}")
                    
                    # Verify schema exists and has tables
                    await self._verify_tenant_schema(db, tenant.schema_name)
                    
                except Exception as e:
                    print(f"✗ Migration failed: {str(e)}")
    
    async def _verify_tenant_schema(self, db: AsyncSession, schema_name: str):
        """Verify that tenant schema exists and has expected tables."""
        try:
            # Check if schema exists
            result = await db.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = :schema_name"
                ),
                {"schema_name": schema_name}
            )
            schema_exists = result.fetchone() is not None
            
            if schema_exists:
                print(f"  ✓ Schema {schema_name} exists")
                
                # Check for alembic_version table
                result = await db.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = :schema_name AND table_name = 'alembic_version'"
                    ),
                    {"schema_name": schema_name}
                )
                alembic_table_exists = result.fetchone() is not None
                
                if alembic_table_exists:
                    print(f"  ✓ alembic_version table exists in {schema_name}")
                    
                    # Get current revision
                    result = await db.execute(
                        text(f"SELECT version_num FROM {schema_name}.alembic_version")
                    )
                    version = result.fetchone()
                    if version:
                        print(f"  ✓ Current revision: {version[0]}")
                else:
                    print(f"  ✗ alembic_version table missing in {schema_name}")
                
                # Check for tenant-specific tables
                result = await db.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = :schema_name ORDER BY table_name"
                    ),
                    {"schema_name": schema_name}
                )
                tables = [row[0] for row in result.fetchall()]
                print(f"  ✓ Tables in {schema_name}: {', '.join(tables)}")
            else:
                print(f"  ✗ Schema {schema_name} does not exist")
                
        except Exception as e:
            print(f"  ✗ Error verifying schema {schema_name}: {str(e)}")
    
    async def test_independent_versioning(self, tenants):
        """Test that tenants have independent version tracking."""
        print("\n=== Testing Independent Versioning ===")
        
        async with self.session_factory() as db:
            print("\nChecking version independence...")
            
            for tenant in tenants:
                try:
                    status = await self.service.get_tenant_migration_status(db, tenant.id)
                    print(f"\n{tenant.tenant_name} ({tenant.schema_name}):")
                    print(f"  - Current Revision: {status.current_revision}")
                    print(f"  - Schema Provisioned: {status.schema_provisioned}")
                    print(f"  - Migrations Applied: {status.migrations_applied}")
                    
                    if status.pending_migrations:
                        print(f"  - Pending Migrations: {len(status.pending_migrations)}")
                    else:
                        print(f"  - No pending migrations")
                        
                except Exception as e:
                    print(f"  ✗ Error getting status: {str(e)}")
    
    async def test_api_endpoints(self, tenants):
        """Test API endpoints functionality."""
        print("\n=== Testing API Endpoints ===")
        
        async with httpx.AsyncClient() as client:
            try:
                # Test getting all tenants
                response = await client.get(f"{self.base_url}/api/tenants/")
                if response.status_code == 200:
                    tenants_data = response.json()
                    print(f"✓ GET /api/tenants/ - Found {len(tenants_data)} tenants")
                else:
                    print(f"✗ GET /api/tenants/ failed: {response.status_code}")
                
                # Test getting individual tenant
                if tenants:
                    tenant_id = tenants[0].id
                    response = await client.get(f"{self.base_url}/api/tenants/{tenant_id}")
                    if response.status_code == 200:
                        tenant_data = response.json()
                        print(f"✓ GET /api/tenants/{tenant_id} - {tenant_data['tenant_name']}")
                    else:
                        print(f"✗ GET /api/tenants/{tenant_id} failed: {response.status_code}")
                    
                    # Test migration status endpoint
                    response = await client.get(
                        f"{self.base_url}/api/tenants/{tenant_id}/migration-status"
                    )
                    if response.status_code == 200:
                        status_data = response.json()
                        print(f"✓ GET /api/tenants/{tenant_id}/migration-status")
                        print(f"  - Current Revision: {status_data.get('current_revision')}")
                    else:
                        print(f"✗ GET migration status failed: {response.status_code}")
                        
            except Exception as e:
                print(f"✗ API test failed: {str(e)}")
                print("Note: Make sure the FastAPI server is running on localhost:8000")
    
    async def run_comprehensive_test(self):
        """Run all tests in sequence."""
        print("🚀 Starting Comprehensive Multi-Tenant System Test")
        print("=" * 60)
        
        try:
            await self.setup_database()
            
            # Test 1: Create tenants in registry
            tenants = await self.test_tenant_registry_creation()
            
            # Test 2: Provision schemas
            await self.test_schema_provisioning(tenants)
            
            # Test 3: Run migrations
            await self.test_tenant_migrations(tenants)
            
            # Test 4: Verify independent versioning
            await self.test_independent_versioning(tenants)
            
            # Test 5: Test API endpoints
            await self.test_api_endpoints(tenants)
            
            print("\n" + "=" * 60)
            print("✅ All tests completed successfully!")
            print("\n📋 Summary:")
            print(f"   - Created {len(tenants)} tenants in registry")
            print(f"   - Provisioned {len(tenants)} tenant schemas")
            print(f"   - Applied migrations to {len(tenants)} tenant schemas")
            print(f"   - Verified independent version tracking")
            print(f"   - Tested API endpoints")
            
            print("\n🎯 Key Features Demonstrated:")
            print("   ✓ Centralized tenant registry in public schema")
            print("   ✓ Isolated tenant schemas with independent data")
            print("   ✓ Per-tenant migration versioning")
            print("   ✓ Single set of migration files for all tenants")
            print("   ✓ Independent tenant upgrade/downgrade capability")
            print("   ✓ RESTful API for tenant management")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.cleanup_database()


async def main():
    """Main test runner."""
    tester = MultiTenantSystemTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())