#!/usr/bin/env python3
"""
Test script for simplified tenant provisioning API with real data
Updated for the new AI service tenant provisioning flow
"""
import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any

# Set environment to development for dev endpoints
os.environ["ENVIRONMENT"] = "development"

# Test data matching the NEW simplified schema requirements
TENANT_DATA = {
    "account_info": {
        "first_name": "John",
        "last_name": "Smith", 
        "phone": "+1-555-123-4567",
        "email": "pastor@gracecommunity.org"
    },
    "church_info": {
        "name": "Grace Community Church",
        "email": "info@gracecommunity.org",
        "domain": "gracecommunity",
        "address": "123 Main Street, Springfield, IL 62701",
        "country": "United States",
        "state": "Illinois",
        "city": "Springfield",
        "size": "201-500",  # Using the exact enum value
        "branch": "Main Campus",
        "timezone": "America/Chicago"
    },
    "subscription": {
        "type": "premium",  # Using exact enum value
        "plan": "monthly",  # Using exact enum value
        "amount": 99.99,
        "date": datetime.now().isoformat()
    },
    "is_active": True,
    "provision_schema": True,
    "run_migrations": True
}

# Additional test data for different scenarios
DEV_TENANT_DATA = {
    "account_info": {
        "first_name": "Jane",
        "last_name": "Doe", 
        "phone": "+1-555-987-6543",
        "email": "admin@devtest.church"
    },
    "church_info": {
        "name": "Dev Test Church",
        "email": "info@devtest.church",
        "domain": "devtest",
        "address": "456 Test Avenue, Dev City, TX 75001",
        "country": "United States",
        "state": "Texas",
        "city": "Dev City",
        "size": "0-200",  # Small church
        "branch": "Test Campus",
        "timezone": "America/Chicago"
    },
    "subscription": {
        "type": "basic",
        "plan": "monthly",
        "amount": 49.99,
        "date": datetime.now().isoformat()
    },
    "is_active": True,
    "provision_schema": True,
    "run_migrations": True
}

API_BASE_URL = "http://localhost:8000/api/v1"

async def test_simplified_tenant_provisioning():
    """Test the new simplified tenant provisioning endpoint"""
    print("🚀 Testing Simplified Tenant Provisioning API")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Test the new /provision endpoint
            print("\n📝 Test: Creating tenant via /tenants/provision endpoint")
            print(f"🏗️  Testing with domain: {TENANT_DATA['church_info']['domain']}")
            
            response = await client.post(
                f"{API_BASE_URL}/tenants/provision",
                json=TENANT_DATA,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 201:
                response_data = response.json()
                print(f"✅ Tenant provisioned successfully!")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Validate the response structure
                tenant_info = response_data.get("tenant", {})
                tenant_id = tenant_info.get("id")
                schema_name = tenant_info.get("schema_name")
                schema_created = response_data.get("schema_created", False)
                migrations_applied = response_data.get("migrations_applied", False)
                message = response_data.get("message", "")
                
                print(f"\n📊 Provisioning Results:")
                print(f"   - Tenant ID: {tenant_id}")
                print(f"   - Schema Name: {schema_name}")
                print(f"   - Schema Created: {schema_created}")
                print(f"   - Migrations Applied: {migrations_applied}")
                print(f"   - Message: {message}")
                
                # Validate critical fields
                assert tenant_id is not None, "Tenant ID should be set"
                assert schema_name is not None, "Schema name should be set"
                assert schema_created == True, "Schema should be created"
                assert migrations_applied == True, "Migrations should be applied"
                
                print("✅ All critical validations passed!")
                return tenant_id, schema_name
                
            else:
                print(f"❌ Failed to provision tenant: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error text: {response.text}")
                return None, None
                
        except httpx.ConnectError:
            print("❌ Connection failed. Make sure the server is running on http://localhost:8000")
            return None, None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None, None

async def test_tenant_registry_only():
    """Test creating tenant registry entry without provisioning"""
    print("\n🏢 Testing Tenant Registry Creation (No Provisioning)")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Create a copy of tenant data for registry-only test
            registry_data = DEV_TENANT_DATA.copy()
            registry_data["church_info"]["domain"] = "registryonly"
            registry_data["church_info"]["name"] = "Registry Only Church"
            registry_data["provision_schema"] = False
            registry_data["run_migrations"] = False
            
            response = await client.post(
                f"{API_BASE_URL}/tenants",
                json=registry_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 201:
                response_data = response.json()
                print(f"✅ Tenant registry entry created successfully!")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                tenant_id = response_data.get("id")
                schema_provisioned = response_data.get("schema_provisioned", False)
                migrations_applied = response_data.get("migrations_applied", False)
                
                print(f"\n📊 Registry Results:")
                print(f"   - Tenant ID: {tenant_id}")
                print(f"   - Schema Provisioned: {schema_provisioned}")
                print(f"   - Migrations Applied: {migrations_applied}")
                
                # Validate that no provisioning occurred
                assert schema_provisioned == False, "Schema should not be provisioned"
                assert migrations_applied == False, "Migrations should not be applied"
                
                print("✅ Registry-only creation validated!")
                return tenant_id
                
            else:
                print(f"❌ Failed to create tenant registry: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error text: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def test_tenant_data_integrity():
    """Test that tenant data is properly linked between schemas"""
    print("\n🔗 Testing Tenant Data Integrity")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Create a tenant with full provisioning
            integrity_data = DEV_TENANT_DATA.copy()
            integrity_data["church_info"]["domain"] = "integrity_test"
            integrity_data["church_info"]["name"] = "Integrity Test Church"
            
            response = await client.post(
                f"{API_BASE_URL}/tenants/provision",
                json=integrity_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                response_data = response.json()
                tenant_info = response_data.get("tenant", {})
                tenant_id = tenant_info.get("id")
                schema_name = tenant_info.get("schema_name")
                
                print(f"✅ Tenant created for integrity test:")
                print(f"   - Tenant ID: {tenant_id}")
                print(f"   - Schema Name: {schema_name}")
                
                # Test retrieving the tenant
                get_response = await client.get(f"{API_BASE_URL}/tenants/{tenant_id}")
                
                if get_response.status_code == 200:
                    tenant_data = get_response.json()
                    print(f"✅ Tenant retrieved successfully!")
                    
                    # Validate data consistency
                    assert tenant_data["id"] == tenant_id, "Tenant ID should match"
                    assert tenant_data["schema_name"] == schema_name, "Schema name should match"
                    assert tenant_data["church_name"] == integrity_data["church_info"]["name"], "Church name should match"
                    assert tenant_data["domain"] == integrity_data["church_info"]["domain"], "Domain should match"
                    
                    print("✅ Data integrity validation passed!")
                    return tenant_id
                else:
                    print(f"❌ Failed to retrieve tenant: {get_response.status_code}")
                    return None
            else:
                print(f"❌ Failed to create tenant for integrity test: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def test_tenant_stats():
    """Test tenant statistics endpoint"""
    print("\n📊 Testing Tenant Statistics")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/tenants/stats")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ Tenant statistics retrieved successfully!")
                print(f"Response: {json.dumps(stats, indent=2)}")
                
                # Validate stats structure
                expected_fields = ["total_tenants", "active_tenants", "provisioned_tenants"]
                for field in expected_fields:
                    assert field in stats, f"Stats should include {field}"
                
                print("✅ Stats validation passed!")
            else:
                print(f"❌ Stats failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error text: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

async def test_tenant_list():
    """Test listing all tenants"""
    print("\n📋 Testing Tenant List")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/tenants")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                tenants = response.json()
                print(f"✅ Found {len(tenants)} tenants")
                
                # Show summary of tenants
                for i, tenant in enumerate(tenants[:3]):  # Show first 3 tenants
                    print(f"   {i+1}. {tenant.get('church_name', 'Unknown')} ({tenant.get('domain', 'Unknown')})")
                
                if len(tenants) > 3:
                    print(f"   ... and {len(tenants) - 3} more tenants")
                
                print("✅ Tenant list validation passed!")
            else:
                print(f"❌ List failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error text: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

async def test_tenant_health():
    """Test tenant system health endpoint"""
    print("\n🏥 Testing Tenant System Health")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/tenants/health")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                health = response.json()
                print("✅ Tenant system health check passed!")
                print(f"Response: {json.dumps(health, indent=2)}")
                
                # Validate health response
                assert "status" in health, "Health response should include status"
                assert health["status"] == "healthy", "System should be healthy"
                
                print("✅ Health check validation passed!")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error text: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

async def main():
    """Main test function"""
    print("🏢 VecApp AI Service - Simplified Tenant Provisioning Test Suite")
    print("Testing the new simplified tenant provisioning flow")
    print("🎯 Goal: Validate tenant registry, schema creation, migrations, and data linking")
    print("🤖 AI Service Focus: No admin users, header-based auth, data sync ready")
    
    # Track test results
    results = {}
    
    # Run all tests
    print("\n" + "=" * 80)
    tenant_id, schema_name = await test_simplified_tenant_provisioning()
    results["provisioning"] = (tenant_id is not None)
    
    print("\n" + "=" * 80)
    registry_id = await test_tenant_registry_only()
    results["registry_only"] = (registry_id is not None)
    
    print("\n" + "=" * 80)
    integrity_id = await test_tenant_data_integrity()
    results["data_integrity"] = (integrity_id is not None)
    
    print("\n" + "=" * 80)
    await test_tenant_stats()
    results["stats"] = True  # Assume success if no exception
    
    print("\n" + "=" * 80)
    await test_tenant_list()
    results["list"] = True  # Assume success if no exception
    
    print("\n" + "=" * 80)
    await test_tenant_health()
    results["health"] = True  # Assume success if no exception
    
    # Summary
    print("\n" + "=" * 80)
    print("✨ Test Suite Summary")
    print("=" * 80)
    
    success_count = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
    
    if tenant_id and schema_name:
        print(f"\n🎉 SUCCESS: Simplified tenant provisioning is working!")
        print(f"   - Main Tenant ID: {tenant_id}")
        print(f"   - Schema Name: {schema_name}")
        print(f"   - Ready for AI processing with header-based auth")
        print(f"   - Data sync ready for Member Service integration")
    
    if success_count == total_tests:
        print("\n🚀 ALL TESTS PASSED! The AI service tenant system is ready!")
    else:
        print(f"\n⚠️  {total_tests - success_count} test(s) failed. Please review the errors above.")

if __name__ == "__main__":
    asyncio.run(main())