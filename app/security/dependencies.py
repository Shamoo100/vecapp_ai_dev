"""
FastAPI Security Dependencies

Clean dependency injection patterns for header-based authentication.
All authentication logic is handled in auth.py - this module only provides
FastAPI dependency wrappers.
"""
from fastapi import Depends
from typing import Tuple

from ..api.schemas.auth_user import (
    UserResponse,
    TenantContextResponse,
    AuthContextResponse
)
from .auth import (
    get_current_user,
    get_current_tenant,
    get_auth_context,
    require_authentication,
    require_tenant_context
)

# === BASIC DEPENDENCIES ===

# Optional dependencies (can return None)
CurrentUserOptional = Depends(get_current_user)
CurrentTenantOptional = Depends(get_current_tenant)
AuthContextDep = Depends(get_auth_context)

# Required dependencies (raise HTTPException if missing)
RequireUser = Depends(require_authentication)
RequireTenant = Depends(require_tenant_context)

# === COMBINATION DEPENDENCIES ===

def UserAndTenant(
    user: UserResponse = Depends(require_authentication),
    tenant: TenantContextResponse = Depends(require_tenant_context)
) -> Tuple[UserResponse, TenantContextResponse]:
    """
    Dependency function that requires both authenticated user and tenant context.
    
    Args:
        user: Authenticated user from headers
        tenant: Tenant context from headers
    
    Returns:
        Tuple of (UserResponse, TenantContextResponse)
    """
    return user, tenant

# === EXPORTS ===

__all__ = [
    # Optional dependencies
    "CurrentUserOptional",
    "CurrentTenantOptional", 
    "AuthContextDep",
    
    # Required dependencies
    "RequireUser",
    "RequireTenant",
    
    # Combination dependencies
    "UserAndTenant"
]

