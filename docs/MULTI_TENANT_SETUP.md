# Multi-Tenant Schema Provisioning System

This document describes the multi-tenant database schema provisioning system implemented for the VecApp AI application.

## Overview

The system provides API-driven schema provisioning and migration management for multiple tenants, where each tenant gets their own isolated database schema. This approach ensures data isolation while maintaining a single application codebase.

## Architecture

### Schema-Based Multi-Tenancy
- Each tenant has their own PostgreSQL schema (e.g., `tenant_demo`, `tenant_church1`)
- The `public` schema contains shared/system tables
- Each tenant schema contains isolated tenant-specific data

### Per-Tenant Migration Versioning
- Each tenant schema maintains its own `alembic_version` table
- Tenants can be at different migration versions
- Independent upgrade/downgrade capabilities per tenant

## Database Schema

### Tenant Model Fields

The `Tenant` model includes the following schema management fields:

```python
# Schema Management
schema_name = Column(String(255))           # Database schema name
schema_provisioned = Column(Boolean)        # Whether schema is created
migrations_applied = Column(Boolean)        # Whether migrations are applied
api_key = Column(String(255))              # Tenant API key
```

## API Endpoints

### 1. Create Tenant with Schema Provisioning

**POST** `/api/tenants/`

Create a new tenant with optional automatic schema provisioning and migrations.

```json
{
  "tenant_name": "Demo Church",
  "domain": "demo-church",
  "email": "admin@demo-church.com",
  "tenant_type": "church",
  "provision_schema": true,
  "run_migrations": true
}
```

**Response:**
```json
{
  "tenant": {
    "id": "123",
    "tenant_name": "Demo Church",
    "schema_name": "demo-church",
    "schema_provisioned": true,
    "migrations_applied": true,
    ...
  },
  "schema_created": true,
  "migrations_applied": true,
  "migration_status": {
    "schema_provisioned": true,
    "migrations_applied": true,
    "current_revision": "3da2eb3bee79"
  },
  "message": "Tenant created successfully, schema provisioned, migrations applied"
}
```

### 2. Provision Schema for Existing Tenant

**POST** `/api/tenants/provision-schema`

```json
{
  "tenant_id": "123",
  "force_recreate": false
}
```

### 3. Run Migrations for Tenant

**POST** `/api/tenants/run-migrations`

```json
{
  "tenant_id": "123",
  "target_revision": "head",
  "force": false
}
```

### 4. Get Migration Status

**GET** `/api/tenants/{tenant_id}/migration-status`

**Response:**
```json
{
  "tenant_id": "123",
  "schema_name": "demo-church",
  "current_revision": "3da2eb3bee79",
  "pending_migrations": [],
  "schema_provisioned": true,
  "migrations_applied": true
}
```

## Usage Workflows

### Workflow 1: Full Automatic Setup

1. Create tenant with `provision_schema: true` and `run_migrations: true`
2. System automatically:
   - Creates tenant record
   - Creates database schema
   - Runs all migrations
   - Updates tenant status

### Workflow 2: Manual Step-by-Step Setup

1. Create tenant with `provision_schema: false`
2. Manually provision schema using `/provision-schema` endpoint
3. Manually run migrations using `/run-migrations` endpoint
4. Check status using `/migration-status` endpoint

### Workflow 3: Existing Tenant Migration

1. Use `/run-migrations` endpoint to upgrade existing tenant
2. Specify target revision or use "head" for latest
3. Monitor status with `/migration-status` endpoint

## Alembic Configuration

The system uses a modified Alembic configuration that supports per-tenant migrations:

### Running Migrations via Command Line

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations to specific tenant
alembic -x tenant=demo-church upgrade head

# Check current revision for tenant
alembic -x tenant=demo-church current

# Show migration history for tenant
alembic -x tenant=demo-church history
```

### Environment Variables

The Alembic `env.py` reads the tenant from the `-x tenant=<name>` parameter and:
- Sets the schema search path to the tenant schema
- Creates tenant-specific `alembic_version` table
- Applies migrations to the correct schema

## Testing

### Running the Test Script

```bash
# Make sure your FastAPI server is running
uvicorn app.main:app --reload

# Run the test script
python test_tenant_api.py
```

The test script demonstrates:
- Creating tenants with automatic provisioning
- Manual schema provisioning
- Running migrations
- Checking migration status

### Manual Testing with curl

```bash
# Create tenant with schema provisioning
curl -X POST "http://localhost:8000/api/tenants/" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Test Church",
    "domain": "test-church",
    "email": "admin@test.com",
    "provision_schema": true,
    "run_migrations": true
  }'

# Check migration status
curl "http://localhost:8000/api/tenants/1/migration-status"
```

## Database Setup

### Initial Setup

1. Ensure PostgreSQL is running
2. Create the main database
3. Run the initial migration to create the tenant table:

```bash
# Generate initial migration (if not exists)
alembic revision --autogenerate -m "initial_migration"

# Apply to public schema (creates tenant table)
alembic upgrade head
```

### Schema Verification

```sql
-- Check existing schemas
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');

-- Check tables in a tenant schema
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'demo-church';

-- Check migration version for a tenant
SELECT version_num FROM "demo-church".alembic_version;
```

## Security Considerations

1. **Schema Isolation**: Each tenant's data is isolated in separate schemas
2. **API Keys**: Each tenant gets a unique API key for authentication
3. **Input Validation**: Schema names are validated to prevent SQL injection
4. **Permission Control**: Database users should have appropriate schema-level permissions

## Monitoring and Maintenance

### Health Checks

- Monitor schema provisioning success rates
- Track migration failures and rollbacks
- Alert on schema creation errors

### Backup Strategy

- Schema-level backups for tenant data isolation
- Point-in-time recovery per tenant
- Migration rollback capabilities

### Performance Considerations

- Schema creation is a DDL operation (requires exclusive locks)
- Migration operations should be run during maintenance windows
- Consider connection pooling per schema for high-traffic tenants

## Troubleshooting

### Common Issues

1. **Schema Already Exists**: Use `force_recreate: true` to recreate
2. **Migration Failures**: Check Alembic logs and database permissions
3. **Connection Issues**: Verify database connectivity and schema permissions

### Debug Commands

```bash
# Check Alembic configuration
alembic check

# Show current migration status
alembic -x tenant=<schema_name> current

# Show migration history
alembic -x tenant=<schema_name> history --verbose
```

## Future Enhancements

1. **Tenant Data Migration**: Tools for moving data between schemas
2. **Schema Templates**: Pre-configured schema templates for different tenant types
3. **Automated Backups**: Per-tenant backup scheduling
4. **Migration Rollback**: API endpoints for migration rollbacks
5. **Bulk Operations**: Batch migration operations across multiple tenants
6. **Monitoring Dashboard**: Web interface for migration status monitoring