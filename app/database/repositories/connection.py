from typing import Optional, AsyncContextManager, Dict, Any, List, Type, TypeVar, Callable, Union
import asyncpg
from contextlib import asynccontextmanager
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.config.settings import get_settings
from app.database.repositories.tenant_context import TenantContext, get_current_tenant_id

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')

class DatabaseConnection:
    """
    Unified database connection manager that supports both raw asyncpg connections
    and SQLAlchemy sessions with multi-tenant and multi-database capabilities.
    
    Key Features:
    - tenant_id: Integer registry ID for tenant identification
    - person_id: UUID for person-specific operations (major identifier)
    - schema_name: REQUIRED core identifier for database operations in multi-tenant system
    - Multi-database support with connection pooling
    - Proper error handling and logging
    
    Note: In this multi-tenant system, schema_name is REQUIRED for all tenant-specific operations.
    """
    
    # Connection pools for different databases
    _pools: Dict[str, asyncpg.Pool] = {}
    _engines: Dict[str, AsyncEngine] = {}
    _session_factories: Dict[str, Callable[[], AsyncSession]] = {}
    
    # Default database name
    DEFAULT_DB = "default"
    
    @classmethod
    async def initialize(cls, db_name: str = DEFAULT_DB) -> None:
        """
        Initialize connection pool and SQLAlchemy engine for a specific database.
        
        Args:
            db_name: Database identifier (default is the main database)
        """
        # Get database URL based on db_name
        if db_name == cls.DEFAULT_DB:
            db_url = settings.DATABASE_URL
            sqlalchemy_url = (
                f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
                f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
        else:
            # For additional databases, configure URLs in settings
            db_url = getattr(settings, f"{db_name.upper()}_DATABASE_URL", settings.DATABASE_URL)
            sqlalchemy_url = getattr(
                settings, 
                f"{db_name.upper()}_SQLALCHEMY_URL", 
                f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
                f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
        
        # Initialize asyncpg pool if not exists
        if db_name not in cls._pools or cls._pools[db_name] is None:
            try:
                cls._pools[db_name] = await asyncpg.create_pool(
                    dsn=db_url,
                    min_size=settings.DB_MIN_CONNECTIONS,
                    max_size=settings.DB_MAX_CONNECTIONS,
                    command_timeout=settings.DB_COMMAND_TIMEOUT,
                    max_inactive_connection_lifetime=settings.DB_MAX_INACTIVE_CONNECTION_LIFETIME,
                )
                logger.info(f"Database connection pool created for {db_name}")
            except Exception as e:
                logger.error(f"Failed to create database connection pool for {db_name}: {str(e)}")
                raise
        
        # Initialize SQLAlchemy engine if not exists
        if db_name not in cls._engines or cls._engines[db_name] is None:
            try:
                cls._engines[db_name] = create_async_engine(
                    sqlalchemy_url,
                    echo=False,
                    future=True,
                    poolclass=NullPool if settings.DB_USE_NULL_POOL else None,
                )
                
                # Create session factory
                cls._session_factories[db_name] = sessionmaker(
                    cls._engines[db_name], 
                    class_=AsyncSession, 
                    expire_on_commit=False
                )
                logger.info(f"SQLAlchemy engine created for {db_name}")
            except Exception as e:
                logger.error(f"Failed to create SQLAlchemy engine for {db_name}: {str(e)}")
                raise
    
    @classmethod
    async def get_pool(cls, db_name: str = DEFAULT_DB) -> asyncpg.Pool:
        """
        Get or create the database connection pool.
        
        Args:
            db_name: Database identifier
            
        Returns:
            The database connection pool
        """
        if db_name not in cls._pools or cls._pools[db_name] is None:
            await cls.initialize(db_name)
        
        return cls._pools[db_name]
    
    @classmethod
    def _get_schema_name_from_tenant_id(cls, tenant_id: int) -> str:
        """
        Convert tenant registry ID to schema name.
        
        Args:
            tenant_id: Integer tenant registry ID
            
        Returns:
            Schema name for the tenant
        """
        return f"tenant_{tenant_id}"
    
    @classmethod
    def _resolve_schema_name(cls, tenant_id: Optional[int] = None, schema_name: Optional[str] = None) -> str:
        """
        Resolve schema name from tenant_id or schema_name.
        In multi-tenant system, one of these MUST be provided.
        
        Args:
            tenant_id: Optional tenant registry ID (int)
            schema_name: Optional explicit schema name
            
        Returns:
            Resolved schema name
            
        Raises:
            ValueError: If neither tenant_id nor schema_name is provided
        """
        if schema_name:
            return schema_name
        elif tenant_id:
            return cls._get_schema_name_from_tenant_id(tenant_id)
        else:
            # Try to get from current context as fallback
            current_tenant = get_current_tenant_id()
            if current_tenant:
                return TenantContext.get_schema_name(current_tenant)
            else:
                raise ValueError(
                    "Multi-tenant system requires either 'tenant_id' or 'schema_name' to be provided. "
                    "All tenant-specific database operations must specify the target schema."
                )
    
    @classmethod
    def _log_context_info(cls, tenant_id: Optional[int], person_id: Optional[UUID], schema_name: str) -> None:
        """
        Log context information for debugging.
        
        Args:
            tenant_id: Tenant registry ID
            person_id: Person UUID
            schema_name: Schema name (required)
        """
        context_info = [f"schema={schema_name}"]
        if tenant_id:
            context_info.append(f"tenant_id={tenant_id}")
        if person_id:
            context_info.append(f"person_id={person_id}")
        
        logger.debug(f"Database context: {', '.join(context_info)}")
    
    @classmethod
    @asynccontextmanager
    async def get_connection(
        cls, 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB
    ) -> AsyncContextManager[asyncpg.Connection]:
        """
        Get a raw asyncpg connection with tenant and person context.
        
        Args:
            schema_name: REQUIRED schema name for multi-tenant operations
            tenant_id: Optional tenant registry ID (int) for additional context
            person_id: Optional person UUID (for person-specific operations)
            db_name: Database identifier
            
        Yields:
            Raw asyncpg connection with proper schema context
        """
        pool = await cls.get_pool(db_name)
        
        # Log context for debugging
        cls._log_context_info(tenant_id, person_id, schema_name)
            
        async with pool.acquire() as conn:
            try:
                # Set schema context (required for multi-tenant)
                await conn.execute(f"SET search_path TO {schema_name}, public")
                logger.debug(f"Set search_path to {schema_name}")
                
                # Store context in connection for potential use in queries
                if person_id:
                    setattr(conn, '_person_id', person_id)
                if tenant_id:
                    setattr(conn, '_tenant_id', tenant_id)
                
                yield conn
            except Exception as e:
                logger.error(f"Error in database connection: {str(e)}")
                raise
            finally:
                # Reset search path to public when done
                try:
                    await conn.execute("SET search_path TO public")
                except Exception as e:
                    logger.warning(f"Failed to reset search_path: {str(e)}")
    
    @classmethod
    async def test_connection(cls, db_name: str = DEFAULT_DB) -> bool:
        """
        Test the database connection.
        
        Args:
            db_name: Database identifier
            
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            pool = await cls.get_pool(db_name)
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    @classmethod
    @asynccontextmanager
    async def get_session(
        cls, 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB
    ) -> AsyncContextManager[AsyncSession]:
        """
        Get a SQLAlchemy session with tenant and person context.
        
        Args:
            schema_name: REQUIRED schema name for multi-tenant operations
            tenant_id: Optional tenant registry ID (int) for additional context
            person_id: Optional person UUID (for person-specific operations)
            db_name: Database identifier
            
        Yields:
            SQLAlchemy AsyncSession with proper schema context
        """
        if db_name not in cls._session_factories or cls._session_factories[db_name] is None:
            await cls.initialize(db_name)
            
        session = cls._session_factories[db_name]()
        
        # Log context for debugging
        cls._log_context_info(tenant_id, person_id, schema_name)
        
        try:
            # Set schema context (required for multi-tenant)
            await session.execute(text(f"SET search_path TO {schema_name}, public"))
            logger.debug(f"Set search_path to {schema_name} for session")
            
            # Store context in session for potential use
            if person_id:
                setattr(session, '_person_id', person_id)
            if tenant_id:
                setattr(session, '_tenant_id', tenant_id)
            setattr(session, '_schema_name', schema_name)
                
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Error in database session: {str(e)}")
            await session.rollback()
            raise
        finally:
            # Reset search path to public
            try:
                await session.execute(text("SET search_path TO public"))
            except Exception as e:
                logger.warning(f"Failed to reset search_path in session: {str(e)}")
            await session.close()
    
    @classmethod
    async def execute(
        cls, 
        query: str, 
        *args, 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB, 
        **kwargs
    ) -> str:
        """
        Execute a database query using raw asyncpg.
        
        Args:
            query: The query to execute
            schema_name: REQUIRED schema name for multi-tenant operations
            tenant_id: Optional tenant registry ID (int)
            person_id: Optional person UUID
            db_name: Database identifier
            *args, **kwargs: Arguments to pass to the query
            
        Returns:
            The query result
        """
        async with cls.get_connection(schema_name, tenant_id, person_id, db_name) as conn:
            return await conn.execute(query, *args, **kwargs)
    
    @classmethod
    async def fetch(
        cls, 
        query: str, 
        *args, 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows using raw asyncpg.
        
        Args:
            query: The query to execute
            schema_name: REQUIRED schema name for multi-tenant operations
            tenant_id: Optional tenant registry ID (int)
            person_id: Optional person UUID
            db_name: Database identifier
            *args, **kwargs: Arguments to pass to the query
            
        Returns:
            List of rows as dictionaries
        """
        async with cls.get_connection(schema_name, tenant_id, person_id, db_name) as conn:
            rows = await conn.fetch(query, *args, **kwargs)
            return [dict(row) for row in rows]
    
    @classmethod
    async def fetchval(
        cls, 
        query: str, 
        *args, 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB, 
        **kwargs
    ) -> Any:
        """
        Fetch a single value using raw asyncpg.
        
        Args:
            query: The query to execute
            schema_name: REQUIRED schema name for multi-tenant operations
            tenant_id: Optional tenant registry ID (int)
            person_id: Optional person UUID
            db_name: Database identifier
            *args, **kwargs: Arguments to pass to the query
            
        Returns:
            The query result value
        """
        async with cls.get_connection(schema_name, tenant_id, person_id, db_name) as conn:
            return await conn.fetchval(query, *args, **kwargs)
    
    @classmethod
    async def transaction(
        cls, 
        callback: Callable[[asyncpg.Connection, ...], T], 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB,
        *args, 
        **kwargs
    ) -> T:
        """
        Execute a callback within a transaction using raw asyncpg.
        
        Args:
            callback: Async function that takes a connection as first argument
            schema_name: REQUIRED schema name for multi-tenant operations
            tenant_id: Optional tenant registry ID (int)
            person_id: Optional person UUID
            db_name: Database identifier
            *args: Additional arguments to pass to callback
            **kwargs: Additional keyword arguments to pass to callback
            
        Returns:
            Result of the callback
        """
        async with cls.get_connection(schema_name, tenant_id, person_id, db_name) as conn:
            async with conn.transaction():
                return await callback(conn, *args, **kwargs)
    
    @classmethod
    async def get_person_context(
        cls,
        person_id: UUID,
        schema_name: str,
        tenant_id: Optional[int] = None,
        db_name: str = DEFAULT_DB
    ) -> Dict[str, Any]:
        """
        Get database context for a specific person.
        
        This is a utility method for person-specific operations that need
        to verify person existence and get related context.
        
        Args:
            person_id: Person UUID
            schema_name: REQUIRED schema name for multi-tenant operations
            tenant_id: Optional tenant registry ID (int)
            db_name: Database identifier
            
        Returns:
            Dictionary with person context information
        """
        try:
            # Check if person exists in the specified context
            query = "SELECT id, first_name, last_name FROM ai_person WHERE id = $1"
            person_data = await cls.fetch(
                query, 
                person_id,
                schema_name=schema_name,
                tenant_id=tenant_id,
                db_name=db_name
            )
            
            return {
                "person_id": person_id,
                "exists": len(person_data) > 0,
                "person_data": person_data[0] if person_data else None,
                "tenant_id": tenant_id,
                "schema_name": schema_name
            }
        except Exception as e:
            logger.error(f"Error getting person context for {person_id}: {str(e)}")
            return {
                "person_id": person_id,
                "exists": False,
                "person_data": None,
                "error": str(e)
            }
    
    @classmethod
    async def close_all(cls) -> None:
        """Close all database connection pools and engines."""
        # Close asyncpg pools
        for db_name, pool in cls._pools.items():
            if pool:
                await pool.close()
                logger.info(f"Database connection pool closed for {db_name}")
        cls._pools = {}
        
        # Close SQLAlchemy engines
        for db_name, engine in cls._engines.items():
            if engine:
                await engine.dispose()
                logger.info(f"SQLAlchemy engine closed for {db_name}")
        cls._engines = {}
        cls._session_factories = {}
    
    @classmethod
    async def close(cls, db_name: str = DEFAULT_DB) -> None:
        """
        Close specific database connection pool and engine.
        
        Args:
            db_name: Database identifier
        """
        # Close asyncpg pool
        if db_name in cls._pools and cls._pools[db_name]:
            await cls._pools[db_name].close()
            cls._pools[db_name] = None
            logger.info(f"Database connection pool closed for {db_name}")
        
        # Close SQLAlchemy engine
        if db_name in cls._engines and cls._engines[db_name]:
            await cls._engines[db_name].dispose()
            cls._engines[db_name] = None
            cls._session_factories[db_name] = None
            logger.info(f"SQLAlchemy engine closed for {db_name}")


# FastAPI dependency function for database sessions
async def get_db_dependency(
    schema_name: str,
    tenant_id: Optional[int] = None, 
    person_id: Optional[UUID] = None,
    db_name: str = DatabaseConnection.DEFAULT_DB
):
    """
    FastAPI dependency function for getting database sessions.
    
    This function is designed to work with FastAPI's Depends() system.
    It properly handles the async context manager and yields the session.
    
    Args:
        schema_name: REQUIRED schema name for multi-tenant operations
        tenant_id: Optional tenant registry ID (int) for additional context
        person_id: Optional person UUID (for person-specific operations)
        db_name: Database identifier
        
    Yields:
        SQLAlchemy session with proper schema and person context
    """
    async with DatabaseConnection.get_session(schema_name, tenant_id, person_id, db_name) as session:
        yield session


# Convenience aliases for backward compatibility
Database = DatabaseConnection
get_db_session = get_db_dependency
get_db = get_db_dependency