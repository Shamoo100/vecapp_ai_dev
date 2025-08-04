"""
AI Auth Repository for AI Service - Data Access Layer
Handles AI service specific authentication and audit operations using actual models.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, or_, insert, func
from uuid import UUID
from datetime import datetime, timedelta
import logging
import json

from app.api.schemas.auth_user import UserResponse, TenantContextResponse
from app.database.models.tenant.ai_audit_log import AIAuditLog
from app.database.models.tenant.feedback import AIFeedback
from app.database.models.tenant.auth import Auth
from app.database.models.public.ai_rate_limit_log import AIRateLimitLog


logger = logging.getLogger(__name__)


class AiAuthRepository:
    """Repository for AI service authentication-related database operations."""
    
    async def log_admin_action(
        self, 
        db: AsyncSession, 
        user: UserResponse, 
        tenant: TenantContextResponse,
        action: str, 
        details: Dict[str, Any]
    ) -> bool:
        """Log admin actions for audit purposes using AIAuditLog model."""
        try:
            await db.execute(text(f"SET search_path TO {tenant.schema_name}"))
            
            audit_log = AIAuditLog(
                user_id=user.id,
                user_email=user.email,
                tenant_id=tenant.id,
                action=action,
                resource_type=details.get("resource_type"),
                resource_id=details.get("resource_id"),
                endpoint=details.get("endpoint"),
                http_method=details.get("http_method"),
                ip_address=details.get("ip_address"),
                user_agent=details.get("user_agent"),
                details=details,
                success='true',
                duration_ms=details.get("duration_ms")
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(f"Admin action logged: {action} by {user.email} in tenant {tenant.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
            await db.rollback()
            return False
    
    async def get_user_by_id(
        self, 
        db: AsyncSession, 
        user_id: str, 
        tenant_schema: str
    ) -> Optional[Auth]:
        """Get user by ID from the tenant schema."""
        try:
            await db.execute(text(f"SET search_path TO {tenant_schema}"))
            
            result = await db.execute(
                select(Auth).where(Auth.id == UUID(user_id))
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    async def validate_user_tenant_access(
        self, 
        db: AsyncSession, 
        user_id: str, 
        tenant_id: str
    ) -> bool:
        """Validate user access by checking if user exists in tenant schema."""
        try:
            # For now, we'll use a simple approach - if user exists in tenant schema, they have access
            # This can be enhanced later with more sophisticated access control
            
            # Get tenant schema name from tenant_id (you might need to adjust this logic)
            tenant_schema = f"tenant_{tenant_id}"  # Adjust based on your schema naming
            
            user = await self.get_user_by_id(db, user_id, tenant_schema)
            return user is not None and user.is_active
            
        except Exception as e:
            logger.error(f"Failed to validate user tenant access: {e}")
            return False
    
    async def get_user_ai_permissions(
        self, 
        db: AsyncSession, 
        user_id: str, 
        tenant_schema: str
    ) -> List[str]:
        """Get AI service specific permissions for a user."""
        try:
            user = await self.get_user_by_id(db, user_id, tenant_schema)
            if not user:
                return []
            
            # Extract AI-related permissions
            ai_permissions = []
            user_permissions = user.permissions or []
            user_roles = user.roles or []
            
            # Map roles to AI permissions
            if any(role in ["admin", "super_admin"] for role in user_roles):
                ai_permissions.extend([
                    "ai_feedback_submit",
                    "ai_feedback_view",
                    "ai_reports_generate",
                    "ai_reports_view"
                ])
            
            # Add specific AI permissions
            for permission in user_permissions:
                if permission.startswith("ai_"):
                    ai_permissions.append(permission)
            
            return list(set(ai_permissions))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to get user AI permissions: {e}")
            return []
    
    async def record_feedback_submission(
        self, 
        db: AsyncSession, 
        user: UserResponse, 
        tenant: TenantContextResponse,
        feedback_id: str,
        feedback_type: str
    ) -> bool:
        """Record feedback submission using AIFeedback model."""
        try:
            await db.execute(text(f"SET search_path TO {tenant.schema_name}"))
            
            # Note: This assumes AIFeedback model has these fields
            # You might need to adjust based on actual model structure
            tracking_record = AIFeedback(
                entity_type=feedback_type,
                entity_id=feedback_id,
                admin_id=user.id,
                admin_email=user.email,
                submission_source='ai_service_admin'
            )
            
            db.add(tracking_record)
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to record feedback submission: {e}")
            await db.rollback()
            return False
    
    async def get_admin_activity_log(
        self, 
        db: AsyncSession, 
        tenant_schema: str,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get admin activity log for the tenant."""
        try:
            await db.execute(text(f"SET search_path TO {tenant_schema}"))
            
            query = select(AIAuditLog)
            
            # Add filters
            if user_id:
                query = query.where(AIAuditLog.user_id == UUID(user_id))
            if action_type:
                query = query.where(AIAuditLog.action == action_type)
            
            # Order by timestamp descending and limit
            query = query.order_by(AIAuditLog.timestamp.desc()).limit(limit)
            
            result = await db.execute(query)
            logs = result.scalars().all()
            
            # Convert to dict format
            return [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id),
                    "user_email": log.user_email,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "timestamp": log.timestamp.isoformat(),
                    "details": log.details,
                    "success": log.success,
                    "duration_ms": log.duration_ms
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get admin activity log: {e}")
            return []
    
    async def check_rate_limit(
        self, 
        db: AsyncSession, 
        user_id: str, 
        action: str,
        time_window_minutes: int = 60,
        max_attempts: int = 10
    ) -> bool:
        """Check if user has exceeded rate limits for specific actions."""
        try:
            # Use public schema for rate limiting
            await db.execute(text("SET search_path TO public"))
            
            # Calculate time window
            time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            # Count attempts in time window
            result = await db.execute(
                select(func.count(AIRateLimitLog.id))
                .where(
                    and_(
                        AIRateLimitLog.user_id == UUID(user_id),
                        AIRateLimitLog.action == action,
                        AIRateLimitLog.timestamp >= time_threshold
                    )
                )
            )
            
            attempt_count = result.scalar()
            
            # Log this attempt
            rate_limit_log = AIRateLimitLog(
                user_id=UUID(user_id),
                action=action,
                timestamp=datetime.utcnow()
            )
            db.add(rate_limit_log)
            await db.commit()
            
            # Return True if under limit, False if over limit
            return attempt_count < max_attempts
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # Allow action if rate limit check fails