from typing import Dict, Any, Optional
import asyncpg
from models.visitor import Visitor

class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None

    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(self.connection_string)

    async def store_visitor(self, visitor: Visitor) -> str:
        """Store visitor data in the database"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO visitors (
                    tenant_id, first_name, last_name, email, 
                    phone, visit_date, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING visitor_id
            """
            visitor_id = await conn.fetchval(
                query,
                visitor.tenant_id,
                visitor.first_name,
                visitor.last_name,
                visitor.email,
                visitor.phone,
                visitor.visit_date
            )
            return visitor_id

    async def get_visitor(self, visitor_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve visitor data"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT * FROM visitors 
                WHERE visitor_id = $1 AND tenant_id = $2
            """
            record = await conn.fetchrow(query, visitor_id, tenant_id)
            return dict(record) if record else None 