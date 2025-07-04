#!/usr/bin/env python3
"""
Test script for the multi-tenant schema provisioning API.

This script demonstrates how to:
1. Create a tenant with schema provisioning
2. Check migration status
3. Run migrations for a tenant
4. Provision schema for existing tenant
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class TenantAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def close(self):
        await self.client.aclose()
    
    async def create_tenant_with_schema(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tenant with schema provisioning."""
        url = f"{self.base_url}/api/tenants/"
        response = await self.client.post(url, json=tenant_data)
        response.raise_for_status()
        return response.json()
    
    async def provision_schema(self, tenant_id: str, force_recreate: bool = False) -> Dict[str, Any]:
        """Provision schema for an existing tenant."""
        url = f"{self.base_url}/api/tenants/provision-schema"
        data = {
            "tenant_id": tenant_id,
            "force_recreate": force_recreate
        }
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    async def run_migrations(self, tenant_id: str, target_revision: str = "head", force: bool = False) -> Dict[str, Any]:
        """Run migrations for a tenant."""
        url = f"{self.base_url}/api/tenants/run-migrations"
        data = {
            "tenant_id": tenant_id,
            "target_revision": target_revision,
            "force": force
        }
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_migration_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get migration status for a tenant."""
        url = f"{self.base_url}/api/tenants/{tenant_id}/migration-status"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def get_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant details."""
        url = f"{self.base_url}/api/tenants/{tenant_id}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()


async def demo_tenant_provisioning():
    """Demonstrate the tenant provisioning workflow."""
    tester = TenantAPITester()
    
    try:
        print("🚀 Starting Tenant Provisioning Demo\n")
        
        # Test 1: Create tenant with automatic schema provisioning and migrations
        print("📝 Test 1: Creating tenant with schema provisioning and migrations")
        tenant_data = {
            "tenant_name": "Demo Church",
            "domain": "demo-church",
            "email": "admin@demo-church.com",
            "tenant_type": "church",
            "provision_schema": True,
            "run_migrations": True
        }
        
        result = await tester.create_tenant_with_schema(tenant_data)
        tenant_id = result["tenant"]["id"]
        print(f"✅ Tenant created: {tenant_id}")
        print(f"   Schema created: {result['schema_created']}")
        print(f"   Migrations applied: {result['migrations_applied']}")
        print(f"   Message: {result['message']}\n")
        
        # Test 2: Check migration status
        print("📊 Test 2: Checking migration status")
        status = await tester.get_migration_status(tenant_id)
        print(f"   Schema provisioned: {status['schema_provisioned']}")
        print(f"   Migrations applied: {status['migrations_applied']}")
        print(f"   Current revision: {status['current_revision']}\n")
        
        # Test 3: Create another tenant without automatic provisioning
        print("📝 Test 3: Creating tenant without automatic provisioning")
        tenant_data_2 = {
            "tenant_name": "Test Church",
            "domain": "test-church",
            "email": "admin@test-church.com",
            "tenant_type": "church",
            "provision_schema": False,
            "run_migrations": False
        }
        
        result_2 = await tester.create_tenant_with_schema(tenant_data_2)
        tenant_id_2 = result_2["tenant"]["id"]
        print(f"✅ Tenant created: {tenant_id_2}")
        print(f"   Schema created: {result_2['schema_created']}")
        print(f"   Message: {result_2['message']}\n")
        
        # Test 4: Manually provision schema for the second tenant
        print("🔧 Test 4: Manually provisioning schema")
        provision_result = await tester.provision_schema(tenant_id_2)
        print(f"   Schema created: {provision_result['schema_created']}")
        print(f"   Message: {provision_result['message']}\n")
        
        # Test 5: Run migrations for the second tenant
        print("🔄 Test 5: Running migrations manually")
        migration_result = await tester.run_migrations(tenant_id_2)
        print(f"   Schema provisioned: {migration_result['schema_provisioned']}")
        print(f"   Migrations applied: {migration_result['migrations_applied']}\n")
        
        # Test 6: Final status check
        print("📊 Test 6: Final status check for both tenants")
        for i, tid in enumerate([tenant_id, tenant_id_2], 1):
            tenant = await tester.get_tenant(tid)
            status = await tester.get_migration_status(tid)
            print(f"   Tenant {i} ({tenant['tenant_name']}):")
            print(f"     Schema Name: {tenant['schema_name']}")
            print(f"     Schema Provisioned: {tenant['schema_provisioned']}")
            print(f"     Migrations Applied: {tenant['migrations_applied']}")
            print(f"     Current Revision: {status['current_revision']}")
        
        print("\n🎉 Demo completed successfully!")
        
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(demo_tenant_provisioning())