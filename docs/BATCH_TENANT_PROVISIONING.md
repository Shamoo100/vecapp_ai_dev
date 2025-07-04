# Batch Tenant Provisioning System Documentation

## Overview

The **Batch Tenant Provisioning System** is a comprehensive solution for automated tenant onboarding in multi-tenant SaaS applications. It provides streamlined workflows for creating multiple tenants simultaneously, with integrated database schema provisioning, API key management, and validation processes.

## Architecture

### 🏗️ **System Components**

```
app/services/
├── batch_tenant_service.py     # Core batch provisioning logic
├── tenant_service.py           # Individual tenant operations
└── tenant_manager.py           # Schema and database management

app/api/endpoints/
└── tenant_endpoints.py         # REST API endpoints

app/database/
├── models/
│   └── tenant_registry.py      # Tenant registry model
└── migrations/                 # Dual migration system
    ├── public/                 # Global schema migrations
    └── tenant/                 # Tenant-specific migrations
```

### 🔄 **Provisioning Flow**

```mermaid
graph TD
    A[Batch Request] --> B[Validate Input Data]
    B --> C[Generate Unique Identifiers]
    C --> D[Create Database Schemas]
    D --> E[Run Tenant Migrations]
    E --> F[Register in Tenant Registry]
    F --> G[Generate API Keys]
    G --> H[Validate Provisioning]
    H --> I[Return Results]
    
    J[Error Handling] --> K[Rollback Operations]
    K --> L[Cleanup Resources]
    
    B -.-> J
    D -.-> J
    E -.-> J
    F -.-> J
```

## Core Features

### 🚀 **Batch Operations**

- **Parallel Processing**: Provision multiple tenants simultaneously
- **Atomic Operations**: All-or-nothing provisioning with rollback
- **Progress Tracking**: Real-time status updates for batch operations
- **Error Isolation**: Individual tenant failures don't affect others

### 🔒 **Security & Validation**

- **Unique Constraint Enforcement**: Prevent duplicate domains/schemas
- **API Key Generation**: Secure, unique keys for each tenant
- **Input Sanitization**: Comprehensive validation of tenant data
- **Schema Isolation**: Complete data separation between tenants

### 📊 **Monitoring & Logging**

- **Detailed Audit Trails**: Track all provisioning operations
- **Performance Metrics**: Monitor provisioning times and success rates
- **Error Reporting**: Comprehensive error logging and alerting
- **Health Checks**: Validate tenant provisioning status

## API Reference

### 📋 **Endpoints**

#### 1. **Batch Tenant Creation**

```http
POST /api/tenants/batch
Content-Type: application/json

{
  "tenants": [
    {
      "tenant_name": "demo_company",
      "domain": "demo.example.com",
      "schema_name": "demo_schema",
      "description": "Demo tenant for testing",
      "settings": {
        "features": ["analytics", "reporting"],
        "limits": {
          "users": 100,
          "storage_gb": 50
        }
      }
    },
    {
      "tenant_name": "client_abc",
      "domain": "abc.example.com",
      "schema_name": "client_abc_schema",
      "description": "ABC Corporation tenant",
      "settings": {
        "features": ["analytics", "reporting", "advanced_security"],
        "limits": {
          "users": 500,
          "storage_gb": 200
        }
      }
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Batch tenant provisioning completed",
  "results": [
    {
      "tenant_name": "demo_company",
      "status": "success",
      "tenant_id": 1,
      "api_key": "tk_demo_abc123...",
      "schema_name": "demo_schema",
      "domain": "demo.example.com"
    },
    {
      "tenant_name": "client_abc",
      "status": "success",
      "tenant_id": 2,
      "api_key": "tk_abc_def456...",
      "schema_name": "client_abc_schema",
      "domain": "abc.example.com"
    }
  ],
  "summary": {
    "total_requested": 2,
    "successful": 2,
    "failed": 0,
    "processing_time_ms": 1250
  }
}
```

#### 2. **Individual Tenant Creation**

```http
POST /api/tenants
Content-Type: application/json

{
  "tenant_name": "new_client",
  "domain": "newclient.example.com",
  "schema_name": "new_client_schema",
  "description": "New client tenant",
  "settings": {
    "features": ["basic"],
    "limits": {
      "users": 50,
      "storage_gb": 25
    }
  }
}
```

#### 3. **Tenant Status Check**

```http
GET /api/tenants/{tenant_id}/status
```

**Response**:
```json
{
  "tenant_id": 1,
  "tenant_name": "demo_company",
  "status": "active",
  "schema_status": "provisioned",
  "migration_version": "20250102_000001",
  "created_at": "2025-01-02T10:30:00Z",
  "last_activity": "2025-01-02T15:45:00Z"
}
```

#### 4. **List All Tenants**

```http
GET /api/tenants?page=1&limit=50
```

## Implementation Details

### 🔧 **BatchTenantService**

```python
class BatchTenantService:
    """Service for batch tenant provisioning operations."""
    
    def __init__(self, db_session, tenant_manager, migration_manager):
        self.db = db_session
        self.tenant_manager = tenant_manager
        self.migration_manager = migration_manager
        self.logger = logging.getLogger(__name__)
    
    async def provision_batch(self, tenant_data_list: List[dict]) -> dict:
        """Provision multiple tenants in batch."""
        results = []
        successful = 0
        failed = 0
        start_time = time.time()
        
        for tenant_data in tenant_data_list:
            try:
                result = await self._provision_single_tenant(tenant_data)
                results.append(result)
                
                if result['status'] == 'success':
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to provision tenant {tenant_data.get('tenant_name')}: {e}")
                results.append({
                    'tenant_name': tenant_data.get('tenant_name'),
                    'status': 'error',
                    'error': str(e)
                })
                failed += 1
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'success': failed == 0,
            'results': results,
            'summary': {
                'total_requested': len(tenant_data_list),
                'successful': successful,
                'failed': failed,
                'processing_time_ms': processing_time
            }
        }
    
    async def _provision_single_tenant(self, tenant_data: dict) -> dict:
        """Provision a single tenant with full validation."""
        try:
            # 1. Validate input data
            validated_data = self._validate_tenant_data(tenant_data)
            
            # 2. Generate unique identifiers
            api_key = self._generate_api_key(validated_data['tenant_name'])
            
            # 3. Create database schema
            schema_created = await self._provision_schema(validated_data['schema_name'])
            if not schema_created:
                raise Exception("Failed to create database schema")
            
            # 4. Register tenant in registry
            tenant_record = await self._register_tenant(validated_data, api_key)
            
            # 5. Validate provisioning
            if await self._validate_tenant_provisioning(tenant_record.id):
                return {
                    'tenant_name': tenant_record.tenant_name,
                    'status': 'success',
                    'tenant_id': tenant_record.id,
                    'api_key': api_key,
                    'schema_name': tenant_record.schema_name,
                    'domain': tenant_record.domain
                }
            else:
                raise Exception("Tenant provisioning validation failed")
                
        except Exception as e:
            # Rollback operations if any step fails
            await self._rollback_tenant_provisioning(tenant_data)
            raise e
    
    def _validate_tenant_data(self, tenant_data: dict) -> dict:
        """Validate and sanitize tenant input data."""
        required_fields = ['tenant_name', 'domain', 'schema_name']
        
        for field in required_fields:
            if not tenant_data.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Validate domain format
        domain = tenant_data['domain']
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$', domain):
            raise ValueError(f"Invalid domain format: {domain}")
        
        # Validate schema name (PostgreSQL identifier rules)
        schema_name = tenant_data['schema_name']
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
            raise ValueError(f"Invalid schema name: {schema_name}")
        
        # Check for existing domain/schema
        if self._check_domain_exists(domain):
            raise ValueError(f"Domain already exists: {domain}")
        
        if self._check_schema_exists(schema_name):
            raise ValueError(f"Schema already exists: {schema_name}")
        
        return tenant_data
    
    def _generate_api_key(self, tenant_name: str) -> str:
        """Generate secure, unique API key for tenant."""
        import secrets
        import hashlib
        
        # Create unique identifier
        timestamp = str(int(time.time()))
        random_bytes = secrets.token_bytes(16)
        
        # Generate hash
        hash_input = f"{tenant_name}_{timestamp}_{random_bytes.hex()}"
        api_key_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:32]
        
        # Format as tenant key
        return f"tk_{tenant_name[:8]}_{api_key_hash}"
    
    async def _provision_schema(self, schema_name: str) -> bool:
        """Provision database schema for tenant."""
        try:
            # Run tenant migrations using the dual migration system
            result = subprocess.run([
                'python', 'app/database/migrations/migrate.py',
                'init-tenant', '--schema', schema_name
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                self.logger.info(f"Schema {schema_name} provisioned successfully")
                return True
            else:
                self.logger.error(f"Schema provisioning failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error provisioning schema {schema_name}: {e}")
            return False
    
    async def _register_tenant(self, tenant_data: dict, api_key: str) -> TenantRegistry:
        """Register tenant in the tenant registry."""
        tenant_record = TenantRegistry(
            tenant_name=tenant_data['tenant_name'],
            domain=tenant_data['domain'],
            schema_name=tenant_data['schema_name'],
            api_key=api_key,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(tenant_record)
        await self.db.commit()
        await self.db.refresh(tenant_record)
        
        return tenant_record
    
    async def _validate_tenant_provisioning(self, tenant_id: int) -> bool:
        """Validate that tenant was provisioned correctly."""
        try:
            # Check tenant registry entry
            tenant = await self.db.get(TenantRegistry, tenant_id)
            if not tenant or not tenant.is_active:
                return False
            
            # Check schema exists and has correct tables
            schema_valid = await self._validate_schema_structure(tenant.schema_name)
            
            return schema_valid
            
        except Exception as e:
            self.logger.error(f"Tenant validation failed: {e}")
            return False
    
    async def _rollback_tenant_provisioning(self, tenant_data: dict):
        """Rollback tenant provisioning in case of failure."""
        try:
            schema_name = tenant_data.get('schema_name')
            domain = tenant_data.get('domain')
            
            # Remove from tenant registry if exists
            if domain:
                tenant = await self.db.query(TenantRegistry).filter(
                    TenantRegistry.domain == domain
                ).first()
                if tenant:
                    await self.db.delete(tenant)
                    await self.db.commit()
            
            # Drop schema if exists
            if schema_name:
                await self._drop_schema(schema_name)
                
            self.logger.info(f"Rollback completed for tenant: {tenant_data.get('tenant_name')}")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
```

### 🔧 **TenantManager Integration**

```python
class TenantManager:
    """Manages tenant schema operations and database connections."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
    
    async def create_tenant_schema(self, schema_name: str) -> bool:
        """Create a new tenant schema with proper isolation."""
        try:
            async with self.engine.begin() as conn:
                # Create schema
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                
                # Set appropriate permissions
                await conn.execute(text(f"GRANT USAGE ON SCHEMA {schema_name} TO tenant_user"))
                await conn.execute(text(f"GRANT CREATE ON SCHEMA {schema_name} TO tenant_user"))
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {e}")
            return False
    
    async def validate_schema_structure(self, schema_name: str) -> bool:
        """Validate that schema has required tables and structure."""
        required_tables = ['tenant', 'person', 'alembic_version']
        
        try:
            async with self.engine.begin() as conn:
                for table in required_tables:
                    result = await conn.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema = :schema AND table_name = :table)"
                    ), {'schema': schema_name, 'table': table})
                    
                    if not result.scalar():
                        logger.error(f"Missing table {table} in schema {schema_name}")
                        return False
                
                return True
                
        except Exception as e:
            logger.error(f"Schema validation failed for {schema_name}: {e}")
            return False
    
    async def drop_tenant_schema(self, schema_name: str) -> bool:
        """Safely drop a tenant schema and all its contents."""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                return True
                
        except Exception as e:
            logger.error(f"Failed to drop schema {schema_name}: {e}")
            return False
```

## Configuration

### 🔧 **Environment Variables**

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/vecapp

# Tenant Configuration
DEFAULT_TENANT_FEATURES=["basic", "analytics"]
MAX_TENANTS_PER_BATCH=50
TENANT_SCHEMA_PREFIX="tenant_"

# Security Configuration
API_KEY_LENGTH=32
API_KEY_PREFIX="tk_"

# Performance Configuration
BATCH_PROCESSING_TIMEOUT=300
SCHEMA_CREATION_TIMEOUT=60
```

### 📋 **Application Settings**

```python
# app/config/tenant_settings.py
class TenantSettings:
    # Validation Rules
    MAX_TENANT_NAME_LENGTH = 255
    MAX_DOMAIN_LENGTH = 255
    MAX_SCHEMA_NAME_LENGTH = 63
    
    # Default Features
    DEFAULT_FEATURES = ["basic", "analytics"]
    AVAILABLE_FEATURES = [
        "basic", "analytics", "reporting", 
        "advanced_security", "api_access", "webhooks"
    ]
    
    # Resource Limits
    DEFAULT_USER_LIMIT = 100
    DEFAULT_STORAGE_LIMIT_GB = 50
    MAX_USER_LIMIT = 10000
    MAX_STORAGE_LIMIT_GB = 1000
    
    # Batch Processing
    MAX_BATCH_SIZE = 50
    BATCH_TIMEOUT_SECONDS = 300
    
    # Schema Naming
    SCHEMA_NAME_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    DOMAIN_PATTERN = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$'
```

## Usage Examples

### 🚀 **Basic Batch Provisioning**

```python
# Example: Provision multiple tenants
import asyncio
from app.services.batch_tenant_service import BatchTenantService

async def provision_demo_tenants():
    service = BatchTenantService(db_session, tenant_manager, migration_manager)
    
    tenant_data = [
        {
            "tenant_name": "demo_company",
            "domain": "demo.example.com",
            "schema_name": "demo_schema",
            "description": "Demo tenant for testing",
            "settings": {
                "features": ["analytics", "reporting"],
                "limits": {"users": 100, "storage_gb": 50}
            }
        },
        {
            "tenant_name": "client_abc",
            "domain": "abc.example.com",
            "schema_name": "client_abc_schema",
            "description": "ABC Corporation tenant",
            "settings": {
                "features": ["analytics", "reporting", "advanced_security"],
                "limits": {"users": 500, "storage_gb": 200}
            }
        }
    ]
    
    result = await service.provision_batch(tenant_data)
    
    if result['success']:
        print(f"Successfully provisioned {result['summary']['successful']} tenants")
        for tenant_result in result['results']:
            print(f"Tenant: {tenant_result['tenant_name']}, API Key: {tenant_result['api_key']}")
    else:
        print(f"Batch provisioning failed. {result['summary']['failed']} tenants failed.")

# Run the provisioning
asyncio.run(provision_demo_tenants())
```

### 🔍 **Monitoring and Health Checks**

```python
# Example: Monitor tenant health
async def check_tenant_health():
    service = BatchTenantService(db_session, tenant_manager, migration_manager)
    
    # Get all active tenants
    tenants = await db_session.query(TenantRegistry).filter(
        TenantRegistry.is_active == True
    ).all()
    
    health_report = []
    
    for tenant in tenants:
        try:
            # Check schema structure
            schema_valid = await service._validate_schema_structure(tenant.schema_name)
            
            # Check database connectivity
            db_accessible = await service._test_tenant_database_access(tenant.schema_name)
            
            health_report.append({
                'tenant_id': tenant.id,
                'tenant_name': tenant.tenant_name,
                'schema_name': tenant.schema_name,
                'schema_valid': schema_valid,
                'db_accessible': db_accessible,
                'overall_health': 'healthy' if schema_valid and db_accessible else 'unhealthy'
            })
            
        except Exception as e:
            health_report.append({
                'tenant_id': tenant.id,
                'tenant_name': tenant.tenant_name,
                'schema_name': tenant.schema_name,
                'error': str(e),
                'overall_health': 'error'
            })
    
    return health_report
```

## Integration with Dual Migration System

The batch tenant provisioning system integrates seamlessly with the [Dual Migration System](./DUAL_MIGRATION_SYSTEM.md):

```python
# Example integration in BatchTenantService
class BatchTenantService:
    async def provision_tenant_schema(self, tenant_data: dict) -> bool:
        """Provision database schema for a new tenant."""
        try:
            schema_name = tenant_data['schema_name']
            
            # Run tenant migrations
            result = subprocess.run([
                'python', 'app/database/migrations/migrate.py',
                'init-tenant', '--schema', schema_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Schema {schema_name} provisioned successfully")
                return True
            else:
                logger.error(f"Schema provisioning failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error provisioning schema: {e}")
            return False
```

## Best Practices

### ✅ **Do's**

1. **Always validate input data** before processing
2. **Use transaction rollbacks** for failed operations
3. **Implement proper logging** for audit trails
4. **Test batch operations** with representative data
5. **Monitor performance metrics** and optimize accordingly
6. **Use secure API key generation** with proper entropy
7. **Implement rate limiting** for API endpoints

### ❌ **Don'ts**

1. **Don't skip input validation** - always sanitize data
2. **Don't ignore rollback procedures** - clean up failed operations
3. **Don't hardcode configuration** - use environment variables
4. **Don't process unlimited batch sizes** - implement reasonable limits
5. **Don't expose sensitive data** in logs or responses

## Security Considerations

### 🔒 **Security Best Practices**

1. **API Key Security**
   - Generate cryptographically secure API keys
   - Store hashed versions in database
   - Implement key rotation mechanisms
   - Use rate limiting for API endpoints

2. **Input Validation**
   - Sanitize all input data
   - Validate against SQL injection
   - Enforce naming conventions
   - Check for malicious patterns

3. **Schema Isolation**
   - Ensure complete data separation
   - Implement proper database permissions
   - Use schema-specific database users
   - Regular security audits

4. **Audit Logging**
   ```python
   class SecurityAuditLogger:
       def log_tenant_creation(self, tenant_data: dict, user_id: str, ip_address: str):
           audit_entry = {
               'event': 'tenant_created',
               'tenant_name': tenant_data['tenant_name'],
               'user_id': user_id,
               'ip_address': ip_address,
               'timestamp': datetime.utcnow(),
               'details': tenant_data
           }
           self.write_audit_log(audit_entry)
   ```

## Performance Optimization

### 📈 **Optimization Strategies**

1. **Parallel Processing**
   ```python
   import asyncio
   
   async def provision_batch_parallel(self, tenant_data_list: List[dict]) -> dict:
       """Provision tenants in parallel for better performance."""
       semaphore = asyncio.Semaphore(5)  # Limit concurrent operations
       
       async def provision_with_semaphore(tenant_data):
           async with semaphore:
               return await self._provision_single_tenant(tenant_data)
       
       tasks = [provision_with_semaphore(data) for data in tenant_data_list]
       results = await asyncio.gather(*tasks, return_exceptions=True)
       
       return self._process_batch_results(results)
   ```

2. **Connection Pooling**
   ```python
   # Optimize database connections
   engine = create_async_engine(
       database_url,
       pool_size=20,
       max_overflow=30,
       pool_timeout=30,
       pool_recycle=3600
   )
   ```

3. **Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def _check_domain_exists(self, domain: str) -> bool:
       """Cache domain existence checks."""
       return self.db.query(TenantRegistry).filter(
           TenantRegistry.domain == domain
       ).first() is not None
   ```

## Troubleshooting

### 🐛 **Common Issues**

#### 1. **Schema Creation Failures**
```bash
# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-13-main.log

# Verify database permissions
psql -U postgres -d vecapp -c "\du"

# Check schema existence
psql -U postgres -d vecapp -c "SELECT schema_name FROM information_schema.schemata;"
```

#### 2. **Migration Failures**
```bash
# Check migration status
python app/database/migrations/migrate.py status --schema problematic_schema

# Manual migration rollback
python app/database/migrations/migrate.py downgrade --schema problematic_schema

# Re-run migrations
python app/database/migrations/migrate.py upgrade-tenant --schema problematic_schema
```

#### 3. **API Key Conflicts**
```python
# Check for duplicate API keys
SELECT api_key, COUNT(*) 
FROM tenant_registry 
GROUP BY api_key 
HAVING COUNT(*) > 1;

# Regenerate API keys if needed
UPDATE tenant_registry 
SET api_key = 'new_unique_key' 
WHERE id = problematic_tenant_id;
```

## Future Enhancements

### 🚀 **Planned Features**

1. **Advanced Batch Operations**
   - Tenant template system
   - Bulk tenant updates
   - Scheduled provisioning
   - Tenant cloning capabilities

2. **Enhanced Monitoring**
   - Real-time provisioning dashboard
   - Performance analytics
   - Resource usage tracking
   - Automated health checks

3. **Integration Improvements**
   - Webhook notifications
   - External system integrations
   - API versioning
   - GraphQL support

4. **Operational Features**
   - Tenant backup/restore
   - Data migration tools
   - Compliance reporting
   - Cost tracking

---

## Summary

The Batch Tenant Provisioning System provides a robust, scalable solution for multi-tenant SaaS applications with:

- **Automated Provisioning**: Streamlined tenant creation with minimal manual intervention
- **Strong Isolation**: Complete data separation between tenants
- **Comprehensive Validation**: Thorough input validation and error handling
- **Performance Optimization**: Parallel processing and efficient resource utilization
- **Security Focus**: Secure API key generation and audit logging
- **Integration Ready**: Seamless integration with the dual migration system

This system enables rapid tenant onboarding while maintaining the highest standards of security, performance, and reliability required for enterprise SaaS applications.