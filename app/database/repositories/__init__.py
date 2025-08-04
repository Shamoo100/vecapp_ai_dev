"""
Database repositories package.

This package contains database connection management and dependency injection
patterns for the VecApp AI multi-tenant system.
"""

# Import key components for easy access
from .connection import DatabaseConnection, get_db_dependency
from .dependencies import (
    PublicDB,
    TenantDB, 
    PersonDB,
    CustomDB,
    get_public_db,
    get_tenant_db,
    get_person_db,
    get_custom_db
)

__all__ = [
    # Connection management
    "DatabaseConnection",
    "get_db_dependency",
    
    # Clean dependency objects
    "PublicDB",
    "TenantDB", 
    "PersonDB",
    "CustomDB",
    
    # Dependency functions
    "get_public_db",
    "get_tenant_db",
    "get_person_db", 
    "get_custom_db"
]