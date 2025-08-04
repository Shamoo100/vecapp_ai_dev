"""
VecApp AI Security Module

This module provides a simplified header-based authentication system for VecApp AI:

Core Components:
- auth.py: Main authentication service with header-based User/Tenant extraction
- dependencies.py: FastAPI dependency shortcuts for common patterns  

Authentication Flow:
1. User authentication via X-auth-user headers (from central VecApp auth)
2. Tenant context via X-request-tenant headers
3. Combined user + tenant authentication for protected endpoints

Usage Examples:
    # Require authenticated user and tenant
    @router.post("/feedback")
    async def submit_feedback(
        auth: Tuple[UserResponse, TenantContextResponse] = Depends(UserAndTenant)
    ):
        user, tenant = auth
        return {"user_id": user.id, "tenant": tenant.schema_name}
    
    # Optional authentication
    @router.get("/public")
    async def public_route(user: Optional[UserResponse] = CurrentUserOptional):
        return {"authenticated": user is not None}
    
    # Require just user
    @router.get("/user-only")
    async def user_only(user: UserResponse = RequireUser):
        return {"user": user.username}
"""

from .auth import (
    AuthService,
    ServiceAuthService,
    get_current_user,
    get_current_tenant,
    require_authentication,
    require_tenant_context,
    get_auth_context,
    require_role,
    require_permission
)

from .dependencies import (
    CurrentUserOptional,
    CurrentTenantOptional,
    AuthContextDep,
    RequireUser,
    RequireTenant,
    UserAndTenant
)

__all__ = [
    # Core services
    "AuthService", 
    "ServiceAuthService",
    
    # Core dependencies
    "get_current_user",
    "get_current_tenant",
    "require_authentication",
    "require_tenant_context",
    "get_auth_context",
    "require_role",
    "require_permission",
    
    # Dependency shortcuts
    "CurrentUserOptional",
    "CurrentTenantOptional",
    "AuthContextDep",
    "RequireUser",
    "RequireTenant",
    
    # Convenience combinations
    "UserAndTenant"
]