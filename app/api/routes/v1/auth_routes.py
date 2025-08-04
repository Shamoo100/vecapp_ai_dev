"""
Authentication API Routes for VecApp AI Service

This module provides JWT-based authentication endpoints for the AI service.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Optional
from app.api.schemas.auth_user import (
    UserResponse,
    TenantContextResponse,
    AuthContextResponse,
    ValidationRequest,
    ValidationResponse
)
from app.security.auth import (
    get_current_user,
    get_current_tenant,
    get_auth_context,
    require_authentication,
    require_tenant_context
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get(
    "/context",
    response_model=AuthContextResponse,
    summary="Get Authentication Context",
    description="Get current authentication context including user and tenant information"
)
async def get_auth_context_endpoint(
    context: AuthContextResponse = Depends(get_auth_context)
) -> AuthContextResponse:
    """Get the current authentication context."""
    return context

@router.get(
    "/user",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get information about the currently authenticated user"
)
async def get_current_user_info(
    user: UserResponse = Depends(require_authentication)
) -> UserResponse:
    """Get current user information."""
    return user

@router.get(
    "/tenant",
    response_model=TenantContextResponse,
    summary="Get Current Tenant",
    description="Get information about the current tenant context"
)
async def get_current_tenant_info(
    tenant: TenantContextResponse = Depends(require_tenant_context)
) -> TenantContextResponse:
    """Get current tenant information."""
    return tenant

@router.get(
    "/ai-context",
    response_model=AuthContextResponse,
    summary="Get AI Operation Context",
    description="Get context information for AI operations including user and tenant data"
)
async def get_ai_operation_context(
    context: AuthContextResponse = Depends(get_auth_context)
) -> AuthContextResponse:
    """Get AI operation context with user and tenant information."""
    return context

@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validate Authentication",
    description="Validate current authentication and check permissions/roles"
)
async def validate_authentication(
    validation: ValidationRequest,
    user: Optional[UserResponse] = Depends(get_current_user),
    tenant: Optional[TenantContextResponse] = Depends(get_current_tenant)
) -> ValidationResponse:
    """Validate authentication and check permissions/roles."""
    
    if not user:
        return ValidationResponse(
            valid=False,
            message="No authenticated user"
        )
    
    has_permission = True
    has_role = True
    
    # Check permission if specified
    if validation.required_permission:
        if not tenant:
            has_permission = False
        else:
            # Simple permission check based on roles
            has_permission = "super_admin" in user.roles
    
    # Check role if specified
    if validation.required_role:
        has_role = validation.required_role in user.roles
    
    is_valid = has_permission and has_role
    
    return ValidationResponse(
        valid=is_valid,
        user_id=user.id,
        tenant_registry_id=tenant.id if tenant else None,
        schema_name=tenant.schema_name if tenant else None,
        has_permission=has_permission,
        has_role=has_role,
        message="Valid authentication" if is_valid else "Authentication validation failed"
    )

@router.get(
    "/health",
    summary="Authentication Health Check",
    description="Health check endpoint for authentication service (no auth required)"
)
async def auth_health_check() -> Dict[str, str]:
    """Health check for authentication service."""
    return {
        "status": "healthy",
        "service": "vecapp-ai-auth",
        "authentication": "jwt-enabled"
    }