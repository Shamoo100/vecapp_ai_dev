"""
Authentication Repository Interface for AI Service
Defines the contract for AI service specific authentication data access operations.
"""
from typing import Protocol, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from app.api.schemas.auth_user import UserResponse, TenantContextResponse


class IAiAuthRepository(Protocol):
    """Interface for AI service authentication repository operations."""
    
    async def log_admin_action(
        self, 
        db: AsyncSession, 
        user: UserResponse, 
        tenant: TenantContextResponse,
        action: str, 
        details: Dict[str, Any]
    ) -> bool:
        """Log admin actions for audit purposes."""
        ...
    
    async def validate_user_tenant_access(
        self, 
        db: AsyncSession, 
        user_id: str, 
        tenant_id: str
    ) -> bool:
        """Validate that user has access to the specified tenant."""
        ...
    
    async def get_user_ai_permissions(
        self, 
        db: AsyncSession, 
        user_id: str, 
        tenant_schema: str
    ) -> List[str]:
        """Get AI service specific permissions for a user."""
        ...
    
    async def record_feedback_submission(
        self, 
        db: AsyncSession, 
        user: UserResponse, 
        tenant: TenantContextResponse,
        feedback_id: str,
        feedback_type: str
    ) -> bool:
        """Record feedback submission for tracking."""
        ...
    
    async def get_admin_activity_log(
        self, 
        db: AsyncSession, 
        tenant_schema: str,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get admin activity log for the tenant."""
        ...
    
    async def check_rate_limit(
        self, 
        db: AsyncSession, 
        user_id: str, 
        action: str,
        time_window_minutes: int = 60,
        max_attempts: int = 10
    ) -> bool:
        """Check if user has exceeded rate limits for specific actions."""
        ...