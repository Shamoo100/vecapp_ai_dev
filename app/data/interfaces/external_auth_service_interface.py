"""
Interface for External Auth Service operations.

This interface defines the contract for accessing authentication data from 
the external Auth Service database.
"""

from typing import Dict, Any, Optional, List, Protocol
from uuid import UUID


class IExternalAuthService(Protocol):
    """
    Interface for external auth service data access operations.
    
    This service handles cross-service database access to the Auth Service
    PostgreSQL database using schema-per-tenant approach.
    """
    
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        ...
    
    async def close(self) -> None:
        """Close the database connection pool."""
        ...
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user details by ID.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User data dictionary or None if not found
        """
        ...
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user details by email.
        
        Args:
            email: The user's email address
            
        Returns:
            User data dictionary or None if not found
        """
        ...
    
    async def validate_user_credentials(self, email: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """
        Validate user credentials.
        
        Args:
            email: User's email address
            password_hash: Hashed password for validation
            
        Returns:
            User data dictionary if valid, None otherwise
        """
        ...
    
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """
        Get user roles.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of role names
        """
        ...
    
    async def get_user_permissions(self, user_id: UUID) -> List[str]:
        """
        Get user permissions.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of permission names
        """
        ...
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in the auth system.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Created user data dictionary
        """
        ...
    
    async def update_user(self, user_id: UUID, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user information.
        
        Args:
            user_id: The user's unique identifier
            user_data: Dictionary containing updated user information
            
        Returns:
            Updated user data dictionary or None if not found
        """
        ...
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    async def get_tenant_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all users for the current tenant.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user data dictionaries
        """
        ...
    
    async def assign_role_to_user(self, user_id: UUID, role: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: The user's unique identifier
            role: Role name to assign
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    async def remove_role_from_user(self, user_id: UUID, role: str) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user_id: The user's unique identifier
            role: Role name to remove
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    async def get_session_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get session information by token.
        
        Args:
            token: Session token
            
        Returns:
            Session data dictionary or None if not found
        """
        ...
    
    async def create_session(self, user_id: UUID, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user session.
        
        Args:
            user_id: The user's unique identifier
            session_data: Session information
            
        Returns:
            Created session data dictionary
        """
        ...
    
    async def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a user session.
        
        Args:
            token: Session token to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        ...