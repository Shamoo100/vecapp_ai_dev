#!/usr/bin/env python3
"""
Script to create a new tenant in the VecApp system.
Usage: python create_tenant.py tenant_name [--active=true/false]
"""

import asyncio
import sys
import argparse
import os
from uuid import uuid4
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.tenant_management import TenantManager
from app.database.models.tenant import Tenant
from app.core.config import settings
from app.database.repositories.tenant_context import TenantContext


async def create_tenant(tenant_name: str, active: bool = True):
    """
    Create a new tenant with the given name.
    
    Args:
        tenant_name: String value representing the tenant name
        active: Whether the tenant should be active initially
    
    Returns:
        The ID of the newly created tenant
    """
    # Generate a unique ID for the tenant (will be used as schema name)
    tenant_id = str(uuid4())
    
    # Create tenant data dictionary
    tenant_data = {
        'name': tenant_name,
        'subdomain': tenant_name.lower().replace(' ', '-'),
        'plan_type': 'standard',  # Default plan type
        'active': active,
        'config': {
            'notification_preferences': {
                'email_enabled': True,
                'sms_enabled': True
            }
        }
    }
    
    # Create the tenant schema
    schema_name = tenant_name.lower().replace(' ', '_')
    await TenantContext.create_tenant_schema(schema_name)
    
    # Create tenant record
    tenant = Tenant(
        id=tenant_id,
        name=tenant_name,
        api_key=f"vecapp_{uuid4().hex}",  # Generate a unique API key
        active=active,
        settings=tenant_data.get('config', {})
    )
    
    # Store the tenant in the database
    # Note: In a real implementation, you would use your database connection
    # This is a simplified example
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        session.add(tenant)
        await session.commit()
    
    print(f"✅ Tenant created successfully!")
    print(f"Tenant ID: {tenant_id}")
    print(f"Tenant Name: {tenant_name}")
    print(f"Schema Name: {schema_name}")
    print(f"API Key: {tenant.api_key}")
    
    return tenant_id


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Create a new tenant')
    parser.add_argument('tenant_name', type=str, help='Name of the tenant')
    parser.add_argument('--active', type=str, default='true', 
                        choices=['true', 'false'],
                        help='Whether the tenant should be active')
    
    args = parser.parse_args()
    return args.tenant_name, args.active.lower() == 'true'


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Tenant name is required")
        print("Usage: python create_tenant.py tenant_name [--active=true/false]")
        sys.exit(1)
    
    tenant_name, active = parse_args()
    asyncio.run(create_tenant(tenant_name, active))