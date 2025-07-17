from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncpg
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CalendarService:
    """
    Service for connecting to the Calendar Service PostgreSQL database.
    
    This service provides direct database access to calendar and event data,
    enabling the AI service to fetch scheduling information independently.
    """
    
    def __init__(self):
        """Initialize the calendar service with database connection pool."""
        self._pool: Optional[asyncpg.Pool] = None
        self.db_url = getattr(settings, 'CALENDAR_SERVICE_DATABASE_URL', None)
        
        if not self.db_url:
            logger.warning("CALENDAR_SERVICE_DATABASE_URL not configured")
    
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if not self.db_url:
            raise ValueError("Calendar service database URL not configured")
            
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.db_url,
                min_size=2,
                max_size=10,
                command_timeout=30.0,
                max_inactive_connection_lifetime=300.0,
            )
            logger.info("Calendar service database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create calendar service connection pool: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Calendar service database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self._pool:
            await self.initialize()
            
        async with self._pool.acquire() as conn:
            yield conn
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_upcoming_events(self, tenant_id: UUID, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Get upcoming events for a tenant.
        
        Args:
            tenant_id: The tenant's unique identifier
            days_ahead: Number of days to look ahead for events
            
        Returns:
            List of upcoming event dictionaries
        """
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        query = """
            SELECT 
                id, title, description, event_type, location,
                start_datetime, end_datetime, all_day,
                organizer_id, max_attendees, registration_required,
                created_at, updated_at
            FROM events 
            WHERE tenant_id = $1 
                AND start_datetime >= NOW() 
                AND start_datetime <= $2
                AND status = 'active'
            ORDER BY start_datetime ASC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, tenant_id, end_date)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching upcoming events for tenant {tenant_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_event_attendees(self, event_id: UUID, tenant_id: UUID) -> List[Dict[str, Any]]:
        """
        Get attendees for a specific event.
        
        Args:
            event_id: The event's unique identifier
            tenant_id: The tenant's unique identifier
            
        Returns:
            List of attendee dictionaries
        """
        query = """
            SELECT 
                ea.id, ea.member_id, ea.registration_date, ea.attendance_status,
                m.first_name, m.last_name, m.email
            FROM event_attendees ea
            JOIN members m ON ea.member_id = m.id
            WHERE ea.event_id = $1 AND ea.tenant_id = $2
            ORDER BY ea.registration_date ASC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, event_id, tenant_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching attendees for event {event_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_member_events(self, member_id: UUID, tenant_id: UUID, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get events a member has attended or registered for.
        
        Args:
            member_id: The member's unique identifier
            tenant_id: The tenant's unique identifier
            days_back: Number of days to look back for events
            
        Returns:
            List of member's event participation
        """
        start_date = datetime.now() - timedelta(days=days_back)
        
        query = """
            SELECT 
                e.id, e.title, e.event_type, e.start_datetime, e.end_datetime,
                ea.attendance_status, ea.registration_date
            FROM events e
            JOIN event_attendees ea ON e.id = ea.event_id
            WHERE ea.member_id = $1 AND ea.tenant_id = $2
                AND e.start_datetime >= $3
            ORDER BY e.start_datetime DESC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, member_id, tenant_id, start_date)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching events for member {member_id}: {str(e)}")
            raise