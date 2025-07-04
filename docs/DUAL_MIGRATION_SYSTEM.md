# Dual Migration System Documentation

## Overview

The VecApp AI project implements a sophisticated **dual migration system** that separates database schema management into two independent tracks:

1. **Public Schema Migrations** - Global infrastructure and tenant registry
2. **Tenant Schema Migrations** - Tenant-specific data tables and structures

This architecture provides strong data isolation, scalable tenant provisioning, and independent schema evolution for multi-tenant SaaS applications.

## Architecture

### 🏗️ **System Components**

```
app/database/migrations/
├── migrate.py              # Central migration management CLI
├── public/                 # Public schema migrations
│   ├── alembic.ini        # Public Alembic configuration
│   └── alembic/
│       ├── env.py         # Public migration environment
│       └── versions/      # Public migration files
└── tenant/                # Tenant schema migrations
    ├── alembic.ini        # Tenant Alembic configuration
    └── alembic/
        ├── env.py         # Tenant migration environment
        └── versions/      # Tenant migration files
```

### 🔄 **Migration Flow**

```mermaid
graph TD
    A[Application Deployment] --> B[Run Public Migrations]
    B --> C[Create tenant_registry Table]
    C --> D[Tenant Provisioning Request]
    D --> E[Create Tenant Schema]
    E --> F[Run Tenant Migrations]
    F --> G[Tenant Ready]
    
    H[New Public Migration] --> I[Update All Environments]
    J[New Tenant Migration] --> K[Update Specific Tenant]
```

## Migration Types

### 📊 **Public Schema Migrations**

**Purpose**: Manage global application infrastructure

**Contains**:
- `tenant_registry` table - Central tenant metadata
- Global configuration tables
- Cross-tenant reference data
- Application-level schema changes

**Location**: `/app/database/migrations/public/`

**Example Migration**:
```python
# 20250102_000000_create_tenant_registry.py
def upgrade():
    op.create_table('tenant_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('schema_name', sa.String(63), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
        sa.UniqueConstraint('schema_name'),
        sa.UniqueConstraint('api_key')
    )
```

### 🏢 **Tenant Schema Migrations**

**Purpose**: Manage tenant-specific data structures

**Contains**:
- Tenant business data tables
- Tenant-specific configurations
- User data and relationships
- Tenant feature customizations

**Location**: `/app/database/migrations/tenant/`

**Example Migration**:
```python
# 20250102_000001_create_tenant_schema_tables.py
def upgrade():
    # Create tenant table
    op.create_table('tenant',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('settings', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create person table
    op.create_table('person',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(20)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'])
    )
```

## Usage Guide

### 🚀 **Initial Setup**

#### 1. Initialize Public Schema (Run Once)
```bash
# Navigate to project root
cd /path/to/vecapp-ai-refactor_base

# Initialize public schema with tenant registry
python app/database/migrations/migrate.py init-public
```

#### 2. Verify Public Schema
```bash
# Check public schema status
python app/database/migrations/migrate.py status-public
```

### 🏢 **Tenant Provisioning**

#### 1. Create New Tenant Schema
```bash
# Initialize tenant schema for 'demo' tenant
python app/database/migrations/migrate.py init-tenant --schema demo

# Initialize tenant schema for 'client_abc' tenant
python app/database/migrations/migrate.py init-tenant --schema client_abc
```

#### 2. Verify Tenant Schema
```bash
# Check specific tenant status
python app/database/migrations/migrate.py status --schema demo
```

### 🔄 **Ongoing Operations**

#### Apply New Public Migrations
```bash
# Apply new public schema changes
python app/database/migrations/migrate.py upgrade-public
```

#### Apply New Tenant Migrations
```bash
# Apply to specific tenant
python app/database/migrations/migrate.py upgrade-tenant --schema demo

# Apply to multiple tenants (manual process)
python app/database/migrations/migrate.py upgrade-tenant --schema client_abc
python app/database/migrations/migrate.py upgrade-tenant --schema client_xyz
```

## CLI Reference

### 📋 **Available Commands**

| Command | Description | Example |
|---------|-------------|----------|
| `init-public` | Initialize public schema | `python migrate.py init-public` |
| `upgrade-public` | Apply public migrations | `python migrate.py upgrade-public` |
| `status-public` | Check public schema status | `python migrate.py status-public` |
| `init-tenant` | Initialize tenant schema | `python migrate.py init-tenant --schema demo` |
| `upgrade-tenant` | Apply tenant migrations | `python migrate.py upgrade-tenant --schema demo` |
| `status` | Check tenant schema status | `python migrate.py status --schema demo` |

### 🛠️ **Migration Script Features**

```python
class MigrationManager:
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        self.public_dir = self.migrations_dir / "public"
        self.tenant_dir = self.migrations_dir / "tenant"
        
    def run_alembic_command(self, config_path: Path, command: list, env_vars: dict = None):
        """Execute Alembic commands with proper environment setup."""
        
    def init_public(self):
        """Initialize public schema migrations."""
        
    def init_tenant(self, schema_name: str):
        """Initialize tenant schema migrations with TENANT_SCHEMA env var."""
```

## Configuration

### 🔧 **Public Schema Configuration**

**File**: `/app/database/migrations/public/alembic.ini`

```ini
[alembic]
script_location = public/alembic
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

**Environment**: `/app/database/migrations/public/alembic/env.py`

```python
# Key features:
# - Targets public schema only
# - Uses TenantRegistry metadata
# - Configures for public schema operations

target_metadata = MetaData()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

### 🏢 **Tenant Schema Configuration**

**File**: `/app/database/migrations/tenant/alembic.ini`

```ini
[alembic]
script_location = tenant/alembic
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic
```

**Environment**: `/app/database/migrations/tenant/alembic/env.py`

```python
# Key features:
# - Uses TENANT_SCHEMA environment variable
# - Creates schema if not exists
# - Sets search_path to tenant schema
# - Imports tenant-specific models

def run_migrations_online():
    tenant_schema = os.environ.get("TENANT_SCHEMA")
    if not tenant_schema:
        raise ValueError("TENANT_SCHEMA environment variable is required")
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        # Create schema if it doesn't exist
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant_schema}"))
        
        # Set search path to tenant schema
        connection.execute(text(f"SET search_path TO {tenant_schema}"))
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=tenant_schema
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

## Best Practices

### ✅ **Do's**

1. **Always run public migrations first** before tenant provisioning
2. **Use descriptive migration names** with timestamps
3. **Test migrations on development tenants** before production
4. **Keep public and tenant migrations separate** - never mix concerns
5. **Use the CLI script** instead of running Alembic directly
6. **Document breaking changes** in migration comments
7. **Backup databases** before running migrations in production

### ❌ **Don'ts**

1. **Don't run tenant migrations without specifying --schema**
2. **Don't modify public schema from tenant migrations**
3. **Don't hardcode tenant names** in migration scripts
4. **Don't skip migration testing** on representative data
5. **Don't run migrations directly with Alembic** - use the CLI wrapper

### 🔒 **Security Considerations**

1. **Schema Isolation**: Each tenant's data is completely isolated
2. **Permission Management**: Ensure proper database user permissions
3. **API Key Security**: Tenant API keys are stored securely in tenant_registry
4. **Audit Trail**: All migration operations are logged

## Troubleshooting

### 🐛 **Common Issues**

#### 1. **"TENANT_SCHEMA environment variable is required"**
```bash
# Solution: Always specify --schema for tenant operations
python migrate.py init-tenant --schema your_tenant_name
```

#### 2. **"ModuleNotFoundError: No module named 'app'"**
```bash
# Solution: Run from project root directory
cd /path/to/vecapp-ai-refactor_base
python app/database/migrations/migrate.py [command]
```

#### 3. **"Schema already exists"**
```bash
# Solution: Check if tenant is already initialized
python migrate.py status --schema your_tenant_name
```

#### 4. **Database Connection Issues**
```bash
# Solution: Verify DATABASE_URL environment variable
echo $DATABASE_URL

# Or check docker-compose database service
docker-compose ps postgres
```

### 🔍 **Debugging**

#### Enable Verbose Logging
```python
# Add to migration environment files
import logging
logging.getLogger('alembic').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Check Migration History
```bash
# Public schema history
python migrate.py status-public

# Tenant schema history
python migrate.py status --schema tenant_name
```

#### Manual Schema Inspection
```sql
-- Check existing schemas
SELECT schema_name FROM information_schema.schemata;

-- Check tables in specific schema
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'your_schema_name';

-- Check alembic version
SELECT * FROM public.alembic_version;
SELECT * FROM your_schema.alembic_version;
```

## Integration with Batch Tenant Provisioning

The dual migration system integrates seamlessly with the [Batch Tenant Provisioning System](./BATCH_TENANT_PROVISIONING.md):

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

## Performance Considerations

### 📈 **Optimization Strategies**

1. **Connection Pooling**: Use appropriate pool sizes for migration operations
2. **Parallel Migrations**: Tenant migrations can run in parallel for different tenants
3. **Batch Operations**: Group multiple schema operations when possible
4. **Index Management**: Create indexes after bulk data operations
5. **Transaction Scope**: Keep migration transactions as short as possible

### 📊 **Monitoring**

```python
# Example monitoring integration
import time
import logging

class MigrationManager:
    def run_alembic_command(self, config_path: Path, command: list, env_vars: dict = None):
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, cwd=self.migrations_dir, env=env, 
                                  capture_output=True, text=True)
            
            duration = time.time() - start_time
            logging.info(f"Migration completed in {duration:.2f}s: {' '.join(command)}")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"Migration failed after {duration:.2f}s: {e}")
            raise
```

## Future Enhancements

### 🚀 **Planned Features**

1. **Automated Tenant Migration**: Batch apply migrations to all tenants
2. **Migration Rollback**: Safe rollback procedures for tenant schemas
3. **Schema Versioning**: Track and manage different schema versions per tenant
4. **Migration Validation**: Pre-flight checks before applying migrations
5. **Performance Metrics**: Built-in timing and resource usage tracking

### 🔮 **Advanced Scenarios**

1. **Blue-Green Deployments**: Support for zero-downtime schema updates
2. **Cross-Tenant Migrations**: Safely migrate data between tenant schemas
3. **Schema Templates**: Predefined schema configurations for different tenant types
4. **Automated Testing**: Integration with CI/CD for migration testing

---

## Summary

The dual migration system provides a robust foundation for multi-tenant applications with:

- **Strong Data Isolation**: Complete separation between tenants
- **Scalable Architecture**: Independent schema management
- **Operational Simplicity**: Single CLI for all migration operations
- **Production Ready**: Battle-tested patterns and error handling
- **Integration Friendly**: Works seamlessly with batch provisioning

This architecture supports the complex requirements of modern SaaS applications while maintaining simplicity and reliability in database operations.