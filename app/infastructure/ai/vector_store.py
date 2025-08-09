from typing import List, Dict, Any, Optional
from uuid import UUID
import numpy as np
from app.database.connection_manager import ConnectionManager

class VectorStore:
    """Repository for storing and retrieving vector embeddings"""
    
    async def store_embedding(
        self,
        entity_id: UUID,
        entity_type: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        tenant_id: UUID
    ) -> UUID:
        """Store a vector embedding
        
        Args:
            entity_id: ID of the entity this embedding represents
            entity_type: Type of entity (e.g., 'document', 'user', etc.)
            embedding: Vector embedding as a list of floats
            metadata: Additional metadata to store with the embedding
            tenant_id: Tenant ID for multi-tenant isolation
            
        Returns:
            ID of the stored embedding
        """
        async with ConnectionManager.get_connection(tenant_id) as conn:
            embedding_id = await conn.fetchval(
                """
                INSERT INTO vector_embeddings (
                    entity_id, entity_type, embedding, metadata, tenant_id
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                entity_id, entity_type, embedding, metadata, tenant_id
            )
            return embedding_id
    
    async def search_similar(
        self,
        query_embedding: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        tenant_id: UUID = None
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings
        
        Args:
            query_embedding: Vector to search for
            entity_type: Optional filter by entity type
            limit: Maximum number of results to return
            tenant_id: Tenant ID for multi-tenant isolation
            
        Returns:
            List of similar items with similarity scores
        """
        async with ConnectionManager.get_connection(tenant_id) as conn:
            # Build query with optional entity_type filter
            query = """
                SELECT 
                    id, entity_id, entity_type, metadata,
                    1 - (embedding <=> $1) as similarity
                FROM vector_embeddings
                WHERE tenant_id = $2
            """
            params = [query_embedding, tenant_id]
            
            if entity_type:
                query += " AND entity_type = $3"
                params.append(entity_type)
                
            query += f" ORDER BY similarity DESC LIMIT {limit}"
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]