from typing import Dict, Any, Optional, List
from uuid import UUID
from app.data.base_repository import BaseRepository
from app.models.visitor import Visitor

class VisitorRepository(BaseRepository[Visitor]):
    """Repository for managing visitor data with tenant schema support.
    
    This repository demonstrates how to use the BaseRepository class to implement
    tenant-aware database operations for a specific entity.
    """
    
    def __init__(self):
        """Initialize the visitor repository."""
        super().__init__(table_name="visitors")
    
    async def get_recent_visitors(self, limit: int = 10, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent visitors for a tenant.
        
        Args:
            limit: Maximum number of visitors to return
            tenant_id: Optional tenant ID to set schema context
            
        Returns:
            List of recent visitors
        """
        query = f"""
            SELECT * FROM {self.table_name}
            ORDER BY visit_date DESC
            LIMIT ${1}
        """
        
        async with self._get_connection(tenant_id) as conn:
            rows = await conn.fetch(query, limit)
            return [dict(row) for row in rows]
    
    async def search_visitors(self, search_term: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for visitors by name or email.
        
        Args:
            search_term: Term to search for in name or email
            tenant_id: Optional tenant ID to set schema context
            
        Returns:
            List of matching visitors
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE 
                (first_name ILIKE $1 OR 
                last_name ILIKE $1 OR 
                email ILIKE $1)
        """
        
        # Add tenant_id filter for additional security if available
        if tenant_id:
            query += " AND tenant_id = $2"
            
        search_pattern = f"%{search_term}%"
        
        async with self._get_connection(tenant_id) as conn:
            if tenant_id:
                rows = await conn.fetch(query, search_pattern, tenant_id)
            else:
                rows = await conn.fetch(query, search_pattern)
                
            return [dict(row) for row in rows]
    
    async def get_visitor_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get visitor statistics for a tenant.
        
        Args:
            tenant_id: Optional tenant ID to set schema context
            
        Returns:
            Dictionary with visitor statistics
        """
        query = f"""
            SELECT 
                COUNT(*) as total_visitors,
                COUNT(DISTINCT email) as unique_visitors,
                MAX(visit_date) as last_visit_date,
                MIN(visit_date) as first_visit_date
            FROM {self.table_name}
        """
        
        # Add tenant_id filter for additional security if available
        if tenant_id:
            query += " WHERE tenant_id = $1"
            
        async with self._get_connection(tenant_id) as conn:
            if tenant_id:
                row = await conn.fetchrow(query, tenant_id)
            else:
                row = await conn.fetchrow(query)
                
            return dict(row) if row else {}