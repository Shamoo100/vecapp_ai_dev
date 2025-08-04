"""
Calendar Repository implementation for cross-service database access.

This repository provides direct database access to the Calendar Service 
PostgreSQL database using schema-per-tenant approach.
"""

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


class CalendarRepository:
    """
    Repository for connecting to the Calendar Service PostgreSQL database.
    
    This repository provides direct database access to calendar and event data using
    schema-per-tenant approach, enabling independent calendar data access.
    """
    
    def __init__(self, tenant_schema: str):
        """
        Initialize the calendar repository with database connection pool.
        
        Args:
            tenant_schema: The tenant-specific schema name
        """
        self._pool: Optional[asyncpg.Pool] = None
        self.tenant_schema = tenant_schema
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
            logger.info(f"Calendar service database connection pool created for schema: {self.tenant_schema}")
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
        """Get a database connection from the pool with schema context."""
        if not self._pool:
            await self.initialize()
            
        async with self._pool.acquire() as conn:
            # Set the search path to the tenant schema
            await conn.execute(f"SET search_path TO {self.tenant_schema}")
            yield conn
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_upcoming_events(self, days_ahead: int = 14) -> List[Dict[str, Any]]:
        #TODO: EventClas meaning ask paul
        """
        Get upcoming events for the tenant.
        
        Args:
            days_ahead: Number of days to look ahead for events
            
        Returns:
            List of upcoming event dictionaries
        """
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        query = """
            SELECT 
                id, title, description, event_type_id, creator_id,
                start_time, end_time, start_date, end_date,
                is_all_day, is_same_day, venue_name, venue_address,
                meeting_link, meeting_room, visibility, status,
                recurrence_pattern, event_ends, time_zone,
                banner_image, additional_info,
                individual_cal_id, team_cal_id, group_cal_id,
                created_at, updated_at
            FROM event 
            WHERE start_time >= NOW() 
                AND start_time <= $1
                AND status = 1
            ORDER BY start_time ASC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, end_date)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching upcoming events: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_event_attendees(self, event_id: UUID) -> List[Dict[str, Any]]:
        """
        Get attendees for a specific event.
        
        Note: This method assumes attendee and person tables exist.
        If they don't exist in the current schema, this will return empty list.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            List of attendee dictionaries
        """
        # First check if the tables exist
        table_check_query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = 'attendee'
            ) as attendees_exists,
            EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = 'person'
            ) as person_exists
        """
        
        try:
            async with self.get_connection() as conn:
                table_check = await conn.fetchrow(table_check_query, self.tenant_schema)
                
                if not (table_check['attendees_exists'] and table_check['person_exists']):
                    logger.warning(f"Attendee or person table not found in schema {self.tenant_schema}")
                    return []
                
                query = """
                    SELECT 
                        a.person_id, a.event_id, a.added_date, a.role, a.status,
                        a.invited_from, a.created_at, a.updated_at,
                        p.name, p.email, p.profile_picture_url, p.is_internal_user
                    FROM attendee a
                    JOIN person p ON a.person_id = p.id
                    WHERE a.event_id = $1
                    ORDER BY a.added_date ASC
                """
                
                rows = await conn.fetch(query, event_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching attendees for event {event_id}: {str(e)}")
            # Return empty list instead of raising for missing tables
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_member_events(self, person_id: UUID, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get events a person has attended or registered for.
        
        Note: This method assumes attendee table exists.
        If it doesn't exist, this will return empty list.
        
        Args:
            person_id: The person's unique identifier
            days_back: Number of days to look back for events
            
        Returns:
            List of person's event participation
        """
        start_date = datetime.now() - timedelta(days=days_back)
        
        # First check if the attendee table exists
        table_check_query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = 'attendee'
            )
        """
        
        try:
            async with self.get_connection() as conn:
                table_exists = await conn.fetchval(table_check_query, self.tenant_schema)
                
                if not table_exists:
                    logger.warning(f"Attendee table not found in schema {self.tenant_schema}")
                    return []
                
                query = """
                    SELECT 
                        e.id, e.title, e.event_type_id, e.start_time, e.end_time,
                        a.status, a.added_date, a.role
                    FROM event e
                    JOIN attendee a ON e.id = a.event_id
                    WHERE a.person_id = $1
                        AND e.start_time >= $2
                    ORDER BY e.start_time DESC
                """
                
                rows = await conn.fetch(query, person_id, start_date)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching events for person {person_id}: {str(e)}")
            # Return empty list instead of raising for missing tables
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_event_by_id(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get event details by ID.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            Event data dictionary or None if not found
        """
        query = """
            SELECT 
                id, title, description, event_type_id, creator_id,
                start_time, end_time, start_date, end_date,
                is_all_day, is_same_day, venue_name, venue_address,
                meeting_link, meeting_room, visibility, status,
                recurrence_pattern, recurrence_end, event_ends, time_zone,
                banner_image, additional_info, "EventClass",
                individual_cal_id, team_cal_id, group_cal_id,
                created_at, updated_at
            FROM event 
            WHERE id = $1
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, event_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching event {event_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_events_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get events within a specific date range.
        
        Args:
            start_date: Start date for the range
            end_date: End date for the range
            
        Returns:
            List of event dictionaries within the date range
        """
        query = """
            SELECT 
                id, title, description, event_type_id, creator_id,
                start_time, end_time, start_date, end_date,
                is_all_day, is_same_day, venue_name, venue_address,
                meeting_link, meeting_room, visibility, status,
                recurrence_pattern, event_ends, time_zone,
                banner_image, additional_info, "EventClass",
                individual_cal_id, team_cal_id, group_cal_id,
                created_at, updated_at
            FROM event 
            WHERE start_time >= $1 AND start_time <= $2
                AND status = 1
            ORDER BY start_time ASC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, start_date, end_date)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching events by date range: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_recurring_events(self) -> List[Dict[str, Any]]:
        """
        Get all recurring events for the tenant.
        
        Returns:
            List of recurring event dictionaries
        """
        query = """
            SELECT 
                id, title, description, event_type_id, creator_id,
                start_time, end_time, start_date, end_date,
                is_all_day, is_same_day, venue_name, venue_address,
                meeting_link, meeting_room, visibility, status,
                recurrence_pattern, recurrence_end, event_ends, time_zone,
                banner_image, additional_info, "EventClass",
                individual_cal_id, team_cal_id, group_cal_id,
                created_at, updated_at
            FROM event 
            WHERE recurrence_pattern > 0
                AND status = 1
            ORDER BY start_time ASC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching recurring events: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_event_categories(self) -> List[Dict[str, Any]]:
        """
        Get all event categories for the tenant.
        
        Returns:
            List of event category dictionaries
        """
        # Check if event_type table exists
        table_check_query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = 'event_type'
            )
        """
        
        try:
            async with self.get_connection() as conn:
                table_exists = await conn.fetchval(table_check_query, self.tenant_schema)
                
                if not table_exists:
                    logger.warning(f"Event_type table not found in schema {self.tenant_schema}")
                    # Return default categories
                    return [
                        {'id': 1, 'name': 'Worship Service', 'description': 'Regular worship services'},
                        {'id': 2, 'name': 'Bible Study', 'description': 'Bible study sessions'},
                        {'id': 3, 'name': 'Community Event', 'description': 'Community outreach events'},
                        {'id': 4, 'name': 'Youth Ministry', 'description': 'Youth-focused events'},
                        {'id': 5, 'name': 'Prayer Meeting', 'description': 'Prayer and intercession meetings'}
                    ]
                
                query = """
                    SELECT id, name, description, created_at, updated_at
                    FROM event_type
                    ORDER BY name ASC
                """
                
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching event categories: {str(e)}")
            # Return default categories on error
            return [
                {'id': 1, 'name': 'Worship Service', 'description': 'Regular worship services'},
                {'id': 2, 'name': 'Bible Study', 'description': 'Bible study sessions'},
                {'id': 3, 'name': 'Community Event', 'description': 'Community outreach events'},
                {'id': 4, 'name': 'Youth Ministry', 'description': 'Youth-focused events'},
                {'id': 5, 'name': 'Prayer Meeting', 'description': 'Prayer and intercession meetings'}
            ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_events_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """
        Get all events for a specific category.
        
        Args:
            category_id: The event category/type ID
            
        Returns:
            List of event dictionaries for the category
        """
        query = """
            SELECT 
                id, title, description, event_type_id, creator_id,
                start_time, end_time, start_date, end_date,
                is_all_day, is_same_day, venue_name, venue_address,
                meeting_link, meeting_room, visibility, status,
                recurrence_pattern, event_ends, time_zone,
                banner_image, additional_info, "EventClass",
                individual_cal_id, team_cal_id, group_cal_id,
                created_at, updated_at
            FROM event 
            WHERE event_type_id = $1
                AND status = 1
            ORDER BY start_time DESC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, category_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching events for category {category_id}: {str(e)}")
            return []