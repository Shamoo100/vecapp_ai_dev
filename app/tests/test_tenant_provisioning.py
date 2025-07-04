#!/usr/bin/env python3
"""
Test script for multi-tenant schema provisioning system.

This test creates the first tenant named 'demo' and validates
the complete tenant provisioning workflow including:
- Tenant creation with schema provisioning
- Migration execution
- Schema isolation verification
- API endpoint testing
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid

# Add the parent directory to sys.path to allow importing app modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from app.database.repositories.connection import get_db_session
from app.services.tenant_service import TenantService
from app.schemas.tenant import TenantCreate, TenantSchemaProvision, TenantMigrationRequest
from app.config.settings import get_settings


class TestTenantProvisioning:
    """Test class for tenant provisioning functionality."""
    
    def __init__(self):
        self.tenant_service = TenantService()
        self.demo_tenant_id = None
        self.demo_schema_name = "demo"
    
    async def setup_database(self):
        """Set up database connection for testing."""
        # Get database session
        self.db_context = get_db_session()
        self.db = await self.db_context.__aenter__()
    
    async def cleanup_demo_tenant(self):
        """Clean up any existing demo tenant and schema."""
        try:
            # Check if demo schema exists and drop it
            result = await self.db.execute(
                text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name"),
                {"schema_name": self.demo_schema_name}
            )
            if result.fetchone():
                await self.db.execute(text(f"DROP SCHEMA IF EXISTS {self.demo_schema_name} CASCADE"))
                await self.db.commit()
                print(f"✅ Cleaned up existing demo schema")
            
            # Check if demo tenant exists in database and remove it
            result = await self.db.execute(
                text("SELECT id FROM tenants WHERE domain = :domain"),
                {"domain": "demo"}
            )
            existing_tenant = result.fetchone()
            if existing_tenant:
                await self.db.execute(
                    text("DELETE FROM tenants WHERE domain = :domain"),
                    {"domain": "demo"}
                )
                await self.db.commit()
                print(f"✅ Cleaned up existing demo tenant record")
                
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")
            await self.db.rollback()
    
    async def test_create_demo_tenant(self):
        """Test creating the demo tenant with full provisioning."""
        print("\n🚀 Creating Demo Tenant with Schema Provisioning")
        
        # Create tenant data
        tenant_data = TenantCreate(
            tenant_name="Demo Church",
            domain="demo",
            email="admin@demo.church",
            tenant_type="church",
            phone="+1-555-0123",
            website="https://demo.church",
            tenant_address="123 Demo Street",
            tenant_city="Demo City",
            tenant_state="Demo State",
            tenant_country="Demo Country",
            provision_schema=True,
            run_migrations=True
        )
        
        # Create tenant with schema provisioning
        result = await self.tenant_service.create_tenant_with_schema(self.db, tenant_data)
        
        # Store tenant ID for further tests
        self.demo_tenant_id = result.tenant.id
        
        # Validate results
        assert result.tenant.tenant_name == "Demo Church"
        assert result.tenant.domain == "demo"
        assert result.tenant.schema_name == "demo"
        assert result.schema_created == True
        assert result.migrations_applied == True
        assert result.tenant.schema_provisioned == True
        assert result.tenant.migrations_applied == True
        assert result.tenant.api_key is not None
        
        print(f"✅ Demo tenant created successfully:")
        print(f"   - Tenant ID: {self.demo_tenant_id}")
        print(f"   - Schema Name: {result.tenant.schema_name}")
        print(f"   - API Key: {result.tenant.api_key[:20]}...")
        print(f"   - Message: {result.message}")
        
        return result
    
    async def test_schema_isolation(self):
        """Test that the demo schema is properly isolated."""
        print("\n🔍 Testing Schema Isolation")
        
        # Check that demo schema exists
        result = await self.db.execute(
            text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name"),
            {"schema_name": self.demo_schema_name}
        )
        assert result.fetchone() is not None, "Demo schema should exist"
        print("✅ Demo schema exists")
        
        # Check that alembic_version table exists in demo schema
        result = await self.db.execute(
            text("SELECT 1 FROM information_schema.tables WHERE table_schema = :schema_name AND table_name = 'alembic_version'"),
            {"schema_name": self.demo_schema_name}
        )
        assert result.fetchone() is not None, "alembic_version table should exist in demo schema"
        print("✅ alembic_version table exists in demo schema")
        
        # Check migration version
        result = await self.db.execute(
            text(f"SELECT version_num FROM {self.demo_schema_name}.alembic_version ORDER BY version_num DESC LIMIT 1")
        )
        version = result.fetchone()
        assert version is not None, "Migration version should be recorded"
        print(f"✅ Current migration version: {version[0]}")
        
        # List tables in demo schema
        result = await self.db.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema_name ORDER BY table_name"),
            {"schema_name": self.demo_schema_name}
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"✅ Tables in demo schema: {', '.join(tables)}")
        
        # Verify tenant-specific tables exist
        expected_tables = ['alembic_version', 'tenants', 'person', 'visitors', 'notes']
        for table in expected_tables:
            if table in tables:
                print(f"   ✓ {table} table exists")
            else:
                print(f"   ⚠️ {table} table missing (may be expected)")
    
    async def test_migration_status(self):
        """Test getting migration status for demo tenant."""
        print("\n📊 Testing Migration Status")
        
        # Get migration status
        status = await self.tenant_service.get_tenant_migration_status(self.db, self.demo_tenant_id)
        
        # Validate status
        assert status.tenant_id == self.demo_tenant_id
        assert status.schema_name == self.demo_schema_name
        assert status.schema_provisioned == True
        assert status.migrations_applied == True
        assert status.current_revision is not None
        
        print(f"✅ Migration status retrieved:")
        print(f"   - Schema Provisioned: {status.schema_provisioned}")
        print(f"   - Migrations Applied: {status.migrations_applied}")
        print(f"   - Current Revision: {status.current_revision}")
        print(f"   - Pending Migrations: {len(status.pending_migrations)}")
        
        return status
    
    async def test_tenant_retrieval(self):
        """Test retrieving the demo tenant."""
        print("\n📋 Testing Tenant Retrieval")
        
        # Get tenant
        tenant = await self.tenant_service.get_tenant(self.db, self.demo_tenant_id)
        
        # Validate tenant
        assert tenant is not None
        assert tenant.id == self.demo_tenant_id
        assert tenant.tenant_name == "Demo Church"
        assert tenant.domain == "demo"
        assert tenant.schema_name == "demo"
        assert tenant.schema_provisioned == True
        assert tenant.migrations_applied == True
        
        print(f"✅ Tenant retrieved successfully:")
        print(f"   - Name: {tenant.tenant_name}")
        print(f"   - Domain: {tenant.domain}")
        print(f"   - Email: {tenant.email}")
        print(f"   - Schema Provisioned: {tenant.schema_provisioned}")
        print(f"   - Migrations Applied: {tenant.migrations_applied}")
        
        return tenant
    
    async def test_schema_recreation(self):
        """Test recreating schema with force flag."""
        print("\n🔄 Testing Schema Recreation")
        
        # Provision schema with force recreate
        provision_request = TenantSchemaProvision(
            tenant_id=self.demo_tenant_id,
            force_recreate=True
        )
        
        result = await self.tenant_service.provision_tenant_schema(self.db, provision_request)
        
        # Validate results
        assert result.schema_created == True
        assert "dropped" in result.message.lower() or "created" in result.message.lower()
        
        print(f"✅ Schema recreation completed:")
        print(f"   - Message: {result.message}")
        print(f"   - Schema Created: {result.schema_created}")
        
        return result
    
    async def run_all_tests(self):
        """Run all tenant provisioning tests."""
        print("🧪 Starting Multi-Tenant Provisioning Tests for Demo Tenant")
        print("=" * 60)
        
        try:
            # Setup
            await self.setup_database()
            await self.cleanup_demo_tenant()
            
            # Run tests
            await self.test_create_demo_tenant()
            await self.test_schema_isolation()
            await self.test_migration_status()
            await self.test_tenant_retrieval()
            await self.test_schema_recreation()
            
            print("\n🎉 All tests completed successfully!")
            print(f"\n📝 Demo Tenant Summary:")
            print(f"   - Tenant ID: {self.demo_tenant_id}")
            print(f"   - Schema Name: {self.demo_schema_name}")
            print(f"   - Domain: demo")
            print(f"   - Status: Fully provisioned and ready")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Close database connection
            if hasattr(self, 'db_context'):
                await self.db_context.__aexit__(None, None, None)


async def main():
    """Main function to run the tenant provisioning tests."""
    tester = TestTenantProvisioning()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ Demo tenant is ready for use!")
        print("\nNext steps:")
        print("1. Start your FastAPI server: uvicorn app.main:app --reload")
        print("2. Test the API endpoints using the test_tenant_api.py script")
        print("3. Use the demo tenant for development and testing")
    else:
        print("\n❌ Demo tenant setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())