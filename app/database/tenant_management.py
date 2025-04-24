from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from core.database import Database

class TenantManager:
    def __init__(self, database: Database):
        self.database = database

    async def create_tenant(self, tenant_data: Dict[str, Any]) -> str:
        """Create new tenant"""
        tenant = Tenant(
            name=tenant_data['name'],
            subdomain=tenant_data['subdomain'],
            plan_type=tenant_data['plan_type'],
            created_at=datetime.utcnow(),
            status='active'
        )
        
        # Create tenant database schema
        await self._create_tenant_schema(tenant)
        
        # Store tenant details
        tenant_id = await self.database.store_tenant(tenant)
        
        # Initialize tenant configurations
        await self._initialize_tenant_config(tenant_id, tenant_data)
        
        return tenant_id

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant details"""
        return await self.database.get_tenant(tenant_id)

    async def update_tenant_config(
        self,
        tenant_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """Update tenant configuration"""
        return await self.database.update_tenant_config(tenant_id, config)

    async def _create_tenant_schema(self, tenant: Tenant):
        """Create isolated database schema for tenant"""
        schema_name = f"tenant_{tenant.id}"
        await self.database.execute_query(f"""
            CREATE SCHEMA IF NOT EXISTS {schema_name};
            
            -- Create tenant-specific tables
            CREATE TABLE {schema_name}.visitors (
                -- visitor table schema
            );
            
            CREATE TABLE {schema_name}.volunteers (
                -- volunteer table schema
            );
            
            -- Add more tenant-specific tables
        """)

    async def _initialize_tenant_config(
        self,
        tenant_id: str,
        tenant_data: Dict[str, Any]
    ):
        """Initialize default tenant configuration"""
        default_config = {
            'follow_up_workflow': {
                'initial_delay_hours': 24,
                'reminder_frequency_days': 7,
                'max_attempts': 3
            },
            'notification_preferences': {
                'email_enabled': True,
                'sms_enabled': True,
                'in_app_enabled': True
            },
            'ai_customization': {
                'persona_generation_enabled': True,
                'custom_prompts': {}
            }
        }
        
        # Merge with tenant-provided config
        config = {**default_config, **tenant_data.get('config', {})}
        await self.database.store_tenant_config(tenant_id, config) 