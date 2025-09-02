from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID

from app.database.models.base import Base
from app.database.repositories.connection import DatabaseConnection

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with centralized connection management for multi-tenant support."""
    
    def __init__(self, model: Type[ModelType]):
        """Initialize the repository with the model class.
        
        Args:
            model: The SQLAlchemy model class this repository manages.
        """
        self.model = model
    
    async def create(
        self, 
        obj_in: Dict[str, Any], 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None
    ) -> ModelType:
        """Create a new record using centralized connection management."""
        async with DatabaseConnection.get_session(
            schema_name=schema_name,
            tenant_id=tenant_id,
            person_id=person_id
        ) as db:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            return db_obj
    
    async def get(
        self, 
        id: Any, 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None
    ) -> Optional[ModelType]:
        """Get a record by ID using centralized connection management."""
        async with DatabaseConnection.get_session(
            schema_name=schema_name,
            tenant_id=tenant_id,
            person_id=person_id
        ) as db:
            query = select(self.model).where(self.model.id == id)
            result = await db.execute(query)
            return result.scalars().first()
    
    async def get_multi(
        self, 
        schema_name: str,
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None
    ) -> List[ModelType]:
        """Get multiple records using centralized connection management."""
        async with DatabaseConnection.get_session(
            schema_name=schema_name,
            tenant_id=tenant_id,
            person_id=person_id
        ) as db:
            query = select(self.model).offset(skip).limit(limit)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            
            result = await db.execute(query)
            return result.scalars().all()
    
    async def update(
        self, 
        id: Any, 
        obj_in: Dict[str, Any], 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None
    ) -> Optional[ModelType]:
        """Update a record using centralized connection management."""
        async with DatabaseConnection.get_session(
            schema_name=schema_name,
            tenant_id=tenant_id,
            person_id=person_id
        ) as db:
            update_query = update(self.model).where(self.model.id == id)
            await db.execute(update_query.values(**obj_in))
            
            # Return the updated record
            query = select(self.model).where(self.model.id == id)
            result = await db.execute(query)
            return result.scalars().first()
    
    async def delete(
        self, 
        id: Any, 
        schema_name: str,
        tenant_id: Optional[int] = None,
        person_id: Optional[UUID] = None
    ) -> bool:
        """Delete a record using centralized connection management."""
        async with DatabaseConnection.get_session(
            schema_name=schema_name,
            tenant_id=tenant_id,
            person_id=person_id
        ) as db:
            delete_query = delete(self.model).where(self.model.id == id)
            result = await db.execute(delete_query)
            return result.rowcount > 0