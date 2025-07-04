#!/usr/bin/env python3
"""
Batch Tenant Provisioning Example

This script demonstrates how to use the scalable batch tenant provisioning system
for creating multiple tenants simultaneously through the API.

Usage:
    python batch_tenant_provisioning_example.py
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
BATCH_TENANTS_ENDPOINT = f"{API_BASE_URL}/batch-tenants"


class BatchTenantClient:
    """Client for interacting with the batch tenant provisioning API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_batch_tenants(self, tenants_data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Create multiple tenants in batch."""
        payload = {
            "tenants": tenants_data,
            "provision_schema": kwargs.get("provision_schema", True),
            "run_migrations": kwargs.get("run_migrations", True),
            "parallel_processing": kwargs.get("parallel_processing", True),
            "max_concurrent": kwargs.get("max_concurrent", 5),
            "continue_on_error": kwargs.get("continue_on_error", True)
        }
        
        async with self.session.post(
            f"{self.base_url}/batch-tenants/batch-create",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 202:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Batch creation failed: {response.status} - {error_text}")
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get the status of a batch operation."""
        async with self.session.get(
            f"{self.base_url}/batch-tenants/batch-status/{batch_id}"
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get batch status: {response.status} - {error_text}")
    
    async def validate_tenant_data(self, tenants_data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Validate tenant data before batch processing."""
        payload = {
            "tenants": tenants_data,
            "parallel_processing": kwargs.get("parallel_processing", True),
            "max_concurrent": kwargs.get("max_concurrent", 5)
        }
        
        async with self.session.post(
            f"{self.base_url}/batch-tenants/validate",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Validation failed: {response.status} - {error_text}")
    
    async def list_active_batches(self) -> List[Dict[str, Any]]:
        """List all active batch operations."""
        async with self.session.get(
            f"{self.base_url}/batch-tenants/active-batches"
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to list active batches: {response.status} - {error_text}")
    
    async def bulk_update_tenants(self, tenant_ids: List[int], update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform bulk updates on multiple tenants."""
        payload = {
            "tenant_ids": tenant_ids,
            "update_data": update_data,
            "apply_migrations": False
        }
        
        async with self.session.post(
            f"{self.base_url}/batch-tenants/bulk-update",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Bulk update failed: {response.status} - {error_text}")


def generate_sample_tenants(count: int = 10) -> List[Dict[str, Any]]:
    """Generate sample tenant data for testing."""
    tenants = []
    
    for i in range(1, count + 1):
        tenant = {
            "tenant_name": f"Sample Church {i:03d}",
            "tenant_type": "church",
            "domain": f"church{i:03d}.example.com",
            "is_active": True,
            "email": f"admin@church{i:03d}.example.com",
            "phone": f"+1-555-{1000 + i:04d}",
            "website": f"https://church{i:03d}.example.com",
            "tenant_address": f"{100 + i} Church Street",
            "tenant_city": "Sample City",
            "tenant_state": "Sample State",
            "tenant_country": "United States",
            "tenant_country_code": "US",
            "zip": f"{10000 + i:05d}",
            "tenant_timezone": "America/New_York",
            "parish_name": f"Parish of Sample Church {i:03d}",
            "branch": "Main Branch" if i % 3 == 0 else None,
            "provision_schema": True,
            "run_migrations": True
        }
        tenants.append(tenant)
    
    return tenants


async def example_basic_batch_creation():
    """Example: Basic batch tenant creation."""
    print("\n=== Basic Batch Tenant Creation ===")
    
    # Generate sample tenant data
    tenants_data = generate_sample_tenants(5)
    
    async with BatchTenantClient() as client:
        try:
            # Validate tenant data first
            print("Validating tenant data...")
            validation_result = await client.validate_tenant_data(tenants_data)
            
            if not validation_result["valid"]:
                print(f"Validation failed: {validation_result['errors']}")
                return
            
            print(f"Validation passed. Estimated processing time: {validation_result['estimated_processing_time_seconds']:.1f}s")
            
            # Create tenants in batch
            print("Creating tenants in batch...")
            batch_result = await client.create_batch_tenants(
                tenants_data,
                parallel_processing=True,
                max_concurrent=3,
                continue_on_error=True
            )
            
            batch_id = batch_result["batch_id"]
            print(f"Batch created with ID: {batch_id}")
            print(f"Status: {batch_result['status']}")
            print(f"Total tenants: {batch_result['total_tenants']}")
            print(f"Successful: {batch_result['successful_tenants']}")
            print(f"Failed: {batch_result['failed_tenants']}")
            
            # Print individual results
            for result in batch_result["results"]:
                status = "✓" if result["success"] else "✗"
                print(f"  {status} {result['tenant_name']} ({result['domain']})")
                if not result["success"]:
                    print(f"    Error: {result.get('error_message', 'Unknown error')}")
                else:
                    print(f"    Tenant ID: {result['tenant_id']}, Schema: {result['schema_name']}")
            
        except Exception as e:
            print(f"Error: {e}")


async def example_monitor_batch_progress():
    """Example: Monitor batch processing progress."""
    print("\n=== Monitor Batch Progress ===")
    
    tenants_data = generate_sample_tenants(8)
    
    async with BatchTenantClient() as client:
        try:
            # Start batch processing
            print("Starting batch processing...")
            batch_result = await client.create_batch_tenants(
                tenants_data,
                parallel_processing=True,
                max_concurrent=2  # Slower processing to demonstrate monitoring
            )
            
            batch_id = batch_result["batch_id"]
            print(f"Batch ID: {batch_id}")
            
            # Monitor progress
            while True:
                status = await client.get_batch_status(batch_id)
                
                print(f"\rStatus: {status['status']} | "
                      f"Progress: {status['successful_tenants'] + status['failed_tenants']}/{status['total_tenants']} | "
                      f"Success: {status['successful_tenants']} | "
                      f"Failed: {status['failed_tenants']}", end="")
                
                if status["status"] in ["completed", "failed", "partial_success"]:
                    print("\n\nBatch completed!")
                    if status.get("total_processing_time_seconds"):
                        print(f"Total processing time: {status['total_processing_time_seconds']:.1f}s")
                    break
                
                await asyncio.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            print(f"\nError: {e}")


async def example_bulk_operations():
    """Example: Bulk operations on existing tenants."""
    print("\n=== Bulk Operations ===")
    
    async with BatchTenantClient() as client:
        try:
            # First, create some tenants
            tenants_data = generate_sample_tenants(3)
            batch_result = await client.create_batch_tenants(tenants_data)
            
            if batch_result["successful_tenants"] == 0:
                print("No tenants were created successfully for bulk operations demo")
                return
            
            # Extract tenant IDs from successful creations
            tenant_ids = [
                result["tenant_id"] for result in batch_result["results"]
                if result["success"] and result["tenant_id"]
            ]
            
            if not tenant_ids:
                print("No valid tenant IDs found for bulk operations")
                return
            
            print(f"Performing bulk update on {len(tenant_ids)} tenants...")
            
            # Perform bulk update
            update_data = {
                "tenant_timezone": "America/Los_Angeles",
                "is_active": True,
                "website": "https://updated-website.com"
            }
            
            bulk_result = await client.bulk_update_tenants(tenant_ids, update_data)
            
            print(f"Bulk update completed:")
            print(f"  Total tenants: {bulk_result['total_tenants']}")
            print(f"  Successful updates: {bulk_result['successful_updates']}")
            print(f"  Failed updates: {bulk_result['failed_updates']}")
            print(f"  Processing time: {bulk_result['processing_time_seconds']:.2f}s")
            
        except Exception as e:
            print(f"Error: {e}")


async def example_error_handling():
    """Example: Error handling and validation."""
    print("\n=== Error Handling and Validation ===")
    
    # Create tenant data with intentional errors
    invalid_tenants = [
        {
            "tenant_name": "Valid Church",
            "domain": "valid-church.com",
            "tenant_type": "church",
            "is_active": True
        },
        {
            "tenant_name": "",  # Invalid: empty name
            "domain": "invalid-church.com",
            "tenant_type": "church",
            "is_active": True
        },
        {
            "tenant_name": "Duplicate Domain Church",
            "domain": "valid-church.com",  # Invalid: duplicate domain
            "tenant_type": "church",
            "is_active": True
        }
    ]
    
    async with BatchTenantClient() as client:
        try:
            # Validate the invalid data
            print("Validating tenant data with errors...")
            validation_result = await client.validate_tenant_data(invalid_tenants)
            
            print(f"Validation result: {validation_result['valid']}")
            if not validation_result["valid"]:
                print("Validation errors found:")
                for error in validation_result["errors"]:
                    print(f"  - {error}")
            
            # Try to create anyway (this should fail)
            print("\nAttempting to create tenants with errors...")
            try:
                await client.create_batch_tenants(invalid_tenants)
            except Exception as e:
                print(f"Expected error occurred: {e}")
            
        except Exception as e:
            print(f"Unexpected error: {e}")


async def example_configuration_management():
    """Example: Configuration management."""
    print("\n=== Configuration Management ===")
    
    async with BatchTenantClient() as client:
        try:
            # Get current configuration
            async with client.session.get(f"{client.base_url}/batch-tenants/config") as response:
                if response.status == 200:
                    config = await response.json()
                    print("Current configuration:")
                    print(f"  Max concurrent operations: {config['max_concurrent_operations']}")
                    print(f"  Operation timeout: {config['operation_timeout_seconds']}s")
                    print(f"  Retry attempts: {config['retry_attempts']}")
                    print(f"  Retry delay: {config['retry_delay_seconds']}s")
            
            # Update configuration
            new_config = {
                "max_concurrent_operations": 8,
                "operation_timeout_seconds": 600,
                "retry_attempts": 2,
                "retry_delay_seconds": 3,
                "enable_rollback": True
            }
            
            async with client.session.put(
                f"{client.base_url}/batch-tenants/config",
                json=new_config
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"\nConfiguration updated: {result['message']}")
            
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Run all examples."""
    print("Batch Tenant Provisioning Examples")
    print("===================================")
    print("\nNote: Make sure your FastAPI server is running on http://localhost:8000")
    print("and the database is properly configured.\n")
    
    try:
        # Run examples
        await example_basic_batch_creation()
        await example_monitor_batch_progress()
        await example_bulk_operations()
        await example_error_handling()
        await example_configuration_management()
        
        print("\n=== All Examples Completed ===")
        
    except Exception as e:
        print(f"\nFailed to run examples: {e}")
        print("Make sure your API server is running and accessible.")


if __name__ == "__main__":
    asyncio.run(main())