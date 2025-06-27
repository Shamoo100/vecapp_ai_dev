from typing import Dict, Any, Optional, List, TypeVar, Generic
from uuid import UUID
from app.database.connection_manager import ConnectionManager
from app.security.tenant_context import get_current_tenant_id, get_current_schema

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository class with tenant schema support.
    
    This class provides common database operations with automatic tenant schema
    context handling, simplifying the implementation of tenant-aware repositories.
    """
    
    def __init__(self, table_name: str):
        """Initialize the repository.
        
        Args:
            table_name: The name of the table this repository manages
        """
        self.table_name = table_name
    
    async def create(self, data: Dict[str, Any], tenant_id: Optional[UUID] = None) -> str:
        """Create a new record in the database.
        
        Args:
            data: Dictionary of column names and values
            tenant_id: Optional tenant ID to set schema context
            
        Returns:
            ID of the created record
        """
        # If tenant_id not provided, try to get from current context
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        
        # Ensure tenant_id is included in the data
        if tenant_id and 'tenant_id' not in data:
            data['tenant_id'] = tenant_id
            
        columns = list(data.keys())
        values = list(data.values())
        
        placeholders = [f'${i+1}' for i in range(len(values))]
        
        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING id
        """
        
        async with ConnectionManager.get_connection(tenant_id) as conn:
            return await conn.fetchval(query, *values)
    
    async def get_by_id(self, id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a record by ID.
        
        Args:
            id: ID of the record to get
            tenant_id: Optional tenant ID to set schema context
            
        Returns:
            Record as a dictionary or None if not found
        """
        # If tenant_id not provided, try to get from current context
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
            
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE id = $1
        """
        
        # Add tenant_id filter for additional security if available
        if tenant_id:
            query += " AND tenant_id = $2"
            
        async with ConnectionManager.get_connection(tenant_id) as conn:
            if tenant_id:
                row = await conn.fetchrow(query, id, tenant_id)
            else:
                row = await conn.fetchrow(query, id)
                
            return dict(row) if row else None
    
    async def get_all(self, tenant_id: Optional[str] = None, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all records matching optional filters.
        
        Args:
            tenant_id: Optional tenant ID to set schema context
            filters: Optional dictionary of column names and values to filter by
            
        Returns:
            List of records as dictionaries
        """
        # If tenant_id not provided, try to get from current context
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
            
        query = f"SELECT * FROM {self.table_name}"
        values = []
        
        # Build WHERE clause from filters
        where_clauses = []
        if filters:
            for i, (key, value) in enumerate(filters.items()):
                where_clauses.append(f"{key} = ${i+1}")
                values.append(value)
                
        # Add tenant_id filter for additional security if available
        if tenant_id:
            where_clauses.append(f"tenant_id = ${len(values)+1}")
            values.append(tenant_id)
            
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
            
        async with ConnectionManager.get_connection(tenant_id) as conn:
            rows = await conn.fetch(query, *values)
            return [dict(row) for row in rows]
    
    async def update(self, id: str, data: Dict[str, Any], tenant_id: Optional[str] = None) -> bool:
        """Update a record by ID.
        
        Args:
            id: ID of the record to update
            data: Dictionary of column names and values to update
            tenant_id: Optional tenant ID to set schema context
            
        Returns:
            True if the record was updated, False otherwise
        """
        # If tenant_id not provided, try to get from current context
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
            
        # Don't allow updating tenant_id
        if 'tenant_id' in data:
            del data['tenant_id']
            
        # Don't allow updating id
        if 'id' in data:
            del data['id']
            
        if not data:  # Nothing to update
            return False
            
        set_clauses = [f"{key} = ${i+1}" for i, key in enumerate(data.keys())]
        values = list(data.values())
        
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE id = ${len(values)+1}
        """
        
        # Add tenant_id filter for additional security if available
        if tenant_id:
            query += f" AND tenant_id = ${len(values)+2}"
            
        values.append(id)
        if tenant_id:
            values.append(tenant_id)
            
        async with ConnectionManager.get_connection(tenant_id) as conn:
            result = await conn.execute(query, *values)
            return 'UPDATE 1' in result
    
    async def delete(self, id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete a record by ID.
        
        Args:
            id: ID of the record to delete
            tenant_id: Optional tenant ID to set schema context
            
        Returns:
            True if the record was deleted, False otherwise
        """
        # If tenant_id not provided, try to get from current context
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
            
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        values = [id]
        
        # Add tenant_id filter for additional security if available
        if tenant_id:
            query += " AND tenant_id = $2"
            values.append(tenant_id)
            
        async with ConnectionManager.get_connection(tenant_id) as conn:
            result = await conn.execute(query, *values)
            return 'DELETE 1' in result