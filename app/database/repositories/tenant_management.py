from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.database.repositoriesconnection import Database

class TenantManager:
    def __init__(self, database: Database):
        self.database = database

    async def create_tenant(self, tenant_data: Dict[str, Any]) -> str:
        """Create new tenant"""
        tenant = Tenant(
            name=tenant_data['name'],
            subdomain=tenant_data['subdomain'],
            plan_type=tenant_data['plan_type'],
            created_at=datetime.now(datetime.timezone.utc),
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

    # Add this method to the TenantManager class
    
    async def _create_tenant_schema(self, tenant: Tenant):
        """Create isolated database schema for tenant
        
        This creates a dedicated schema for the tenant and initializes all required tables
        within that schema using Alembic migrations, ensuring proper data isolation between tenants.
        """
        from app.database.tenant_context import TenantContext
        import subprocess
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Create the tenant schema
        schema_name = TenantContext.get_schema_name(tenant.id)
        
        # First create the schema
        await TenantContext.create_tenant_schema(tenant.id)
        
        # Then apply all migrations to the schema
        logger.info(f"Applying migrations to new tenant schema: {schema_name}")
        try:
            cmd = ["alembic", "-x", f"tenant={schema_name}", "upgrade", "head"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully applied migrations to schema {schema_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply migrations to schema {schema_name}: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False

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