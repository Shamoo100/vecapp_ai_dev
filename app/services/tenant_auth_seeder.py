"""
Tenant Authentication and User Data Seeder Service.
Handles seeding of authentication, user types, and user status data for tenant schemas.
"""
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
import logging

from app.database.models.tenant import Auth, UserType, UserStatus

logger = logging.getLogger(__name__)

class TenantAuthSeeder:
    """Service for seeding authentication and user-related data in tenant schemas."""
    
    def __init__(self, session: AsyncSession, tenant_schema: str):
        """
        Initialize the seeder with database session and tenant schema.
        
        Args:
            session: Async database session
            tenant_schema: Name of the tenant schema
        """
        self.session = session
        self.tenant_schema = tenant_schema
    
    async def seed_all_data(self, super_admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Seed all authentication and user-related data for a tenant.
        
        Args:
            super_admin_data: Dictionary containing super admin user data
            
        Returns:
            Dictionary with seeding results
        """
        results = {
            "user_types": [],
            "user_statuses": [],
            "super_admin": None,
            "errors": []
        }
        
        try:
            # Set schema search path
            await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
            
            # Seed lookup tables first
            results["user_types"] = await self._seed_user_types()
            results["user_statuses"] = await self._seed_user_statuses()
            
            # Create super admin user
            results["super_admin"] = await self._create_super_admin(super_admin_data)
            
            await self.session.commit()
            logger.info(f"Successfully seeded authentication data for tenant schema: {self.tenant_schema}")
            
        except Exception as e:
            await self.session.rollback()
            error_msg = f"Failed to seed authentication data for {self.tenant_schema}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            raise
        
        return results
    
    async def _seed_user_types(self) -> List[Dict[str, Any]]:
        """Seed user types lookup table."""
        user_types_data = [
            {"id": 1, "name": "member", "description": "Church member", "sort_order": 1},
            {"id": 2, "name": "regular_attendee", "description": "Regular church attendee", "sort_order": 2},
            {"id": 3, "name": "visitor", "description": "Church visitor", "sort_order": 3},
        ]
        
        created_types = []
        
        for type_data in user_types_data:
            try:
                # Check if user type already exists
                result = await self.session.execute(
                    select(UserType).where(UserType.name == type_data["name"])
                )
                existing_type = result.scalar_one_or_none()
                
                if not existing_type:
                    user_type = UserType(**type_data)
                    self.session.add(user_type)
                    await self.session.flush()  # Get the ID
                    created_types.append({
                        "id": user_type.id,
                        "name": user_type.name,
                        "description": user_type.description
                    })
                    logger.info(f"Created user type: {user_type.name}")
                else:
                    created_types.append({
                        "id": existing_type.id,
                        "name": existing_type.name,
                        "description": existing_type.description
                    })
                    logger.info(f"User type already exists: {existing_type.name}")
                    
            except IntegrityError as e:
                logger.warning(f"User type {type_data['name']} already exists: {e}")
                await self.session.rollback()
                continue
        
        return created_types
    
    async def _seed_user_statuses(self) -> List[Dict[str, Any]]:
        """Seed user statuses lookup table."""
        user_statuses_data = [
            {"id": 1, "name": "active", "description": "Active user", "sort_order": 1},
            {"id": 2, "name": "inactive", "description": "Inactive user", "sort_order": 2},
            {"id": 3, "name": "deceased", "description": "Deceased user", "sort_order": 3},
        ]
        
        created_statuses = []
        
        for status_data in user_statuses_data:
            try:
                # Check if user status already exists
                result = await self.session.execute(
                    select(UserStatus).where(UserStatus.name == status_data["name"])
                )
                existing_status = result.scalar_one_or_none()
                
                if not existing_status:
                    user_status = UserStatus(**status_data)
                    self.session.add(user_status)
                    await self.session.flush()  # Get the ID
                    created_statuses.append({
                        "id": user_status.id,
                        "name": user_status.name,
                        "description": user_status.description
                    })
                    logger.info(f"Created user status: {user_status.name}")
                else:
                    created_statuses.append({
                        "id": existing_status.id,
                        "name": existing_status.name,
                        "description": existing_status.description
                    })
                    logger.info(f"User status already exists: {existing_status.name}")
                    
            except IntegrityError as e:
                logger.warning(f"User status {status_data['name']} already exists: {e}")
                await self.session.rollback()
                continue
        
        return created_statuses
    
    async def _create_super_admin(self, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create super admin user for the tenant.
        
        Args:
            admin_data: Dictionary containing admin user data
            
        Returns:
            Dictionary with created admin user info
        """
        try:
            # Check if super admin already exists
            result = await self.session.execute(
                select(Auth).where(Auth.username == admin_data.get("username", "super_admin"))
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info(f"Super admin already exists: {existing_admin.username}")
                return {
                    "id": str(existing_admin.id),
                    "username": existing_admin.username,
                    "email": existing_admin.email,
                    "roles": existing_admin.roles,
                    "created": False
                }
            
            # Create new super admin
            super_admin = Auth(
                username=admin_data.get("username", "super_admin"),
                email=admin_data.get("email", "admin@tenant.local"),
                first_name=admin_data.get("first_name", "Super"),
                last_name=admin_data.get("last_name", "Admin"),
                roles=["super_admin"],
                permissions=[
                    "user_management",
                    "tenant_management", 
                    "system_administration",
                    "data_management",
                    "report_generation",
                    "ai_management"
                ],
                is_active=True,
                is_verified=True
            )
            
            # Set password
            super_admin.set_password(admin_data.get("password", "TempPassword123!"))
            
            self.session.add(super_admin)
            await self.session.flush()  # Get the ID
            
            logger.info(f"Created super admin user: {super_admin.username}")
            
            return {
                "id": str(super_admin.id),
                "username": super_admin.username,
                "email": super_admin.email,
                "roles": super_admin.roles,
                "permissions": super_admin.permissions,
                "created": True
            }
            
        except Exception as e:
            logger.error(f"Failed to create super admin: {str(e)}")
            raise
    
    async def get_user_type_by_name(self, name: str) -> Optional[UserType]:
        """Get user type by name."""
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        result = await self.session.execute(
            select(UserType).where(UserType.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_user_status_by_name(self, name: str) -> Optional[UserStatus]:
        """Get user status by name."""
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        result = await self.session.execute(
            select(UserStatus).where(UserStatus.name == name)
        )
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Auth]:
        """
        Authenticate a user by username and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            Auth object if authentication successful, None otherwise
        """
        await self.session.execute(text(f"SET search_path TO {self.tenant_schema}"))
        
        # Try to find user by username or email
        result = await self.session.execute(
            select(Auth).where(
                (Auth.username == username) | (Auth.email == username)
            )
        )
        user = result.scalar_one_or_none()
        
        if user and user.verify_password(password) and user.is_active:
            # Update last login
            user.last_login = text("NOW()")
            user.login_attempts = 0
            await self.session.commit()
            return user
        
        # Increment login attempts if user exists
        if user:
            user.login_attempts += 1
            await self.session.commit()
        
        return None