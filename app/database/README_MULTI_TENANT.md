# Multi-Tenant Schema Implementation

## Overview

This document describes the implementation of a multi-tenant architecture where each tenant has its own database schema. This approach provides strong data isolation between tenants while maintaining a single database instance.

## Key Components

### 1. Tenant Context Management

- `TenantContext` class in `app/database/tenant_context.py` provides utilities for working with tenant-specific schemas
- `tenant_context_var` in `app/security/tenant_context.py` stores the current tenant ID in a context variable
- `TenantContextMiddleware` extracts tenant ID from requests and sets it in the context

### 2. Database Connection Management

- `DatabaseConnection` class in `app/database/connection.py` provides methods for executing queries with tenant schema context
- All database operations automatically use the tenant schema based on the current tenant context
- Connection pooling is maintained for performance

### 3. Schema Creation and Management

- `TenantManager` in `app/database/tenant_management.py` handles creating new tenant schemas
- Each tenant gets its own schema named `tenant_{tenant_id}`
- Tables are created within the tenant's schema using Alembic migrations

### 4. Schema Migrations with Alembic

- Alembic is used to manage database schema changes across all tenant schemas
- Custom Alembic environment supports tenant-specific migrations
- `apply_tenant_migrations.py` script applies migrations to all tenant schemas

## Usage

### Setting Tenant Context

The tenant context is automatically set by the middleware based on:
1. The `X-Tenant-ID` header
2. The tenant ID in the URL path (e.g., `/tenants/{tenant_id}/...`)

### Database Operations

Use the `DatabaseConnection` class for database operations:

```python
from app.database.connection import DatabaseConnection

# The tenant context is automatically determined from the current request
async def get_user(user_id: str):
    return await DatabaseConnection.fetchrow(
        "SELECT * FROM users WHERE user_id = $1",
        user_id
    )

# Or explicitly specify a tenant ID
async def get_user_for_tenant(user_id: str, tenant_id: str):
    return await DatabaseConnection.fetchrow(
        "SELECT * FROM users WHERE user_id = $1",
        user_id,
        tenant_id=tenant_id
    )
```

### Creating a New Tenant

Use the `TenantManager` to create a new tenant:

```python
from app.database.tenant_management import TenantManager

async def create_new_tenant(tenant_data):
    tenant_manager = TenantManager(database)
    tenant_id = await tenant_manager.create_tenant(tenant_data)
    return tenant_id
```

## Security Considerations

1. Always validate tenant access - ensure users can only access their own tenant's data
2. Include tenant_id in tables as an additional security measure
3. Use the tenant context middleware to ensure proper isolation
4. Validate tenant IDs before using them in database operations

## Performance Considerations

1. Connection pooling is maintained for performance
2. Schema switching has minimal overhead
3. Indexes should be created within each tenant schema as needed
4. Consider using a read replica for heavy reporting queries

## Migration Considerations

When adding new tables or modifying existing ones:

1. Update the schema creation in `TenantManager._create_tenant_schema`
2. Create a migration script to update existing tenant schemas
3. Test thoroughly with multiple tenant schemas

## Conclusion

This multi-tenant schema approach provides strong data isolation with minimal overhead, allowing the application to scale to many tenants while maintaining security and performance.