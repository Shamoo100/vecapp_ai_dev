"""
AI Authentication Service - Business Logic Layer
Handles user management, role assignments, and authentication workflows for AI service.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
import logging

from app.api.schemas.auth_user import UserResponse, TenantContextResponse
from app.database.models.tenant.auth import Auth
from app.data.repositories.ai_auth_repository import AiAuthRepository

logger = logging.getLogger(__name__)

class AiAuthService:
    """Service for handling AI authentication business logic."""
    
    def __init__(self, session: AsyncSession, tenant_schema: str):
        """Initialize the AI auth service with database session and tenant schema."""
        self.session = session
        self.tenant_schema = tenant_schema
        self.auth_repository = AiAuthRepository()

    async def get_user(self, user_id: UUID) -> Optional[Auth]:
        """Get user by ID."""
        return await self.auth_repository.get_user_by_id(
            self.session, 
            str(user_id), 
            self.tenant_schema
        )
    
    async def add_role_to_user(self, user_id: UUID, role: str) -> bool:
        """Add a role to a user - Business Logic."""
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        
        result = await self.session.execute(select(Auth).where(Auth.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Business logic: Check if role is valid, user permissions, etc.
        if not await self._is_valid_role(role):
            raise ValueError(f"Invalid role: {role}")
        
        # Update roles
        current_roles = user.roles or []
        if role not in current_roles:
            user.roles = current_roles + [role]
            await self.session.commit()
        
        return True
    
    async def remove_role_from_user(self, user_id: UUID, role: str) -> bool:
        """Remove a role from a user - Business Logic."""
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        
        result = await self.session.execute(select(Auth).where(Auth.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Business logic: Check if user can remove this role
        if not await self._can_remove_role(user, role):
            raise ValueError(f"Cannot remove role: {role}")
        
        # Update roles
        if user.roles and role in user.roles:
            user.roles = [r for r in user.roles if r != role]
            await self.session.commit()
        
        return True
    
    async def add_permission_to_user(self, user_id: UUID, permission: str) -> bool:
        """Add a permission to a user - Business Logic."""
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        
        result = await self.session.execute(select(Auth).where(Auth.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Business logic: Validate permission, check user access level, etc.
        if not await self._is_valid_permission(permission):
            raise ValueError(f"Invalid permission: {permission}")
        
        # Update permissions
        current_permissions = user.permissions or []
        if permission not in current_permissions:
            user.permissions = current_permissions + [permission]
            await self.session.commit()
        
        return True
    
    async def remove_permission_from_user(self, user_id: UUID, permission: str) -> bool:
        """Remove a permission from a user - Business Logic."""
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        
        result = await self.session.execute(select(Auth).where(Auth.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Update permissions
        if user.permissions and permission in user.permissions:
            user.permissions = [p for p in user.permissions if p != permission]
            await self.session.commit()
        
        return True
    
    async def _is_valid_role(self, role: str) -> bool:
        """Business logic to validate if a role is valid."""
        valid_roles = ["admin", "super_admin", "member", "visitor", "staff"]
        return role in valid_roles
    
    async def _can_remove_role(self, user: Auth, role: str) -> bool:
        """Business logic to check if a role can be removed."""
        # Example: Don't allow removing the last admin role
        if role == "admin" and user.roles and user.roles.count("admin") == 1:
            # Check if this is the last admin in the tenant
            admin_count = await self._count_admins()
            return admin_count > 1
        return True
    
    async def _is_valid_permission(self, permission: str) -> bool:
        """Business logic to validate if a permission is valid."""
        valid_permissions = [
            "view_reports", "generate_reports", "manage_reports", "delete_reports",
            "manage_users", "view_users", "admin", "*",
            "ai_feedback_submit", "ai_feedback_view", "ai_reports_generate", "ai_reports_view"
        ]
        return permission in valid_permissions
    
    async def _count_admins(self) -> int:
        """Count total admins in the tenant."""
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        
        result = await self.session.execute(
            select(Auth).where(Auth.roles.op('?')('admin'))
        )
        admins = result.scalars().all()
        return len(admins)
    
    async def validate_admin_access_for_feedback(
        self, 
        user: UserResponse, 
        tenant: TenantContextResponse
    ) -> bool:
        """
        Validate that user has admin access for feedback operations.
        
        Args:
            user: Authenticated user from headers
            tenant: Tenant context from headers
            
        Returns:
            True if user has admin access, False otherwise
        """
        # Business logic: Check if user is admin for this tenant
        if "admin" not in user.roles and "super_admin" not in user.roles:
            logger.warning(f"User {user.id} attempted admin action without admin role")
            return False
        
        # Additional validation: Check if user exists in tenant and is active
        db_user = await self.get_user(user.id)
        if not db_user or not db_user.is_active:
            logger.warning(f"User {user.id} not found or inactive in tenant {tenant.id}")
            return False
        
        logger.info(f"Admin access validated for user {user.id} in tenant {tenant.id}")
        return True
    
    async def log_feedback_submission(
        self, 
        user: UserResponse, 
        tenant: TenantContextResponse,
        feedback_data: Dict[str, Any]
    ) -> None:
        """
        Log feedback submission for audit purposes.
        
        Args:
            user: User who submitted feedback
            tenant: Tenant context
            feedback_data: Feedback data submitted
        """
        # Use repository to log the action
        await self.auth_repository.log_admin_action(
            self.session,
            user,
            tenant,
            "feedback_submission",
            {
                "resource_type": "feedback",
                "resource_id": feedback_data.get("feedback_id"),
                "endpoint": "/feedback/submit",
                "http_method": "POST",
                **feedback_data
            }
        )
        
        logger.info(
            f"Feedback submitted by admin {user.id} ({user.email}) "
            f"for tenant {tenant.id} ({tenant.name})"
        )
    
    async def validate_user_context(
        self, 
        user: UserResponse, 
        tenant: TenantContextResponse
    ) -> bool:
        """
        Validate that user context is consistent and valid.
        
        Args:
            user: Authenticated user
            tenant: Tenant context
            
        Returns:
            True if context is valid, False otherwise
        """
        # Business logic validation
        if not user.id or not tenant.id:
            logger.error("Invalid user or tenant context - missing IDs")
            return False
        
        # Check if user has access to this tenant
        has_access = await self.auth_repository.validate_user_tenant_access(
            self.session, 
            str(user.id), 
            str(tenant.id)
        )
        
        if not has_access:
            logger.warning(f"User {user.id} does not have access to tenant {tenant.id}")
            return False
        
        return True
    
    async def get_user_permissions_for_ai_service(
        self, 
        user: UserResponse
    ) -> List[str]:
        """
        Get AI service specific permissions for user.
        
        Args:
            user: Authenticated user
            
        Returns:
            List of AI service permissions
        """
        return await self.auth_repository.get_user_ai_permissions(
            self.session,
            str(user.id),
            self.tenant_schema
        )
    
    def _is_valid_ai_permission(self, permission: str) -> bool:
        """Validate if permission is valid for AI service."""
        valid_ai_permissions = [
            "ai_feedback_submit",
            "ai_feedback_view", 
            "ai_reports_generate",
            "ai_reports_view"
        ]
        return permission in valid_ai_permissions