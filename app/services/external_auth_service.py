"""
External Auth Service - Business Logic Layer for External Auth Service Integration.

This service handles business logic for authentication operations,
orchestrating the external auth repository for database access.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime, timedelta
import bcrypt

from app.data.repositories.external_auth_repository import ExternalAuthRepository

logger = logging.getLogger(__name__)


class ExternalAuthService:
    """
    Service for handling external auth service business logic.
    
    This service provides business logic for authentication operations,
    user management, and role/permission handling.
    """
    
    def __init__(self, schema_name: str):
        """
        Initialize the external auth service with tenant schema.
        
        Args:
            schema_name: The tenant-specific schema name
        """
        self.schema_name = schema_name
        self.repository = ExternalAuthRepository(schema_name)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the external auth service and its dependencies."""
        if not self._initialized:
            await self.repository.initialize()
            self._initialized = True
            logger.info(f"External auth service initialized for schema: {self.schema_name}")
    
    async def close(self) -> None:
        """Close the external auth service and cleanup resources."""
        if self._initialized:
            await self.repository.close()
            self._initialized = False
            logger.info("External auth service closed")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User data dictionary if authentication successful, None otherwise
        """
        try:
            # Hash the password for comparison (Auth Service stores hashed passwords)
            password_hash = self._hash_password(password)
            
            # Validate credentials directly
            user = await self.repository.validate_user_credentials(email, password_hash)
            if not user:
                logger.warning(f"Authentication failed: Invalid credentials for {email}")
                return None
            
            # Check if user is active
            if not user.get('is_active', False):
                logger.warning(f"Authentication failed: User {email} is not active")
                return None
            
            logger.info(f"User {email} authenticated successfully")
            return user
            
        except Exception as e:
            logger.error(f"Error during authentication for {email}: {str(e)}")
            return None
    
    async def get_user_profile(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user profile information.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User profile data dictionary or None if not found
        """
        try:
            user = await self.repository.get_user_by_id(user_id)
            if user:
                # Remove sensitive data
                user_data = user.copy()
                user_data.pop('password_hash', None)
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error fetching user profile {user_id}: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            user = await self.repository.get_user_by_email(email)
            if user:
                # Remove sensitive data
                user_data = user.copy()
                user_data.pop('password_hash', None)
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {str(e)}")
            return None
    
    async def get_user_permissions(self, user_id: UUID) -> List[str]:
        """
        Get comprehensive user permissions including role-based permissions.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of permission strings
        """
        try:
            # Get direct permissions from repository
            direct_permissions = await self.repository.get_user_permissions(user_id)
            
            # Get role-based permissions
            user_roles = await self.repository.get_user_roles(user_id)
            
            permissions = set(direct_permissions)
            
            # Add role-based permissions
            for role in user_roles:
                role_permissions = self._get_role_permissions(role)
                permissions.update(role_permissions)
            
            return list(permissions)
            
        except Exception as e:
            logger.error(f"Error fetching user permissions {user_id}: {str(e)}")
            return []
    
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """
        Get user roles.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of role names
        """
        try:
            return await self.repository.get_user_roles(user_id)
        except Exception as e:
            logger.error(f"Error fetching user roles {user_id}: {str(e)}")
            return []
    
    async def validate_user_access(self, user_id: UUID, required_permission: str) -> bool:
        """
        Validate if user has required permission.
        
        Args:
            user_id: The user's unique identifier
            required_permission: Permission string to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            user_permissions = await self.get_user_permissions(user_id)
            return required_permission in user_permissions
        except Exception as e:
            logger.error(f"Error validating user access {user_id}: {str(e)}")
            return False
    
    async def get_tenant_users_summary(self) -> Dict[str, Any]:
        """
        Get summary of users in the tenant.
        
        Returns:
            Dictionary containing user statistics and summary
        """
        try:
            users = await self.repository.get_tenant_users(limit=1000)
            
            summary = {
                'total_users': len(users),
                'active_users': len([u for u in users if u.get('is_active', False)]),
                'verified_users': len([u for u in users if u.get('is_verified', False)]),
                'admin_users': len([u for u in users if 'admin' in u.get('roles', [])]),
                'recent_users': len([
                    u for u in users 
                    if u.get('created_at') and 
                    (datetime.utcnow() - u['created_at']).days <= 30
                ])
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting tenant users summary: {str(e)}")
            return {}
    
    async def get_all_tenant_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all users for the tenant.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user data dictionaries
        """
        try:
            users = await self.repository.get_tenant_users(limit)
            # Remove sensitive data from all users
            for user in users:
                user.pop('password_hash', None)
            return users
        except Exception as e:
            logger.error(f"Error fetching tenant users: {str(e)}")
            return []
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            password_hash: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password for storage.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """
        Get permissions associated with a role.
        
        Args:
            role: Role name
            
        Returns:
            List of permissions for the role
        """
        role_permissions = {
            'admin': [
                'ai_feedback_submit', 'ai_feedback_view',
                'ai_reports_generate', 'ai_reports_view',
                'manage_users', 'view_users'
            ],
            'super_admin': [
                'ai_feedback_submit', 'ai_feedback_view',
                'ai_reports_generate', 'ai_reports_view',
                'manage_users', 'view_users', 'manage_tenant'
            ],
            'member': [
                'ai_feedback_submit', 'ai_reports_view'
            ],
            'visitor': [
                'ai_feedback_submit'
            ],
            'pastor': [
                'ai_feedback_submit', 'ai_feedback_view',
                'ai_reports_generate', 'ai_reports_view',
                'view_users'
            ],
            'leader': [
                'ai_feedback_submit', 'ai_reports_view',
                'view_users'
            ]
        }
        
        return role_permissions.get(role, [])