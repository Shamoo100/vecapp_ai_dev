from typing import Optional, AsyncContextManager, Dict, Any, List, Type, TypeVar, Callable, Union
import asyncpg
from contextlib import asynccontextmanager
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config.settings import get_settings
from app.database.repositories.tenant_context import TenantContext 

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')

class DatabaseConnection:
    """
    Unified database connection manager that supports both raw asyncpg connections
    and SQLAlchemy sessions with multi-tenant and multi-database capabilities.
    """
    
    # Connection pools for different databases
    _pools: Dict[str, asyncpg.Pool] = {}
    _engines: Dict[str, AsyncEngine] = {}
    _session_factories: Dict[str, Callable[[], AsyncSession]] = {}
    
    # Default database name
    DEFAULT_DB = "default"
    
    @classmethod
    async def initialize(cls, db_name: str = DEFAULT_DB):
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
            # For additional databases, you would configure URLs in settings
            # and retrieve them based on db_name
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
    @asynccontextmanager
    async def get_connection(
        cls, 
        tenant_id: Optional[UUID] = None, 
        db_name: str = DEFAULT_DB
    ) -> AsyncContextManager[asyncpg.Connection]:
        # Use centralized get_schema_name
        if tenant_id:
            schema_name = get_schema_name(str(tenant_id))
            set_current_schema(schema_name)  # Set using centralized function
        pool = await cls.get_pool(db_name)
        
        # If tenant_id not provided, try to get from current context
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
            
        async with pool.acquire() as conn:
            if tenant_id:
                schema_name = TenantContext.get_schema_name(str(tenant_id))
                await conn.execute(f"SET search_path TO {schema_name}, public")
            try:
                yield conn
            finally:
                # Reset search path to public when done
                if tenant_id:
                    await conn.execute("SET search_path TO public")
    
    @classmethod
    @asynccontextmanager
    async def get_session(
        cls, 
        tenant_id: Optional[UUID] = None, 
        db_name: str = DEFAULT_DB
    ) -> AsyncContextManager[AsyncSession]:
        """
        Get a SQLAlchemy session with tenant schema set.
        
        Args:
            tenant_id: Optional tenant ID to set schema context
            db_name: Database identifier
            
        Yields:
            SQLAlchemy session with proper schema context
        """
        if db_name not in cls._session_factories or cls._session_factories[db_name] is None:
            await cls.initialize(db_name)
            
        session = cls._session_factories[db_name]()
        
        try:
            # If tenant_id provided, set schema context
            if tenant_id:
                schema_name = TenantContext.get_schema_name(str(tenant_id))
                await session.execute(f"SET search_path TO {schema_name}, public")
                
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Reset search path to public
            if tenant_id:
                await session.execute("SET search_path TO public")
            await session.close()
    
    @classmethod
    async def execute(
        cls, 
        query: str, 
        *args, 
        tenant_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB, 
        **kwargs
    ) -> str:
        """
        Execute a database query using raw asyncpg.
        
        Args:
            query: The query to execute
            tenant_id: Optional tenant ID
            db_name: Database identifier
            *args, **kwargs: Arguments to pass to the query
            
        Returns:
            The query result
        """
        async with cls.get_connection(tenant_id, db_name) as conn:
            return await conn.execute(query, *args, **kwargs)
    
    @classmethod
    async def fetch(
        cls, 
        query: str, 
        *args, 
        tenant_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows using raw asyncpg.
        
        Args:
            query: The query to execute
            tenant_id: Optional tenant ID
            db_name: Database identifier
            *args, **kwargs: Arguments to pass to the query
            
        Returns:
            List of rows as dictionaries
        """
        async with cls.get_connection(tenant_id, db_name) as conn:
            rows = await conn.fetch(query, *args, **kwargs)
            return [dict(row) for row in rows]
    
    @classmethod
    async def fetchval(
        cls, 
        query: str, 
        *args, 
        tenant_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB, 
        **kwargs
    ) -> Any:
        """
        Fetch a single value using raw asyncpg.
        
        Args:
            query: The query to execute
            tenant_id: Optional tenant ID
            db_name: Database identifier
            *args, **kwargs: Arguments to pass to the query
            
        Returns:
            The query result value
        """
        async with cls.get_connection(tenant_id, db_name) as conn:
            return await conn.fetchval(query, *args, **kwargs)
    
    @classmethod
    async def execute_transaction(
        cls, 
        callback: Callable[[asyncpg.Connection, ...], T], 
        tenant_id: Optional[UUID] = None,
        db_name: str = DEFAULT_DB,
        *args, 
        **kwargs
    ) -> T:
        """
        Execute a callback within a transaction using raw asyncpg.
        
        Args:
            callback: Async function that takes a connection as first argument
            tenant_id: Optional tenant ID
            db_name: Database identifier
            *args: Additional arguments to pass to callback
            **kwargs: Additional keyword arguments to pass to callback
            
        Returns:
            Result of the callback
        """
        async with cls.get_connection(tenant_id, db_name) as conn:
            async with conn.transaction():
                return await callback(conn, *args, **kwargs)
    
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


# Convenience aliases for backward compatibility
Database = DatabaseConnection
get_db_session = DatabaseConnection.get_session