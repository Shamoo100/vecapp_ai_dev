# database.py
import asyncpg
import logging
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings
from app.database.tenant_context import TenantContext
from app.security.tenant_context import get_current_tenant_id, get_current_schema

logger = logging.getLogger(__name__)
settings = get_settings()

class DatabaseManager:
    """
    Unified database connection manager supporting both asyncpg and SQLAlchemy
    with multi-tenant schema support.
    """
    
    # Asyncpg components
    _asyncpg_pool: Optional[asyncpg.Pool] = None
    
    # SQLAlchemy components
    _sa_engine: Optional[AsyncEngine] = None
    _sa_session_factory: Optional[sessionmaker] = None

    @classmethod
    async def initialize(cls):
        """Initialize both connection pools"""
        # Initialize asyncpg pool
        if not cls._asyncpg_pool:
            cls._asyncpg_pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=settings.DB_MIN_CONNECTIONS,
                max_size=settings.DB_MAX_CONNECTIONS,
                command_timeout=settings.DB_COMMAND_TIMEOUT,
                max_inactive_connection_lifetime=settings.DB_MAX_INACTIVE_CONNECTION_LIFETIME,
            )
            logger.info("Asyncpg connection pool created")

        # Initialize SQLAlchemy engine
        if not cls._sa_engine:
            cls._sa_engine = create_async_engine(
                f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
                echo=False,
                future=True,
            )
            cls._sa_session_factory = sessionmaker(
                cls._sa_engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("SQLAlchemy engine created")

    @classmethod
    async def close(cls):
        """Close all connection pools"""
        if cls._asyncpg_pool:
            await cls._asyncpg_pool.close()
            cls._asyncpg_pool = None
            logger.info("Asyncpg connection pool closed")
        
        if cls._sa_engine:
            await cls._sa_engine.dispose()
            cls._sa_engine = None
            logger.info("SQLAlchemy engine disposed")

    # Asyncpg interface
    @classmethod
    @asynccontextmanager
    async def asyncpg_connection(cls, schema: Optional[str] = None) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get an asyncpg connection with schema context"""
        if not cls._asyncpg_pool:
            await cls.initialize()
        
        schema = schema or get_current_schema()
        async with cls._asyncpg_pool.acquire() as conn:
            if schema:
                await conn.execute(f"SET search_path TO {schema}, public")
            try:
                yield conn
            finally:
                if schema:
                    await conn.execute("SET search_path TO public")

    @classmethod
    async def execute_transaction(cls, callback, schema: Optional[str] = None, *args, **kwargs):
        """Execute asyncpg operations in a transaction"""
        async with cls.asyncpg_connection(schema) as conn:
            async with conn.transaction():
                return await callback(conn, *args, **kwargs)

    # SQLAlchemy interface
    @classmethod
    @asynccontextmanager
    async def sa_session(cls, schema: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
        """Get a SQLAlchemy async session with schema context"""
        if not cls._sa_session_factory:
            await cls.initialize()
        
        schema = schema or get_current_schema()
        session = cls._sa_session_factory()
        
        try:
            if schema:
                await session.execute(f"SET search_path TO {schema}, public")
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Hybrid helpers
    @classmethod
    async def execute(cls, query: str, *args, schema: Optional[str] = None, **kwargs) -> str:
        """Execute query using asyncpg"""
        async with cls.asyncpg_connection(schema) as conn:
            return await conn.execute(query, *args, **kwargs)

    @classmethod
    async def fetch(cls, query: str, *args, schema: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Fetch rows using asyncpg"""
        async with cls.asyncpg_connection(schema) as conn:
            rows = await conn.fetch(query, *args, **kwargs)
            return [dict(row) for row in rows]

    @classmethod
    async def fetchval(cls, query: str, *args, schema: Optional[str] = None, **kwargs) -> Any:
        """Fetch single value using asyncpg"""
        async with cls.asyncpg_connection(schema) as conn:
            return await conn.fetchval(query, *args, **kwargs)

    @classmethod
    def get_schema_name(cls, tenant_id: UUID) -> str:
        """Get schema name from tenant ID"""
        return TenantContext.get_schema_name(str(tenant_id))