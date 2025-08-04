"""
Authentication and authorization module for VecApp AI Service.
Handles user and tenant context extraction from request headers.

This module provides authentication for the VecApp AI service, supporting:
- User authentication via X-auth-user headers (from central VecApp auth)
- Tenant context via X-request-tenant headers
- Service-to-service authentication for internal communication
- AI context for LangChain operations
"""
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.schemas.auth_user import (
    UserResponse, 
    TenantContextResponse, 
    AuthContextResponse
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthService:
    """
    Service for extracting authentication information from request headers.
    Handles both user and tenant context from central system.
    """
    
    @staticmethod
    def extract_user_from_request(request: Request) -> Optional[UserResponse]:
        """
        Extract user information from X-auth-user header.
        
        Args:
            request: FastAPI request object
            
        Returns:
            UserResponse object if user header is present and valid, None otherwise
        """
        user_header = request.headers.get("X-auth-user")
        if not user_header:
            return None
        
        try:
            user_data = json.loads(user_header)
            
            # Extract user ID (required)
            user_id = user_data.get("id")
            if not user_id:
                logger.warning("User header missing required 'id' field")
                return None
            
            # Extract roles (default to empty list if not present)
            roles = user_data.get("roles", [])
            if isinstance(roles, str):
                roles = [roles]  # Convert single role string to list
            
            # Extract tenant information for linking
            tenant_registry_id = user_data.get("tenant_registry_id")
            schema_name = user_data.get("schema_name")
            
            if not tenant_registry_id or not schema_name:
                logger.warning("User header missing tenant linking information")
                return None
            
            return UserResponse(
                id=UUID(user_id),
                username=user_data.get("username", ""),
                email=user_data.get("email", ""),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                roles=roles,
                is_active=user_data.get("is_active", True),
                tenant_registry_id=int(tenant_registry_id),
                schema_name=schema_name
            )
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse user header: {e}")
            return None
    
    @staticmethod
    def extract_tenant_from_request(request: Request) -> Optional[TenantContextResponse]:
        """
        Extract tenant information from X-request-tenant header.
        
        Args:
            request: FastAPI request object
            
        Returns:
            TenantContextResponse object if tenant header is present and valid, None otherwise
        """
        tenant_header = request.headers.get("X-request-tenant")
        if not tenant_header:
            return None
        
        try:
            # Handle both simple string (schema_name) and JSON formats
            if tenant_header.startswith('{'):
                # JSON format
                tenant_data = json.loads(tenant_header)
                tenant_id = tenant_data.get("id")
                name = tenant_data.get("name", tenant_data.get("tenant_name", ""))
                schema_name = tenant_data.get("schema_name", "")
                domain = tenant_data.get("domain", "")
                is_active = tenant_data.get("is_active", True)
            else:
                # Simple string format (just schema_name)
                schema_name = tenant_header.strip()
                # For simple format, we need to get other info from somewhere else
                # This might require a database lookup in a real implementation
                tenant_id = None  # Would need to be resolved
                name = schema_name.title()  # Simple fallback
                domain = f"{schema_name}.vecapp.com"  # Simple fallback
                is_active = True
            
            if not schema_name:
                logger.warning("Tenant header missing schema_name")
                return None
            
            # If tenant_id is missing, this might need a database lookup
            if tenant_id is None:
                logger.warning("Tenant header missing id - may need database lookup")
                # For now, we'll use a placeholder
                tenant_id = 0
            
            return TenantContextResponse(
                id=int(tenant_id),
                name=name,
                schema_name=schema_name,
                domain=domain,
                is_active=is_active
            )
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse tenant header: {e}")
            return None

class ServiceAuthService:
    """
    Service for handling service-to-service authentication.
    Manages JWT tokens for internal service communication.
    """
    
    def __init__(self, secret_key: str = "your-secret-key"):
        """
        Initialize service auth with secret key.
        
        Args:
            secret_key: Secret key for JWT token generation/validation
        """
        self.secret_key = secret_key
    
    def generate_service_token(self, service_name: str, tenant_id: Optional[int] = None) -> str:
        """
        Generate JWT token for service-to-service communication.
        
        Args:
            service_name: Name of the calling service
            tenant_id: Optional tenant ID for tenant-specific operations
            
        Returns:
            JWT token string
        """
        # Implementation would use PyJWT or similar
        # This is a placeholder implementation
        payload = {
            "service": service_name,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow().timestamp()
        }
        # In real implementation: return jwt.encode(payload, self.secret_key, algorithm="HS256")
        return f"service_token_{service_name}_{tenant_id}"
    
    def validate_service_token(self, token: str) -> dict:
        """
        Validate service JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        # Implementation would use PyJWT or similar
        # This is a placeholder implementation
        if not token.startswith("service_token_"):
            raise HTTPException(status_code=401, detail="Invalid service token")
        
        parts = token.split("_")
        if len(parts) < 3:
            raise HTTPException(status_code=401, detail="Malformed service token")
        
        return {
            "service": parts[2],
            "tenant_id": int(parts[3]) if parts[3] != "None" else None
        }

# === FASTAPI DEPENDENCIES ===

async def get_current_user(request: Request) -> Optional[UserResponse]:
    """
    Extract current user from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        UserResponse object if user is authenticated, None otherwise
    """
    return AuthService.extract_user_from_request(request)

async def get_current_tenant(request: Request) -> Optional[TenantContextResponse]:
    """
    Extract current tenant from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        TenantContextResponse object if tenant context is available, None otherwise
    """
    return AuthService.extract_tenant_from_request(request)

async def get_auth_context(request: Request) -> AuthContextResponse:
    """
    Get complete authentication context from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        AuthContextResponse with user and tenant information
    """
    user = await get_current_user(request)
    tenant = await get_current_tenant(request)
    
    return AuthContextResponse(
        authenticated=user is not None,
        user=user,
        tenant=tenant,
        timestamp=datetime.utcnow().isoformat()
    )

async def require_authentication(
    user: Optional[UserResponse] = Depends(get_current_user)
) -> UserResponse:
    """
    Require user authentication from headers.
    
    Args:
        user: Current user from headers
        
    Returns:
        UserResponse object for authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required - X-auth-user header missing or invalid"
        )
    return user

async def require_tenant_context(
    tenant: Optional[TenantContextResponse] = Depends(get_current_tenant)
) -> TenantContextResponse:
    """
    Require tenant context from headers.
    
    Args:
        tenant: Current tenant from headers
        
    Returns:
        TenantContextResponse object
        
    Raises:
        HTTPException: If tenant context is not available
    """
    if not tenant:
        raise HTTPException(
            status_code=400,
            detail="Tenant context required - X-request-tenant header missing or invalid"
        )
    return tenant

def require_role(required_role: str):
    """
    FastAPI dependency factory for role-based access control.
    
    Args:
        required_role: Role required to access the endpoint
        
    Returns:
        Dependency function that checks user role
    """
    async def check_role(user: UserResponse = Depends(require_authentication)) -> UserResponse:
        if required_role not in user.roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required"
            )
        return user
    
    return check_role

def require_permission(required_permission: str):
    """
    FastAPI dependency factory for permission-based access control.
    
    Args:
        required_permission: Permission required to access the endpoint
        
    Returns:
        Dependency function that checks user permission
    """
    async def check_permission(user: UserResponse = Depends(require_authentication)) -> UserResponse:
        # Note: UserResponse doesn't have permissions field in current schema
        # This would need to be implemented based on your permission system
        # For now, we'll check if user has admin role as a fallback
        if "super_admin" not in user.roles:
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{required_permission}' required"
            )
        return user
    
    return check_permission



