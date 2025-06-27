from typing import Generic, TypeVar, Type, List, Optional, Any, Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql import Select

from app.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def create(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get a record by ID."""
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update(
        self, db: AsyncSession, *, id: Any, obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update a record."""
        await db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        return await self.get(db, id)
    
    async def delete(self, db: AsyncSession, *, id: Any) -> None:
        """Delete a record."""
        await db.execute(delete(self.model).where(self.model.id == id))