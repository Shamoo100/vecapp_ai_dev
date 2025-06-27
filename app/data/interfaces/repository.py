from typing import Dict, Any, List, Optional, TypeVar, Generic, Protocol
from uuid import UUID

T = TypeVar('T')

class IRepository(Protocol, Generic[T]):
    """Interface for all repositories to implement"""
    
    async def create(self, data: Dict[str, Any], tenant_id: Optional[UUID] = None) -> str:
        """Create a new record"""
        ...
    
    async def get_by_id(self, id: UUID, tenant_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        ...
    
    async def get_all(self, tenant_id: Optional[UUID] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all records matching optional filters"""
        ...
    
    async def update(self, id: UUID, data: Dict[str, Any], tenant_id: Optional[UUID] = None) -> bool:
        """Update a record by ID"""
        ...
    
    async def delete(self, id: UUID, tenant_id: Optional[UUID] = None) -> bool:
        """Delete a record by ID"""
        ...