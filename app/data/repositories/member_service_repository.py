"""
Member Repository implementation for cross-service database access.

This repository provides direct database access to the Member Service 
PostgreSQL database using schema-per-tenant approach.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import asyncpg
import json  # Add JSON import for JSONB serialization
from contextlib import asynccontextmanager
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from app.api.schemas.visitor_welcome_form import MemberBasicInfo, FamilyMemberInfo
from app.api.exceptions import DatabaseException

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MemberRepository:
    """
    Repository for connecting to the Member Service PostgreSQL database.
    
    This repository provides direct database access to member data using
    schema-per-tenant approach, bypassing SQS messaging for improved 
    performance and independence.
    """
    
    def __init__(self, schema_name: str):
        """
        Initialize the member repository with database connection pool.
        
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
                timeout=60.0,  # Increase timeout to handle slow connections
                statement_cache_size=0  # Disable statement cache to avoid issues
            )
            
            # Test the connection
            async with self.get_connection() as conn:
                # Verify we can switch to the schema
                await conn.execute(f"SET search_path TO {self.schema_name}")
                
            logger.info(f"Member service database connection pool created for schema: {self.schema_name}")
            
        except Exception as e:
            logger.error(f"Failed to create member service connection pool: {str(e)}")
            if self._pool:
                await self._pool.close()
            raise DatabaseException(f"Failed to initialize database connection: {str(e)}")
    
    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            try:
                await self._pool.close()
                logger.info("Member service database connection pool closed successfully")
            except Exception as e:
                logger.error(f"Error closing database connection pool: {str(e)}")
            finally:
                self._pool = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection with proper schema context."""
        if not self._pool:
            raise DatabaseException("Database connection pool not initialized")
            
        try:
            async with self._pool.acquire() as conn:
                # Always set search path first
                await conn.execute(f"SET search_path TO {self.schema_name}")
                yield conn
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"Database error in get_connection: {str(e)}")
            raise DatabaseException(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_connection: {str(e)}")
            raise DatabaseException(f"Connection error: {str(e)}")
    
    # ========================================
    # PROVISIONING-TIME SYNC REPOSITORY METHODS
    # ========================================

    # TODO: Repository methods to be implemented for already implemented interfaces
    # ========================================
    # PROVISIONING-TIME SYNC METHODS 
    # TODO: Repository methods to be implemented
    # ========================================
    # async def sync_person_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
    #     """
    #     Sync all person data for provisioning-time initialization.
        
    #     Args:
    #         tenant_schema: The tenant's schema name
            
    #     Returns:
    #         List of all person data dictionaries
    #     """
    #     ...
    
    # async def sync_family_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
    #     """
    #     Sync all family data for provisioning-time initialization.
        
    #     Args:
    #         tenant_schema: The tenant's schema name
            
    #     Returns:
    #         List of all family data dictionaries
    #     """
    #     ...
    
    # async def sync_user_types(self, tenant_schema: str) -> List[Dict[str, Any]]:
    #     """
    #     Sync all user types for provisioning-time initialization.
        
    #     Args:
    #         tenant_schema: The tenant's schema name
            
    #     Returns:
    #         List of user type dictionaries
    #     """
    #     ...
    
    # async def sync_user_status_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
    #     """
    #     Sync all user status data for provisioning-time initialization.
        
    #     Args:
    #         tenant_schema: The tenant's schema name
            
    #     Returns:
    #         List of user status dictionaries
    #     """
    #     ...
    
    # async def sync_task_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
    #     """
    #     Sync all task data for provisioning-time initialization.
        
    #     Args:
    #         tenant_schema: The tenant's schema name
            
    #     Returns:
    #         List of task data dictionaries
    #     """
    #     ...
    
    # async def sync_notes_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
    #     """
    #     Sync all notes data for provisioning-time initialization.
        
    #     Args:
    #         tenant_schema: The tenant's schema name
            
    #     Returns:
    #         List of notes data dictionaries
    #     """
    #     ...
# ========================================
# ON-DEMAND DATA PULLING REPOSITORY METHODS 
# ========================================
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
            WHERE p.user_type_id = 2 AND p.deleted_at IS NULL
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
    async def get_visitor_welcome_form_data(self, person_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get visitor welcome form data by person ID (on-demand).
        
        Args:
            person_id: The person's unique identifier
            
        Returns:
            Welcome form data dictionary containing person and family info, or None if not found
            
        Raises:
            ValueError: If the person ID is invalid
            DatabaseException: If there's a database error
        """
        query = """
            SELECT 
                -- Person information
                p.id as person_id, p.title, p.first_name, p.last_name, p.middle_name,
                p.email, p.phone, p.dob as date_of_birth, p.gender, p.race, 
                p.address, p.city, p.state, p.country, p.zip, p.how_join as how_heard_about_us, 
                p.joined_via, p.join_date, p.marital_status,
                p.preferred_comm_method as preferred_communication_method, 
                p.time_to_contact as best_contact_time,
                p.spiritual_need, p.spiritual_challenge,
                p.prayer_request, p.just_relocated as recently_relocated,
                p.consider_joining as considering_joining,p.joining_our_church,
                p.daily_devotional as receive_devotionals,
                p.feedback, p.profession as occupation,
                p.created_at, p.updated_at,
                
                -- Family information
                f.id as family_id, f.first_name as family_head_first_name,
                f.last_name as family_head_last_name, f.fam_address,
                f.fam_city, f.fam_state, f.fam_zip, f.fam_country,
                f.fam_country_code, f.fam_wedding_date, f.family_size,
                f.spouse_first_name, f.fam_entered_by, f.fam_last_edit_by,
                f.profile_pic as family_profile_pic,
                f.created_at as family_created_at,
                f.updated_at as family_updated_at
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.id = $1 
            AND p.deleted_at IS NULL
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, person_id)
                if row:
                    # Convert row to dictionary
                    data = dict(row)
                    
                    # # Handle None values and provide defaults for required fields
                    # processed_data = {}
                    # for key, value in data.items():
                    #     if value is None:
                    #         # Provide sensible defaults for None values
                    #         if key in ['race', 'address', 'prayer_request', 'feedback']:
                    #             processed_data[key] = ""
                    #         elif key in ['recently_relocated', 'considering_joining', 'receive_devotionals']:
                    #             processed_data[key] = "not_specified"
                    #         elif key == 'preferred_communication_method':
                    #             processed_data[key] = "not_specified"
                    #         elif key == 'best_contact_time':
                    #             processed_data[key] = "not_specified"
                    #         elif key == 'occupation':
                    #             processed_data[key] = "not_specified"
                    #         elif key == 'how_heard_about_us':
                    #             processed_data[key] = "not_specified"
                    #         elif key == 'marital_status':
                    #             processed_data[key] = "not_specified"
                    #         else:
                    #             processed_data[key] = value
                    #     else:
                    #         processed_data[key] = value
                    
                    return data
                return None
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"Database error fetching welcome form data for person {person_id}: {str(e)}")
            raise DatabaseException(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching welcome form data for person {person_id}: {str(e)}")
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
    async def get_family_members_profiles(self, member_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed profiles for multiple family members by their IDs.
        
        Args:
            member_ids: List of person IDs (as strings)
            
        Returns:
            List of detailed member profile dictionaries
        """
        if not member_ids:
            return []
            
        # Convert string IDs to UUIDs
        uuid_ids = []
        for member_id in member_ids:
            try:
                uuid_ids.append(UUID(member_id))
            except ValueError:
                logger.warning(f"Invalid UUID format for member_id: {member_id}")
                continue
        
        if not uuid_ids:
            return []
        
        # Create placeholders for the IN clause
        placeholders = ','.join(f'${i+1}' for i in range(len(uuid_ids)))
        
        query = f"""
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone, 
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.user_type_id, p.member_status, p.fam_id,
                f.first_name as family_head_first_name, f.last_name as family_head_last_name,
                p.how_join, p.joined_via, p.is_verified, p.has_account, p.relationship,
                p.employment_status, p.employer, p.profession, p.job_title,
                p.highest_qualification, p.school, p.course, p.is_graduated,
                p.spiritual_need, p.spiritual_challenge, p.prayer_request,
                p.created_at, p.updated_at, p.fam_id,
                f.first_name as family_head_first_name, f.last_name as family_head_last_name,
                f.fam_address, f.fam_city, f.fam_state, f.fam_country, f.fam_zip
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.id IN ({placeholders}) AND p.deleted_at IS NULL
            ORDER BY p.dob ASC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, *uuid_ids)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching family members profiles: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_new_family_data(self, tenant_schema: str, fam_id: UUID, family_head_id: UUID) -> List[Dict[str, Any]]:
        """
        Get new family data based on this scenerio : 1-family_context is individual,family_history is new, this means fam_id,fam_head_id = person_id
        
        Args:
            tenant_schema: The tenant's schema name
            fam_id: the family's unique identifier
            family_head_id: the family heads id to confirm it is the same as the newly added  fam_id a new family
            
        Returns:
            List of new family data dictionaries
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.user_type_id, p.member_status, p.fam_id,
                f.id as family_id, f.first_name as family_head_first_name, 
                f.last_name as family_head_last_name,
                f.fam_address, f.fam_city, f.fam_state, f.fam_country, f.fam_zip
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.fam_id = $1 
            AND f.id = p.id 
            AND p.id = $2 
            AND p.deleted_at IS NULL
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, fam_id, family_head_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching new family data for family {fam_id} and head {family_head_id}: {str(e)}")
            raise

    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_existing_family_data(self, tenant_schema: str, since: datetime) -> List[Dict[str, Any]]:
        """
        Get existing family data based on this scenario: family_context is individual, 
        family_history is existing, meaning fam_id exists and fam_head_id != person_id.
        this means context should tell ai that it is a new family member being added to an already existing family
        
        Args:
            tenant_schema: The tenant's schema name
            since: Timestamp to check for existing families since
            
        Returns:
            List of existing family data dictionaries
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.user_type_id, p.member_status, p.fam_id,
                f.id as family_id, f.first_name as family_head_first_name, 
                f.last_name as family_head_last_name,
                f.fam_address, f.fam_city, f.fam_state, f.fam_country, f.fam_zip
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.fam_id IS NOT NULL 
            AND f.id != p.id
            AND p.created_at >= $1
            AND p.deleted_at IS NULL
            ORDER BY p.created_at DESC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, since)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching existing family data since {since}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_new_individual_added_to_existing_family(self, tenant_schema: str, person_id: UUID, fam_id: UUID) -> Dict[str, Any]:
        """
        Get data for a new individual being added to an existing family where they are not the family head.
        
        Args:
            tenant_schema: The tenant's schema name
            person_id: The new individual's unique identifier
            family_id: The existing family's unique identifier
            
        Returns:
            Dictionary containing both the new individual's data and their associated existing family data
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.user_type_id, p.member_status, p.fam_id,
                f.id as family_id, f.first_name as family_head_first_name, 
                f.last_name as family_head_last_name,
                f.fam_address, f.fam_city, f.fam_state, f.fam_country, f.fam_zip
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.id = $1 
            AND p.fam_id = $2
            AND f.id != p.id
            AND p.deleted_at IS NULL
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, person_id, fam_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching data for new individual {person_id} in family {fam_id}: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_new_family_members_added_to_existing_family(self, tenant_schema: str, fam_id: UUID, since: datetime) -> List[Dict[str, Any]]:
        """
        Get data for both existing and new family members added to an existing family.
        
        Args:
            tenant_schema: The tenant's schema name
            family_id: The existing family's unique identifier
            since: Timestamp to check for new members added since
            
        Returns:
            List of dictionaries containing both existing and new family member data
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.user_type_id, p.member_status, p.fam_id, p.relationship,
                f.id as family_id, f.first_name as family_head_first_name, 
                f.last_name as family_head_last_name,
                f.fam_address, f.fam_city, f.fam_state, f.fam_country, f.fam_zip,
                p.created_at, p.updated_at
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.fam_id = $1 
            AND p.created_at >= $2
            AND p.deleted_at IS NULL
            ORDER BY p.created_at DESC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, fam_id, since)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching new family members for family {fam_id} since {since}: {str(e)}")
            raise
    

    #========= Notes ============
    
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
            WHERE n.recipient_id = $1
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
    async def get_notes_by_title_pattern(self, person_id: UUID, title_patterns: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notes for a person filtered by title patterns.
        
        Args:
            person_id: The person's unique identifier
            title_patterns: List of title patterns to match (case-insensitive)
            limit: Maximum number of notes to return
            
        Returns:
            List of filtered note data dictionaries
        """
        # Create ILIKE conditions for each pattern
        title_conditions = " OR ".join([f"LOWER(n.title) LIKE LOWER($%d)" % (i + 2) for i in range(len(title_patterns))])
        
        query = f"""
            SELECT 
                n.id, n.title, n.notes_body, n.note_link, n.note_photos,
                n.file_attachment, n.is_edited, n.is_archived,
                n.task_id, n.task_assignee_id, n.recipient_id, n.recipient_fam_id,
                n.created_at, n.updated_at
            FROM notes n
            WHERE n.recipient_id = $1 
                AND ({title_conditions})
                AND n.is_archived = false
            ORDER BY n.created_at DESC
            LIMIT ${len(title_patterns) + 2}
        """
        
        try:
            async with self.get_connection() as conn:
                # Prepare parameters: person_id + title patterns + limit
                params = [person_id] + [f"%{pattern}%" for pattern in title_patterns] + [limit]
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching notes by title patterns for person {person_id}: {str(e)}")
            raise

    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def create_note(self, note_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new note in the database.
        
        Args:
            note_data: Dictionary containing note information
            
        Returns:
            Created note data dictionary or None if creation failed
        """
        # TODO: meta should be JSONB
        query = """
            INSERT INTO notes (
                title, task_id, person_id, notes_body, note_link, note_photos,
                file_attachment, task_assignee_id, recipient_id, recipient_fam_id,type, meta
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            RETURNING id, title, notes_body, created_at, updated_at
        """
        
        try:
            # Serialize meta field to JSON string for JSONB column
            meta_value = note_data.get('meta')
            if meta_value is not None and isinstance(meta_value, dict):
                meta_json = json.dumps(meta_value)
            else:
                meta_json = meta_value
            
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
                    note_data.get('recipient_fam_id'),
                    note_data.get('type'),
                    meta_json  # Use serialized JSON string
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

# ========================================
# Task Repository Methods
# ========================================
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_updated_person_data(self, tenant_schema: str, person_id: UUID, since: datetime) -> List[Dict[str, Any]]:
        """
        Get person data updated since a specific timestamp (on-demand).
        
        Args:
            since: Timestamp to check for updates since
            
        Returns:
            List of updated person data dictionaries
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.user_type_id, p.member_status, p.fam_id,
                f.first_name as family_head_first_name, f.last_name as family_head_last_name,
                p.updated_at
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.id = $1 AND p.updated_at >= $2 AND p.deleted_at IS NULL
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, person_id, since)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching updated person data for {person_id} since {since}: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_updated_notes(self, tenant_schema: str, since: datetime) -> List[Dict[str, Any]]:
        """
        Get notes updated since a specific timestamp (on-demand).
        
        Args:
            since: Timestamp to check for updates since
            
        Returns:
            List of updated note dictionaries
        """
        query = """
            SELECT 
                n.id, n.title, n.notes_body, n.note_link, n.note_photos,
                n.file_attachment, n.is_edited, n.is_archived,
                n.task_id, n.task_assignee_id, n.recipient_id, n.recipient_fam_id,
                n.person_id, n.created_at, n.updated_at, n.meta
            FROM notes n
            WHERE n.updated_at >= $1
            ORDER BY n.updated_at DESC
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, since)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching updated notes since {since}: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_person_by_email(self, tenant_schema: str, email: str) -> Optional[Dict[str, Any]]:
        """
        Get person details by email address (on-demand).
        
        Args:
            email: The person's email address
            
        Returns:
            Person data dictionary or None if not found
        """
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.dob, p.gender, p.address, p.city, p.state, p.country, p.zip,
                p.marital_status, p.wedding_date, p.join_date, p.membership_date,
                p.user_type_id, p.member_status, p.fam_id,
                f.first_name as family_head_first_name, f.last_name as family_head_last_name
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE p.email = $1 AND p.deleted_at IS NULL
        """
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, email)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching person by email {email}: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def search_persons(self, tenant_schema: str, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for persons by name or other criteria (on-demand).
        
        Args:
            search_term: Search term for person lookup
            limit: Maximum number of results to return
            
        Returns:
            List of matching person data dictionaries
        """
        search_pattern = f"%{search_term}%"
        query = """
            SELECT 
                p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
                p.gender, p.city, p.state, p.user_type_id, p.member_status,
                f.first_name as family_head_first_name, f.last_name as family_head_last_name
            FROM person p
            LEFT JOIN fam f ON p.fam_id = f.id
            WHERE (
                p.first_name ILIKE $1 OR 
                p.last_name ILIKE $1 OR 
                p.email ILIKE $1 OR 
                p.phone ILIKE $1
            ) AND p.deleted_at IS NULL
            ORDER BY p.updated_at DESC
            LIMIT $2
        """
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, search_pattern, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error searching persons with term {search_term}: {str(e)}")
            raise



#archived implementation for get_family_members_profiles
    # @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    # async def get_family_members_profiles(self, member_ids: List[str]) -> List[Dict[str, Any]]:
    #     """
    #     Get detailed profiles for multiple family members by their IDs.
        
    #     Args:
    #         member_ids: List of person IDs (as strings for SQS compatibility)
            
    #     Returns:
    #         List of enhanced member profiles with family context
    #     """
    #     query = """
    #         SELECT 
    #             p.id, p.first_name, p.last_name, p.middle_name, p.email, p.phone,
    #             p.dob, p.gender, p.address, p.city, p.state, p.country,
    #             p.marital_status, p.relationship, p.user_type_id, p.member_status,
    #             f.id as family_id, f.first_name as family_head_first_name,
    #             f.last_name as family_head_last_name,
    #             f.fam_address, f.fam_city, f.fam_state, f.fam_country
    #         FROM person p
    #         LEFT JOIN fam f ON p.fam_id = f.id
    #         WHERE p.id = ANY($1::uuid[]) AND p.deleted_at IS NULL
    #     """
        
    #     try:
    #         async with self.get_connection() as conn:
    #             # Convert string IDs to UUID list
    #             uuid_list = [UUID(id_str) for id_str in member_ids]
    #             rows = await conn.fetch(query, uuid_list)
    #             return [dict(row) for row in rows]
    #     except Exception as e:
    #         logger.error(f"Error fetching family member profiles: {str(e)}")
    #         raise
    
   