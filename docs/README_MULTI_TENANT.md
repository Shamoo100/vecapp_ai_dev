# 📋 VecApp AI Tenant Service Documentation
## 🏗️ Overview: Multi-Tenant Architecture
The VecApp AI system uses a multi-tenant architecture where each organization (church, business, etc.) gets their own isolated database schema while sharing the same application infrastructure. This allows for:

- Data Isolation : Each tenant's data is completely separate
- Customization : Per-tenant configurations and features
- Scalability : Easy addition of new tenants
- Security : No cross-tenant data access
## 📁 File Roles & Responsibilities
### 🎯 Core Tenant Services 1. `tenant_service.py`
Role : Primary Tenant Management Service

- Purpose : Comprehensive tenant lifecycle management
- Key Functions :
  - CRUD Operations : Create, read, update, delete tenants
  - Schema Provisioning : Create isolated database schemas for tenants
  - Migration Management : Run Alembic migrations on tenant schemas
  - Super Admin Creation : Set up initial admin users for new tenants
  - Data Seeding : Insert initial configuration data 2. `multi_tenant_service.py`
Role : Enhanced Multi-Tenant Operations

- Purpose : Advanced tenant management with versioning support
- Key Functions :
  - Per-tenant versioning : Track schema versions per tenant
  - Advanced provisioning : More sophisticated schema management
  - Migration tracking : Detailed migration status monitoring
  - Schema validation : Ensure schema integrity 3. `batch_tenant_service.py`
Role : Scalable Batch Operations

- Purpose : Handle large-scale tenant operations efficiently
- Key Functions :
  - Batch Creation : Create multiple tenants simultaneously
  - Parallel Processing : Concurrent tenant provisioning
  - Bulk Updates : Update multiple tenants at once
  - Progress Tracking : Monitor batch operation status
  - Error Handling : Graceful failure management with retry logic
### 🔐 Authentication & Authorization Services 4. `auth_service.py`
Role : Tenant-Scoped Authentication

- Purpose : Handle user authentication within tenant contexts
- Key Functions :
  - User Management : Create/manage users within tenant schemas
  - Role Assignment : Assign roles and permissions
  - Authentication Workflows : Login/logout within tenant context
  - Permission Checking : Validate user permissions 5. `tenant_auth_seeder.py`
Role : Authentication Data Seeding

- Purpose : Set up initial authentication data for new tenants
- Key Functions :
  - User Type Seeding : Create default user roles (admin, member, etc.)
  - User Status Seeding : Set up user status types (active, inactive, etc.)
  - Permission Seeding : Initialize default permissions
  - Auth Configuration : Set up tenant-specific auth settings
### 🗄️ Data Layer 6. `tenant_registry.py`
Role : Central Tenant Registry Model

- Purpose : Database model for the central tenant registry (stored in public schema)
- Key Fields :
  - Basic Info : tenant_name , domain , tenant_type
  - Contact Info : email , phone , website
  - Location : tenant_address , tenant_city , tenant_state
  - Schema Management : schema_name , schema_provisioned , migrations_applied
  - Security : api_key for tenant identification 7. `tenant.py`
Role : API Data Models

- Purpose : Pydantic schemas for API request/response validation
- Key Schemas :
  - TenantCreate : For creating new tenants
  - TenantUpdate : For updating existing tenants
  - TenantInDB : Database representation
  - BatchTenantCreate : For batch operations
  - TenantProvisionResponse : Provisioning results
## 🔄 How They Work Together
### Tenant Creation Flow:
### Authentication Flow:
### Batch Operations Flow:
## 🎯 Key Concepts
### 1. Schema Isolation
- Each tenant gets a dedicated PostgreSQL schema (e.g., tenant_church_abc )
- All tenant data lives in their schema
- Public schema only contains the tenant registry
### 2. Provisioning States
- Not Provisioned : Tenant exists but no schema
- Schema Created : Schema exists but no migrations
- Fully Provisioned : Schema + migrations + initial data
### 3. API Key Management
- Each tenant gets a unique API key
- Used for service-to-service authentication
- Stored securely in the tenant registry
### 4. Migration Management
- Alembic migrations run per-tenant schema
- Each tenant can be on different migration versions
- Supports rollback and targeted migrations
## 🚀 Usage Examples
### Create a Single Tenant:
### Batch Create Tenants:
### Authenticate User in Tenant Context:
```
from app.services.external_auth_service import ExternalAuthService

# Initialize with tenant schema
auth_service = AuthService(db_session, 
"tenant_stmarys_church")

# Authenticate user within tenant
user = await auth_service.authenticate_user("user@stmarys.
church", "password")
```
## 🔧 Configuration & Settings
### Tenant Provisioning Config:
- max_concurrent_operations : Parallel processing limit
- operation_timeout_seconds : Timeout for operations
- retry_attempts : Number of retries on failure
- enable_rollback : Rollback on failure
### Schema Naming Convention:
- Format: tenant_{sanitized_domain}
- Example: stmarys.church → tenant_stmarys_church