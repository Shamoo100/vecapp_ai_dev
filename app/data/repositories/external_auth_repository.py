"""
External Auth Repository implementation for cross-service database access.

This repository provides direct database access to the Auth Service 
PostgreSQL database using schema-per-tenant approach, mapping from
person, person_role, and person_permission tables to our Auth model.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncpg
from contextlib import asynccontextmanager
import logging
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ExternalAuthRepository:
    """
    Repository for connecting to the Auth Service PostgreSQL database.
    
    This repository provides direct database access to authentication data using
    schema-per-tenant approach, mapping from person, person_role, and person_permission
    tables to our Auth model structure.
    """
    
    def __init__(self, schema_name: str):
        """
        Initialize the auth repository with database connection pool.
        
        Args:
            schema_name: The tenant-specific schema name (e.g., 'demo')
        """
        self._pool: Optional[asyncpg.Pool] = None
        self.schema_name = schema_name
        self.db_url = getattr(settings, 'AUTH_SERVICE_DATABASE_URL', None)
        
        if not self.db_url:
            logger.warning("AUTH_SERVICE_DATABASE_URL not configured")
    
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if not self.db_url:
            raise ValueError("Auth service database URL not configured")
            
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.db_url,
                min_size=2,
                max_size=10,
                command_timeout=30.0,
                max_inactive_connection_lifetime=300.0,
            )
            logger.info(f"Auth service database connection pool created for schema: {self.schema_name}")
        except Exception as e:
            logger.error(f"Failed to create auth service connection pool: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Auth service database connection pool closed")
    
    async def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            async with self.get_connection() as conn:
                # Simple test query
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Auth service database connection test failed: {str(e)}")
            return False

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool with schema context."""
        if not self._pool:
            await self.initialize()
            
        async with self._pool.acquire() as conn:
            # Set the search path to the tenant schema
            await conn.execute(f"SET search_path TO {self.schema_name}")
            yield conn
    

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user details by ID from person table with roles and permissions.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User data dictionary mapped to Auth model structure or None if not found
        """
        query = """
            SELECT 
                p.id, 
                p.username, 
                p.email, 
                p.password AS password_hash, 
                p.first_name, 
                p.last_name, 
                COALESCE( 
                    jsonb_agg(DISTINCT r.slug) FILTER (WHERE r.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS roles, 
                COALESCE( 
                    jsonb_agg(DISTINCT perm.slug) FILTER (WHERE perm.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS permissions, 
                NOT p.is_deactivated AS is_active, 
                p.is_verified, 
                p.first_time_login AS last_login, 
                0 AS login_attempts, 
                NULL::timestamp with time zone AS locked_until, 
                p.updated_at AS password_changed_at, 
                false AS must_change_password, 
                p.created_at, 
                p.updated_at 
            FROM person p 
            LEFT JOIN person_role pr ON p.id = pr.person_id 
                AND (pr.end_date IS NULL OR pr.end_date > NOW()) 
            LEFT JOIN roles r ON pr.role_id = r.id 
            LEFT JOIN person_permission pp ON p.id = pp.person_id 
                AND (pp.end_date IS NULL OR pp.end_date > NOW()) 
            LEFT JOIN permissions perm ON pp.perm_id = perm.id 
            WHERE p.id = $1 AND p.deleted_at IS NULL 
            GROUP BY 
                p.id, p.username, p.email, p.password, 
                p.first_name, p.last_name, 
                p.is_deactivated, p.is_verified, 
                p.first_time_login, p.created_at, p.updated_at
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, user_id)
                if not row:
                    return None
                
                # Properly parse JSON arrays from jsonb_agg
                roles = row['roles'] if row['roles'] else []
                permissions = row['permissions'] if row['permissions'] else []
                
                # Convert to Python lists if they're not already
                if isinstance(roles, str):
                    roles = json.loads(roles)
                if isinstance(permissions, str):
                    permissions = json.loads(permissions)
                
                return {
                    'id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'password_hash': row['password_hash'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'roles': roles,
                    'permissions': permissions,
                    'is_active': row['is_active'],
                    'is_verified': row['is_verified'],
                    'last_login': row['last_login'],
                    'login_attempts': row['login_attempts'],
                    'locked_until': row['locked_until'],
                    'password_changed_at': row['password_changed_at'],
                    'must_change_password': row['must_change_password'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user details by email from person table with roles and permissions.
        
        Args:
            email: The user's email address
            
        Returns:
            User data dictionary mapped to Auth model structure or None if not found
        """
        query = """
            SELECT 
                p.id, 
                p.username, 
                p.email, 
                p.password AS password_hash, 
                p.first_name, 
                p.last_name, 
                COALESCE( 
                    jsonb_agg(DISTINCT r.slug) FILTER (WHERE r.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS roles, 
                COALESCE( 
                    jsonb_agg(DISTINCT perm.slug) FILTER (WHERE perm.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS permissions, 
                NOT p.is_deactivated AS is_active, 
                p.is_verified, 
                p.first_time_login AS last_login, 
                0 AS login_attempts, 
                NULL::timestamp with time zone AS locked_until, 
                p.updated_at AS password_changed_at, 
                false AS must_change_password, 
                p.created_at, 
                p.updated_at 
            FROM person p 
            LEFT JOIN person_role pr ON p.id = pr.person_id 
                AND (pr.end_date IS NULL OR pr.end_date > NOW()) 
            LEFT JOIN roles r ON pr.role_id = r.id 
            LEFT JOIN person_permission pp ON p.id = pp.person_id 
                AND (pp.end_date IS NULL OR pp.end_date > NOW()) 
            LEFT JOIN permissions perm ON pp.perm_id = perm.id 
            WHERE p.email = $1 AND p.deleted_at IS NULL 
            GROUP BY 
                p.id, p.username, p.email, p.password, 
                p.first_name, p.last_name, 
                p.is_deactivated, p.is_verified, 
                p.first_time_login, p.created_at, p.updated_at
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, email)
                if not row:
                    return None
                
                # Properly parse JSON arrays from jsonb_agg
                roles = row['roles'] if row['roles'] else []
                permissions = row['permissions'] if row['permissions'] else []
                
                # Convert to Python lists if they're not already
                if isinstance(roles, str):
                    roles = json.loads(roles)
                if isinstance(permissions, str):
                    permissions = json.loads(permissions)
                
                return {
                    'id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'password_hash': row['password_hash'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'roles': roles,
                    'permissions': permissions,
                    'is_active': row['is_active'],
                    'is_verified': row['is_verified'],
                    'last_login': row['last_login'],
                    'login_attempts': row['login_attempts'],
                    'locked_until': row['locked_until'],
                    'password_changed_at': row['password_changed_at'],
                    'must_change_password': row['must_change_password'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def validate_user_credentials(self, email: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """
        Validate user credentials against person table.
        
        Args:
            email: User's email address
            password_hash: Hashed password for validation
            
        Returns:
            User data dictionary if valid, None otherwise
        """
        query = """
            SELECT 
                p.id, 
                p.username, 
                p.email, 
                p.password AS password_hash, 
                p.first_name, 
                p.last_name, 
                COALESCE( 
                    jsonb_agg(DISTINCT r.slug) FILTER (WHERE r.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS roles, 
                COALESCE( 
                    jsonb_agg(DISTINCT perm.slug) FILTER (WHERE perm.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS permissions, 
                NOT p.is_deactivated AS is_active, 
                p.is_verified, 
                p.first_time_login AS last_login, 
                0 AS login_attempts, 
                NULL::timestamp with time zone AS locked_until, 
                p.updated_at AS password_changed_at, 
                false AS must_change_password, 
                p.created_at, 
                p.updated_at 
            FROM person p 
            LEFT JOIN person_role pr ON p.id = pr.person_id 
                AND (pr.end_date IS NULL OR pr.end_date > NOW()) 
            LEFT JOIN roles r ON pr.role_id = r.id 
            LEFT JOIN person_permission pp ON p.id = pp.person_id 
                AND (pp.end_date IS NULL OR pp.end_date > NOW()) 
            LEFT JOIN permissions perm ON pp.perm_id = perm.id 
            WHERE p.email = $1 AND p.password = $2 
                AND p.is_deactivated = false AND p.deleted_at IS NULL 
            GROUP BY 
                p.id, p.username, p.email, p.password, 
                p.first_name, p.last_name, 
                p.is_deactivated, p.is_verified, 
                p.first_time_login, p.created_at, p.updated_at
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, email, password_hash)
                if not row:
                    return None
                
                # Properly parse JSON arrays from jsonb_agg
                roles = row['roles'] if row['roles'] else []
                permissions = row['permissions'] if row['permissions'] else []
                
                # Convert to Python lists if they're not already
                if isinstance(roles, str):
                    roles = json.loads(roles)
                if isinstance(permissions, str):
                    permissions = json.loads(permissions)
                
                # Convert jsonb arrays to Python lists (excluding password_hash for security)
                return {
                    'id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'roles': roles,
                    'permissions': permissions,
                    'is_active': row['is_active'],
                    'is_verified': row['is_verified'],
                    'last_login': row['last_login'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
        except Exception as e:
            logger.error(f"Error validating credentials for {email}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """
        Get user roles from person_role table.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of role slugs
        """
        query = """
            SELECT DISTINCT r.slug
            FROM person_role pr
            JOIN roles r ON pr.role_id = r.id
            WHERE pr.person_id = $1 
                AND (pr.end_date IS NULL OR pr.end_date > NOW())
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, user_id)
                return [row['slug'] for row in rows]
        except Exception as e:
            logger.error(f"Error fetching roles for user {user_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_user_permissions(self, user_id: UUID) -> List[str]:
        """
        Get user permissions from person_permission table.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of permission slugs
        """
        query = """
            SELECT DISTINCT perm.slug
            FROM person_permission pp
            JOIN permissions perm ON pp.perm_id = perm.id
            WHERE pp.person_id = $1 
                AND (pp.end_date IS NULL OR pp.end_date > NOW())
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, user_id)
                return [row['slug'] for row in rows]
        except Exception as e:
            logger.error(f"Error fetching permissions for user {user_id}: {str(e)}")
            raise
    

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_tenant_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all users for the current tenant from person table.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user data dictionaries mapped to Auth model structure
        """
        query = """
            SELECT 
                p.id, 
                p.username, 
                p.email, 
                p.password AS password_hash, 
                p.first_name, 
                p.last_name, 
                COALESCE( 
                    jsonb_agg(DISTINCT r.slug) FILTER (WHERE r.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS roles, 
                COALESCE( 
                    jsonb_agg(DISTINCT perm.slug) FILTER (WHERE perm.slug IS NOT NULL), 
                    '[]'::jsonb 
                ) AS permissions, 
                NOT p.is_deactivated AS is_active, 
                p.is_verified, 
                p.first_time_login AS last_login, 
                0 AS login_attempts, 
                NULL::timestamp with time zone AS locked_until, 
                p.updated_at AS password_changed_at, 
                false AS must_change_password, 
                p.created_at, 
                p.updated_at 
            FROM person p 
            LEFT JOIN person_role pr ON p.id = pr.person_id 
                AND (pr.end_date IS NULL OR pr.end_date > NOW()) 
            LEFT JOIN roles r ON pr.role_id = r.id 
            LEFT JOIN person_permission pp ON p.id = pp.person_id 
                AND (pp.end_date IS NULL OR pp.end_date > NOW()) 
            LEFT JOIN permissions perm ON pp.perm_id = perm.id 
            WHERE p.deleted_at IS NULL 
            GROUP BY 
                p.id, p.username, p.email, p.password, 
                p.first_name, p.last_name, 
                p.is_deactivated, p.is_verified, 
                p.first_time_login, p.created_at, p.updated_at
            ORDER BY p.created_at DESC
            LIMIT $1
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, limit)
                result = []
                for row in rows:
                    # Properly parse JSON arrays from jsonb_agg
                    roles = row['roles'] if row['roles'] else []
                    permissions = row['permissions'] if row['permissions'] else []
                    
                    # Convert to Python lists if they're not already
                    if isinstance(roles, str):
                        roles = json.loads(roles)
                    if isinstance(permissions, str):
                        permissions = json.loads(permissions)
                    
                    result.append({
                        'id': row['id'],
                        'username': row['username'],
                        'email': row['email'],
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'roles': roles,
                        'permissions': permissions,
                        'is_active': row['is_active'],
                        'is_verified': row['is_verified'],
                        'last_login': row['last_login'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                return result
        except Exception as e:
            logger.error(f"Error fetching tenant users: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in the auth system.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Created user data dictionary
        """
        query = """
            INSERT INTO users (
                email, first_name, last_name, password_hash, 
                is_active, is_verified, roles, permissions, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9
            ) RETURNING 
                id, email, first_name, last_name, is_active, is_verified,
                created_at, updated_at, roles, permissions, metadata
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    user_data['email'],
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data['password_hash'],
                    user_data.get('is_active', True),
                    user_data.get('is_verified', False),
                    user_data.get('roles', []),
                    user_data.get('permissions', []),
                    user_data.get('metadata', {})
                )
                return dict(row)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def update_user(self, user_id: UUID, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user information.
        
        Args:
            user_id: The user's unique identifier
            user_data: Dictionary containing updated user information
            
        Returns:
            Updated user data dictionary or None if not found
        """
        # Build dynamic update query based on provided fields
        update_fields = []
        values = []
        param_count = 1
        
        for field, value in user_data.items():
            if field in ['first_name', 'last_name', 'is_active', 'is_verified', 'roles', 'permissions', 'metadata']:
                update_fields.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if not update_fields:
            return await self.get_user_by_id(user_id)
        
        query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = ${param_count} AND deleted_at IS NULL
            RETURNING 
                id, email, first_name, last_name, is_active, is_verified,
                created_at, updated_at, roles, permissions, metadata
        """
        values.append(user_id)
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, *values)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        query = """
            UPDATE users 
            SET is_active = false, updated_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
        """
        
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(query, user_id)
                return result.split()[-1] == '1'  # Check if one row was affected
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {str(e)}")
            raise