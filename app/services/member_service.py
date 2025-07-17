from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncpg
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MemberService:
    """
    Service for connecting to the Member Service PostgreSQL database.
    
    This service provides direct database access to member data using
    schema-per-tenant approach, bypassing SQS messaging for improved 
    performance and independence.
    """
    
    def __init__(self, schema_name: str):
        """Initialize the member service with database connection pool.
        
        Args:
            schema_name: The tenant-specific schema name
        """
        self._pool: Optional[asyncpg.Pool] = None
        self.schema_name = schema_name
        self.db_url = getattr(settings, 'MEMBER_SERVICE_DATABASE_URL', None)
        
        if not self.db_url:
            logger.warning("MEMBER_SERVICE_DATABASE_URL not configured")
    
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if not self.db_url:
            raise ValueError("Member service database URL not configured")
            
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.db_url,
                min_size=2,
                max_size=10,
                command_timeout=30.0,
                max_inactive_connection_lifetime=300.0,
            )
            logger.info(f"Member service database connection pool created for schema: {self.schema_name}")
        except Exception as e:
            logger.error(f"Failed to create member service connection pool: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Member service database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool with schema context."""
        if not self._pool:
            await self.initialize()
            
        async with self._pool.acquire() as conn:
            # Set the search path to the tenant schema
            await conn.execute(f"SET search_path TO {self.schema_name}")
            yield conn
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_person_by_id(self, person_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get person details by ID.
        
        Args:
            person_id: The person's unique identifier
            
        Returns:
            Person data dictionary or None if not found
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone, 
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.baptism_date, p.conversion_date, p.user_type_id, p.member_status,
                p.how_join, p.joined_via, p.is_verified, p.has_account,
                p.employment_status, p.employer, p.profession, p.job_title,
                p.highest_qualification, p.school, p.course, p.is_graduated,
                p.spiritual_need, p.spiritual_challenge, p.prayer_request,
                p.created_at, p.updated_at, p.fam_id,
                f.first_name as family_head_first_name, f.last_name as family_head_last_name,
                f.fam_address, f.fam_city, f.fam_state, f.fam_country, f.fam_zip
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.id = $1 AND p.deleted_at IS NULL
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, person_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching person {person_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_visitors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all visitors (user_type_id = 1) from the person table.
        
        Args:
            limit: Maximum number of visitors to return
            
        Returns:
            List of visitor data dictionaries
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state, p.country,
                p.how_join, p.joined_via, p.join_date, p.created_at,
                p.fam_id, p.member_status,
                f.first_name as family_head_first_name, f.last_name as family_head_last_name
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.user_type_id = 1 AND p.deleted_at IS NULL
            ORDER BY p.created_at DESC
            LIMIT $1
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching visitors: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_family_members(self, fam_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all family members for a given family ID.
        
        Args:
            fam_id: The family's unique identifier
            
        Returns:
            List of family member data dictionaries
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.dob, p.gender, p.relationship, p.user_type_id, p.member_status,
                p.created_at, p.updated_at
            FROM person p
            WHERE p.fam_id = $1 AND p.deleted_at IS NULL
            ORDER BY p.dob ASC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, fam_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching family members for family {fam_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_person_notes(self, person_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notes associated with a person.
        
        Args:
            person_id: The person's unique identifier
            limit: Maximum number of notes to return
            
        Returns:
            List of note data dictionaries
        """
        query = """
            SELECT 
                n.id, n.title, n.notes_body, n.note_link, n.note_photos,
                n.file_attachment, n.is_edited, n.is_archived,
                n.task_id, n.task_assignee_id, n.recipient_id, n.recipient_fam_id,
                n.created_at, n.updated_at
            FROM notes n
            WHERE n.person_id = $1
            ORDER BY n.created_at DESC
            LIMIT $2
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, person_id, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching notes for person {person_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def create_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new note in the notes table.
        
        Args:
            note_data: Dictionary containing note information
            
        Returns:
            Created note data dictionary
        """
        query = """
            INSERT INTO notes (
                title, task_id, person_id, notes_body, note_link, note_photos,
                file_attachment, task_assignee_id, recipient_id, recipient_fam_id, meta
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
            RETURNING id, title, notes_body, created_at, updated_at
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    query,
                    note_data.get('title'),
                    note_data.get('task_id'),
                    note_data.get('person_id'),
                    note_data.get('notes_body'),
                    note_data.get('note_link'),
                    note_data.get('note_photos'),
                    note_data.get('file_attachment'),
                    note_data.get('task_assignee_id'),
                    note_data.get('recipient_id'),
                    note_data.get('recipient_fam_id')
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_recent_visitors(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent visitors within the specified number of days.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of visitors to return
            
        Returns:
            List of recent visitor data dictionaries
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state,
                p.how_join, p.joined_via, p.join_date, p.created_at,
                p.fam_id, p.member_status
            FROM person p
            WHERE p.user_type_id = 1 
                AND p.deleted_at IS NULL
                AND p.created_at >= NOW() - INTERVAL '%s days'
            ORDER BY p.created_at DESC
            LIMIT $1
        """ % days
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching recent visitors: {str(e)}")
            raise


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get task details by ID.
        
        Args:
            task_id: The task's unique identifier
            
        Returns:
            Task data dictionary or None if not found
        """
        query = """
            SELECT 
                id, process_id, created_by, task_title, task_description, 
                task_type, task_status, task_resolution, task_priority,
                task_planned_startdate, task_planned_starttime,
                task_planned_enddate, task_planned_endtime,
                task_actual_startdatetime, task_actual_enddatetime,
                to_do_task_notification_frequency, to_do_task_notification_frequency_days,
                in_prog_task_notification_frequency, in_prog_task_notification_frequency_days,
                pastdue_task_notification_frequency, pastdue_task_notification_frequency_days,
                is_archived, follow_up_prev_task, routed_to, recipient_id,
                assign_usertype, follow_up_user, task_type_flag,
                created_at, updated_at, task_planned_startdatetime,
                task_planned_enddatetime, tenant_id, is_past_due_date
            FROM task
            WHERE id = $1
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, task_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching task {task_id}: {str(e)}")
            raise