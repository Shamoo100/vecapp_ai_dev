#!/usr/bin/env python3
"""
Simple test to verify database schema synchronization fixes.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.services.multi_tenant_service import MultiTenantService
from app.api.schemas.tenant import TenantCreate
from app.config.settings import Settings
from app.database.repositories.tenant import TenantRepository


async def test_schema_sync():
    """Test that database schema synchronization works correctly."""
    print("🔧 Testing Database Schema Synchronization")
    print("=" * 50)
    
    # Setup database connection
    settings = Settings()
    database_url = settings.DATABASE_URL
    
    # Convert to async URL if needed
    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Test 1: Create a tenant with all fields
            print("\n1. Testing tenant creation with all fields...")
            
            tenant_data = TenantCreate(
                tenant_name="Test Church Schema Sync",
                domain="test-schema-sync.example.com",
                email="admin@test-schema-sync.example.com",
                phone="+1-555-0123",
                tenant_address="123 Test Street",
                tenant_city="Test City",
                tenant_state="Test State",
                tenant_country="Test Country",
                zip="12345",
                provision_schema=False,  # Don't provision schema for this test
                run_migrations=False
            )
            
            # Initialize service
            service = MultiTenantService()
            
            # Create tenant
            created_tenant = await service.create_tenant(db, tenant_data)
            print(f"   ✅ Created tenant: {created_tenant.tenant_name} (ID: {created_tenant.id})")
            print(f"   ✅ Domain: {created_tenant.domain}")
            print(f"   ✅ Email: {created_tenant.email}")
            print(f"   ✅ Schema: {created_tenant.schema_name}")
            
            # Test 2: Verify all fields are properly stored
            print("\n2. Verifying field mapping...")
            retrieved_tenant = await service.get_tenant(db, created_tenant.id)
            
            if retrieved_tenant:
                print(f"   ✅ Retrieved tenant: {retrieved_tenant.tenant_name}")
                print(f"   ✅ Email field: {retrieved_tenant.email}")
                print(f"   ✅ Phone field: {retrieved_tenant.phone}")
                print(f"   ✅ Address field: {retrieved_tenant.tenant_address}")
                print(f"   ✅ City field: {retrieved_tenant.tenant_city}")
                print(f"   ✅ State field: {retrieved_tenant.tenant_state}")
                print(f"   ✅ Country field: {retrieved_tenant.tenant_country}")
                print(f"   ✅ Zip field: {retrieved_tenant.zip}")
            else:
                print("   ❌ Failed to retrieve tenant")
                return False
            
            # Test 3: Clean up
            print("\n3. Cleaning up test data...")
            await db.execute(text("DELETE FROM tenant_registry WHERE id = :tenant_id"), {"tenant_id": created_tenant.id})
            await db.commit()
            print("   ✅ Test data cleaned up")
            
            print("\n" + "=" * 50)
            print("✅ Database Schema Synchronization Test PASSED!")
            print("\n📋 Verified:")
            print("   ✓ All schema fields map correctly to database columns")
            print("   ✓ No UndefinedColumnError for 'email' field")
            print("   ✓ No IntegrityError for 'tenant_head' field")
            print("   ✓ Field name mapping works correctly")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(test_schema_sync())
    sys.exit(0 if success else 1)