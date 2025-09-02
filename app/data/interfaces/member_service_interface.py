"""
Interface for Member Service operations.

This interface defines the contract for accessing member data from 
the external Member Service database, supporting both provisioning-time 
sync and on-demand data pulling.
"""

from typing import Dict, Any, Optional, List, Protocol
from uuid import UUID
from datetime import datetime
from app.data.models.member_service_models import (
    FamilyMember,
    PersonProfile,
    PersonNote,
    FamilyProfile,
    FollowUpTask,
    PrayerRequest,
    PersonFeedback,
    PersonDecision,
    JourneyReportData,
)

#==== REPOSITORY INTERFACE ====
# This interface defines the contract for the repository layer that interacts with the database.
# It abstracts the data access logic and allows for easier testing and mocking.    
class IMemberRepository(Protocol):
    async def initialize(self) -> None: ...
    async def close(self) -> None: ...

    #person and family context methods
    async def get_person_by_id(self, person_id: UUID) -> Optional[PersonProfile]: 
        """Get person details by ID."""
        ...

    async def get_family_by_id(self, fam_id: UUID) -> Optional[FamilyProfile]: 
        """Get family details by family ID."""
        ...

    async def get_family_members(self, fam_id: UUID) -> List[FamilyMember]:
        """Get all family members for a given family ID."""
        ...

    async def get_family_members_profiles(self, member_ids: List[str]) -> List[PersonProfile]:
        """Get detailed profiles for multiple family members by their IDs."""
        ...
    
    
    # Visitors / Search
    async def get_visitors(self, limit: int = 500) -> List[PersonProfile]: 
        """Get all visitors (user_type_id = 1) from the person table."""
        ...

    async def get_recent_visitors(self, days: int = 30, limit: int = 100) -> List[PersonProfile]:
        """Get recent visitors within the specified number of days."""
        ...

    async def get_visitors_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PersonProfile]:
        """Get visitors within a specific date range."""
        ...

    async def get_person_by_email(self, email: str) -> Optional[PersonProfile]:             
        """Get person details by email address."""
        ...
    
    async def search_persons(self, search_term: str, limit: int = 50) -> List[PersonProfile]:
        """Search for persons by name or other criteria."""
    
        ...
    
    # Notes / Tasks / Changes
    async def get_person_notes(self, person_id: UUID, limit: int = 50) -> List[PersonNote]:
        """Get notes associated with a person."""
        ...  
    async def get_notes_by_title_pattern(self, person_id: UUID, title_patterns: List[str], limit: int = 50) -> List[PersonNote]: 
        """Get notes by title pattern for a person."""
        ...

    async def create_note(self, note_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new note in the notes table."""
        ...

    async def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """get tasks with task_id"""
        ...
    async def get_updated_person_data(self, person_id: UUID, since: datetime) -> List[PersonProfile]: 
        """Get person data updated since a specific timestamp."""
        ...
    async def get_updated_notes(self, since: datetime) -> List[PersonNote]: 
        """Get notes updated since a specific timestamp."""
        ...

    # Scenario queries (kept, but they return models)
    async def get_visitor_welcome_form_data(self, person_id: UUID) -> Optional[Dict[str, Any]]:
        """Get visitor welcome form data by person ID."""
        ...
    async def get_new_family_data(self, fam_id: UUID, family_head_id: UUID) -> List[PersonProfile]:
        """Get new family data based on the scenario where family_context is individual and family_history is new."""
        ...
    async def get_existing_family_data(self, since: datetime) -> List[PersonProfile]:
        """Get existing family data based on the scenario where family_context is individual and family_history is existing."""
        ...
    async def get_new_individual_added_to_existing_family(self, person_id: UUID, fam_id: UUID) -> Optional[PersonProfile]: ...




class IMemberService(Protocol):
    """
    Interface for member service operations.
    
    This service handles both provisioning-time data sync and on-demand 
    data pulling from the Member Service PostgreSQL database using 
    schema-per-tenant approach.
    """
    
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        ...
    
    async def close(self) -> None:
        """Close the database connection pool."""
        ...
    
    # ========================================
    # PROVISIONING-TIME SYNC METHODS 
    # TODO: Repository methods to be implemented
    # ========================================
    
    async def sync_person_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
        """
        Sync all person data for provisioning-time initialization.
        
        Args:
            tenant_schema: The tenant's schema name
            
        Returns:
            List of all person data dictionaries
        """
        ...
    
    async def sync_family_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
        """
        Sync all family data for provisioning-time initialization.
        
        Args:
            tenant_schema: The tenant's schema name
            
        Returns:
            List of all family data dictionaries
        """
        ...
    
    async def sync_user_types(self, tenant_schema: str) -> List[Dict[str, Any]]:
        """
        Sync all user types for provisioning-time initialization.
        
        Args:
            tenant_schema: The tenant's schema name
            
        Returns:
            List of user type dictionaries
        """
        ...
    
    async def sync_user_status_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
        """
        Sync all user status data for provisioning-time initialization.
        
        Args:
            tenant_schema: The tenant's schema name
            
        Returns:
            List of user status dictionaries
        """
        ...
    
    async def sync_task_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
        """
        Sync all task data for provisioning-time initialization.
        
        Args:
            tenant_schema: The tenant's schema name
            
        Returns:
            List of task data dictionaries
        """
        ...
    
    async def sync_notes_data(self, tenant_schema: str) -> List[Dict[str, Any]]:
        """
        Sync all notes data for provisioning-time initialization.
        
        Args:
            tenant_schema: The tenant's schema name
            
        Returns:
            List of notes data dictionaries
        """
        ...
    
    # ========================================
    # ON-DEMAND DATA PULLING METHODS
    # ========================================
    
    async def get_person_by_id(self, person_id: UUID) -> Optional[PersonProfile]:
        """
        Get person details by ID (on-demand).
        
        Args:
            person_id: The person's unique identifier
            
        Returns:
            Person data dictionary or None if not found
        """
        ...

    async def get_family_by_id(self, fam_id: UUID) -> Optional[FamilyProfile]:
        """
        Get family details by family ID (on-demand).
        
        Args:
            fam_id: The family's unique identifier
            
        Returns:
            Family data dictionary or None if not found
        """
        ...
    
    async def get_visitors(self, limit: int = 100) -> List[PersonProfile]:
        """
        Get all visitors (user_type_id = 1) from the person table (on-demand).
        
        Args:
            limit: Maximum number of visitors to return
            
        Returns:
            List of visitor data dictionaries
        """
        ...
    async def get_recent_visitors(self, days: int = 30, limit: int = 500) -> List[PersonProfile]:
        """
        Get recent visitors within the specified number of days (on-demand).
        
        Args:
            days: Number of days to look back
            limit: Maximum number of visitors to return
            
        Returns:
            List of recent visitor data dictionaries
        """
        ...
    async def get_visitors_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PersonProfile]:
        """
        Get visitors within a specific date range (on-demand).
        
        Args:
            start_date: Start date for the range
            end_date: End date for the range
            
        Returns:
            List of visitor data dictionaries within the date range
        """
        ...

    async def get_visitor_welcome_form_data(self, person_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get visitor welcome form data by person ID (on-demand).
        
        Args:
            person_id: The person's unique identifier
            
        Returns:
            Welcome form data dictionary or None if not found
        """
        ...

    async def get_family_members_profiles(self, member_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed profiles for multiple family members by their IDs.
        
        Args:
            member_ids: List of person IDs (as strings for SQS compatibility)
            
        Returns:
            List of enhanced member profiles with family context
        """
        ...
    
    async def get_family_members(self, fam_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all family members for a given family ID (on-demand).
        
        Args:
            fam_id: The family's unique identifier
            
        Returns:
            List of family member data dictionaries

        ##this will also suffice for this scenerio
        3-family_context is family, family_history is new, this means the new fam_id,
        fam_head_id = person_id and other family members will be queried by fam_id
        """
        ...
    
    async def get_new_family_data(self,fam_id: UUID, family_head_id: UUID) -> List[Dict[str, Any]]:
        """
        Get new family data based on this scenerio : 1-family_context is individual,family_history is new, this means fam_id,fam_head_id = person_id
        
        Args:
            tenant_schema: The tenant's schema name
            fam_id: the family's unique identifier
            family_head_id: the family heads id to confirm it is the same as the newly added  fam_id a new family
            
        Returns:
            List of new family data dictionaries
        """
        ...

    async def get_existing_family_data(self, since: datetime) -> List[Dict[str, Any]]:
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
        ...
    
    async def get_new_individual_added_to_existing_family(self, person_id: UUID, fam_id: UUID) -> Dict[str, Any]:
        """
        Get data for a new individual being added to an existing family where they are not the family head.
        
        Args:
            tenant_schema: The tenant's schema name
            person_id: The new individual's unique identifier
            family_id: The existing family's unique identifier
            
        Returns:
            Dictionary containing both the new individual's data and their associated existing family data
        """
        ...

    async def get_new_family_members_added_to_existing_family(self, fam_id: UUID, since: datetime) -> List[Dict[str, Any]]:
        """
        Get data for both existing and new family members added to an existing family.
        
        Args:
            tenant_schema: The tenant's schema name
            family_id: The existing family's unique identifier
            since: Timestamp to check for new members added since
            
        Returns:
            List of dictionaries containing both existing and new family member data
        """
        ...

    async def get_person_notes(self, person_id: UUID, limit: int = 50) -> List[PersonNote]:
        """
        Get notes associated with a person (on-demand).
        
        Args:
            person_id: The person's unique identifier
            limit: Maximum number of notes to return
            
        Returns:
            List of note data dictionaries
        """
        ...
    
    async def create_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new note in the notes table.
        
        Args:
            note_data: Dictionary containing note information
            
        Returns:
            Created note data dictionary
        """
        ...
    
    async def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get task details by ID (on-demand).
        
        Args:
            task_id: The task's unique identifier
            
        Returns:
            Task data dictionary or None if not found
        """
        ...
    
    async def get_task_assignees(self, task_id: int) -> List[Dict[str, Any]]:
        """
        Get assignees for a specific task (on-demand).
        
        Args:
            task_id: The task's unique identifier
            
        Returns:
            List of assignee data dictionaries
        """
        ...

    async def get_updated_person_data(self, person_id: UUID, since: datetime) -> List[PersonProfile]:
        """
        Get person data updated since a specific timestamp (on-demand).
        
        Args:
            since: Timestamp to check for updates since
            
        Returns:
            List of updated person data dictionaries
        """
        ...
    
    async def get_updated_notes(self, since: datetime) -> List[PersonNote]:
        """
        Get notes updated since a specific timestamp (on-demand).
        
        Args:
            since: Timestamp to check for updates since
            
        Returns:
            List of updated note dictionaries
        """
        ...
    
    async def get_person_by_email(self, email: str) -> Optional[PersonProfile]:
        """
        Get person details by email address (on-demand).
        
        Args:
            email: The person's email address
            
        Returns:
            Person data dictionary or None if not found
        """
        ...
    
    async def search_persons(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for persons by name or other criteria (on-demand).
        
        Args:
            search_term: Search term for person lookup
            limit: Maximum number of results to return
            
        Returns:
            List of matching person data dictionaries
        """
        ...

    # Journey Report Data Collection Methods
    async def get_person_follow_up_tasks(self, person_id: UUID, limit: int = 100) -> List[FollowUpTask]:
        """Get all follow-up tasks for a person with assignees and feedback."""
        ...
    
    async def get_family_follow_up_tasks(self, fam_id: UUID, limit: int = 100) -> List[FollowUpTask]:
        """Get all follow-up tasks for a family with assignees and feedback."""
        ...
    
    async def get_person_prayer_requests(self, person_id: UUID) -> List[PrayerRequest]:
        """Get prayer requests for a person."""
        ...
    
    async def get_person_feedback(self, person_id: UUID) -> List[PersonFeedback]:
        """Get feedback entries for a person."""
        ...
    
    async def get_person_decisions(self, person_id: UUID) -> List[PersonDecision]:
        """Get decision data for a person."""
        ...
    
    async def get_journey_report_data(self, person_id: UUID, date_range: Optional[tuple] = None) -> JourneyReportData:
        """Get comprehensive journey report data for a person."""
        ...
    
    async def get_family_journey_report_data(self, fam_id: UUID, date_range: Optional[tuple] = None) -> List[JourneyReportData]:
        """Get comprehensive journey report data for all family members."""
        ...
    
    async def get_visitors_journey_data(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[JourneyReportData]:
        """Get journey report data for visitors within a date range."""
        ...