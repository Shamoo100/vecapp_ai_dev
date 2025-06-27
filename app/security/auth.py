from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User:
    """
    User class representing an authenticated user.
    """
    
    def __init__(self, id: str, username: str, email: str, roles: List[str], permissions: Dict[str, List[str]]):
        """
        Initialize a user.
        
        Args:
            id: The user ID
            username: The username
            email: The user's email
            roles: List of roles assigned to the user
            permissions: Dictionary mapping tenant IDs to lists of permissions
        """
        self.id = id
        self.username = username
        self.email = email
        self.roles = roles
        self.permissions = permissions
    
    def has_permission(self, permission: str, tenant_id: str) -> bool:
        """
        Check if the user has a specific permission for a tenant.
        
        Args:
            permission: The permission to check
            tenant_id: The ID of the tenant to check permissions for
            
        Returns:
            True if the user has the permission, False otherwise
        """
        # Super admins have all permissions
        if "super_admin" in self.roles:
            return True
        
        # Check tenant-specific permissions
        tenant_permissions = self.permissions.get(tenant_id, [])
        if permission in tenant_permissions:
            return True
        
        # Check for wildcard permissions
        if "*" in tenant_permissions:
            return True
        
        # Check for permission groups
        if permission == "generate_reports" and "manage_reports" in tenant_permissions:
            return True
        if permission == "view_reports" and "manage_reports" in tenant_permissions:
            return True
        if permission == "delete_reports" and "manage_reports" in tenant_permissions:
            return True
        
        return False

# Global variable to store the current user in context
_current_user = None

def set_current_user(user: User):
    """Set the current user in the global context"""
    global _current_user
    _current_user = user

def get_current_user() -> Optional[User]:
    """Get the current user from the global context"""
    return _current_user

async def authenticate_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Authenticate a user based on their token.
    
    Args:
        token: The authentication token
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    # TODO: Implement actual token validation and user retrieval
    # This is a placeholder implementation
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create a dummy user for testing
    user = User(
        id="user123",
        username="testuser",
        email="test@example.com",
        roles=["admin"],
        permissions={
            "tenant123": ["manage_reports", "view_reports", "generate_reports", "delete_reports"]
        }
    )
    
    # Set the current user in the global context
    set_current_user(user)
    
    return user