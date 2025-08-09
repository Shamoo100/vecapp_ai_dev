"""
FastAPI Database Dependencies

Clean dependency injection patterns for database connections.
Provides a proper hierarchy of database dependencies to avoid exposing
unnecessary parameters in OpenAPI documentation.

This module establishes clear separation between:
- Public schema operations (tenant provisioning, system-wide operations)
- Tenant-specific operations (requires schema_name)
- Person-specific operations (requires schema_name + person_id)
- Custom operations (flexible but exposes all parameters)
"""

from typing import Optional, AsyncGenerator
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.connection import DatabaseConnection


# === PUBLIC SCHEMA DEPENDENCIES ===

async def get_public_db(
    db_name: str = DatabaseConnection.DEFAULT_DB
) -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for public schema operations.
    
    Use this for:
    - Tenant provisioning
    - System-wide operations
    - Health checks
    - Operations that don't require tenant context
    
    Args:
        db_name: Database identifier (defaults to main database)
        
    Yields:
        SQLAlchemy session connected to public schema
    """
    async with DatabaseConnection.get_session(
        schema_name="public",
        tenant_id=None,
        person_id=None,
        db_name=db_name
    ) as session:
        yield session


# === TENANT-SPECIFIC DEPENDENCIES ===

async def get_tenant_db(
    schema_name: str,
    tenant_id: Optional[int] = None,
    db_name: str = DatabaseConnection.DEFAULT_DB
) -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for tenant-specific operations.
    
    Use this for:
    - Tenant-scoped data operations
    - Multi-tenant application logic
    - Operations that require tenant context but not person context
    
    Args:
        schema_name: REQUIRED tenant schema name
        tenant_id: Optional tenant registry ID for additional context
        db_name: Database identifier (defaults to main database)
        
    Yields:
        SQLAlchemy session connected to specified tenant schema
    """
    async with DatabaseConnection.get_session(
        schema_name=schema_name,
        tenant_id=tenant_id,
        person_id=None,
        db_name=db_name
    ) as session:
        yield session


# === PERSON-SPECIFIC DEPENDENCIES ===

async def get_person_db(
    schema_name: str,
    person_id: UUID,
    tenant_id: Optional[int] = None,
    db_name: str = DatabaseConnection.DEFAULT_DB
) -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for person-specific operations.
    
    Use this for:
    - Person-scoped data operations
    - User-specific functionality
    - Operations that require both tenant and person context
    
    Args:
        schema_name: REQUIRED tenant schema name
        person_id: REQUIRED person UUID
        tenant_id: Optional tenant registry ID for additional context
        db_name: Database identifier (defaults to main database)
        
    Yields:
        SQLAlchemy session connected to specified tenant schema with person context
    """
    async with DatabaseConnection.get_session(
        schema_name=schema_name,
        tenant_id=tenant_id,
        person_id=person_id,
        db_name=db_name
    ) as session:
        yield session


# === CUSTOM/FLEXIBLE DEPENDENCIES ===

async def get_custom_db(
    schema_name: str,
    tenant_id: Optional[int] = None,
    person_id: Optional[UUID] = None,
    db_name: str = DatabaseConnection.DEFAULT_DB
) -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for custom operations with full parameter control.
    
    ⚠️  WARNING: This dependency exposes all parameters in OpenAPI documentation.
    Only use this when you need the flexibility and understand the API documentation impact.
    
    Use this for:
    - Complex operations requiring flexible parameter combinations
    - Legacy endpoints during migration
    - Special cases where other dependencies don't fit
    
    Args:
        schema_name: REQUIRED schema name for multi-tenant operations
        tenant_id: Optional tenant registry ID for additional context
        person_id: Optional person UUID for person-specific operations
        db_name: Database identifier (defaults to main database)
        
    Yields:
        SQLAlchemy session with full parameter flexibility
    """
    async with DatabaseConnection.get_session(
        schema_name=schema_name,
        tenant_id=tenant_id,
        person_id=person_id,
        db_name=db_name
    ) as session:
        yield session


# === FASTAPI DEPENDENCY OBJECTS ===

# Public schema dependencies (clean API documentation)
PublicDB = Depends(get_public_db)

# Tenant-specific dependencies (exposes schema_name + tenant_id)
TenantDB = Depends(get_tenant_db)

# Person-specific dependencies (exposes schema_name + person_id + tenant_id)
PersonDB = Depends(get_person_db)

# Custom dependencies (exposes all parameters - use sparingly)
CustomDB = Depends(get_custom_db)


# === BACKWARD COMPATIBILITY ALIASES ===

# Legacy aliases for gradual migration
get_db_dependency = get_custom_db  # Original function with all parameters
get_db = get_public_db  # Simple database access
get_db_session = get_custom_db  # Session-based access

# Legacy dependency objects
Database = CustomDB  # Full compatibility
DB = PublicDB  # Simple access


# === EXPORTS ===

__all__ = [
    # Dependency functions
    "get_public_db",
    "get_tenant_db", 
    "get_person_db",
    "get_custom_db",
    
    # FastAPI dependency objects
    "PublicDB",
    "TenantDB",
    "PersonDB", 
    "CustomDB",
    
    # Backward compatibility
    "get_db_dependency",
    "get_db",
    "get_db_session",
    "Database",
    "DB"
]