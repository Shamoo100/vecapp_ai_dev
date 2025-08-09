from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database.models.base import Base
from uuid import UUID
from app.database.repositories.tenant_context import get_current_tenant_id

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations and tenant support."""
    
    def __init__(self, model: Type[ModelType]):
        """Initialize the repository with the model class.
        
        Args:
            model: The SQLAlchemy model class this repository manages.
        """
        self.model = model
    
    async def create(self, db: AsyncSession, obj_in: Dict[str, Any], tenant_id: Optional[UUID] = None) -> ModelType:
        """Create a new record.
        
        Args:
            db: Async database session
            obj_in: Dictionary of attributes for the new object
            tenant_id: Optional tenant ID for multi-tenant support
        
        Returns:
            The created model instance
        """
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        if tenant_id and 'tenant_id' not in obj_in:
            obj_in['tenant_id'] = tenant_id
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, id: Any, tenant_id: Optional[UUID] = None) -> Optional[ModelType]:
        """Get a record by ID.
        
        Args:
            db: Async database session
            id: ID of the record
            tenant_id: Optional tenant ID for filtering
        
        Returns:
            The model instance or None if not found
        """
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        query = select(self.model).where(self.model.id == id)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None, tenant_id: Optional[UUID] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filters.
        
        Args:
            db: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dictionary of filters
            tenant_id: Optional tenant ID for filtering
        
        Returns:
            List of model instances
        """
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        query = select(self.model).offset(skip).limit(limit)
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update(
        self, db: AsyncSession, id: Any, obj_in: Dict[str, Any], tenant_id: Optional[UUID] = None
    ) -> Optional[ModelType]:
        """Update a record.
        
        Args:
            db: Async database session
            id: ID of the record to update
            obj_in: Dictionary of attributes to update
            tenant_id: Optional tenant ID for filtering
        
        Returns:
            The updated model instance or None if not found
        """
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        update_query = update(self.model).where(self.model.id == id)
        if tenant_id:
            update_query = update_query.where(self.model.tenant_id == tenant_id)
        await db.execute(update_query.values(**obj_in))
        return await self.get(db, id, tenant_id)
    
    async def delete(self, db: AsyncSession, id: Any, tenant_id: Optional[UUID] = None) -> bool:
        """Delete a record.
        
        Args:
            db: Async database session
            id: ID of the record to delete
            tenant_id: Optional tenant ID for filtering
        
        Returns:
            True if the record was deleted, False otherwise
        """
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        delete_query = delete(self.model).where(self.model.id == id)
        if tenant_id:
            delete_query = delete_query.where(self.model.tenant_id == tenant_id)
        result = await db.execute(delete_query)
        return result.rowcount > 0