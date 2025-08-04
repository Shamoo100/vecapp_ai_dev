"""
Interface for Member Service operations.

This interface defines the contract for accessing member data from 
the external Member Service database, supporting both provisioning-time 
sync and on-demand data pulling.
"""

from typing import Dict, Any, Optional, List, Protocol
from uuid import UUID
from datetime import datetime


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
    
    async def get_person_by_id(self, person_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get person details by ID (on-demand).
        
        Args:
            person_id: The person's unique identifier
            
        Returns:
            Person data dictionary or None if not found
        """
        ...
    
    async def get_visitors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all visitors (user_type_id = 1) from the person table (on-demand).
        
        Args:
            limit: Maximum number of visitors to return
            
        Returns:
            List of visitor data dictionaries
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
        ...

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
        ...
    
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
        ...

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
        ...

    async def get_person_notes(self, tenant_schema: str, person_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notes associated with a person (on-demand).
        
        Args:
            person_id: The person's unique identifier
            limit: Maximum number of notes to return
            
        Returns:
            List of note data dictionaries
        """
        ...
    
    async def create_note(self, tenant_schema: str, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new note in the notes table.
        
        Args:
            note_data: Dictionary containing note information
            
        Returns:
            Created note data dictionary
        """
        ...
    
    async def get_recent_visitors(self, tenant_schema: str, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent visitors within the specified number of days (on-demand).
        
        Args:
            days: Number of days to look back
            limit: Maximum number of visitors to return
            
        Returns:
            List of recent visitor data dictionaries
        """
        ...
    
    async def get_task_by_id(self, tenant_schema: str, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get task details by ID (on-demand).
        
        Args:
            task_id: The task's unique identifier
            
        Returns:
            Task data dictionary or None if not found
        """
        ...
    
    async def get_updated_person_data(self, tenant_schema: str, person_id: UUID, since: datetime) -> List[Dict[str, Any]]:
        """
        Get person data updated since a specific timestamp (on-demand).
        
        Args:
            since: Timestamp to check for updates since
            
        Returns:
            List of updated person data dictionaries
        """
        ...
    
    async def get_updated_notes(self, tenant_schema: str, since: datetime) -> List[Dict[str, Any]]:
        """
        Get notes updated since a specific timestamp (on-demand).
        
        Args:
            since: Timestamp to check for updates since
            
        Returns:
            List of updated note dictionaries
        """
        ...
    
    async def get_person_by_email(self, tenant_schema: str, email: str) -> Optional[Dict[str, Any]]:
        """
        Get person details by email address (on-demand).
        
        Args:
            email: The person's email address
            
        Returns:
            Person data dictionary or None if not found
        """
        ...
    
    async def search_persons(self, tenant_schema: str, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for persons by name or other criteria (on-demand).
        
        Args:
            search_term: Search term for person lookup
            limit: Maximum number of results to return
            
        Returns:
            List of matching person data dictionaries
        """
        ...
    
    


# Legacy interface for backward compatibility
class IMemberRepository(IMemberService):
    """
    Legacy interface for member repository operations.
    
    This interface is maintained for backward compatibility.
    New implementations should use IMemberService.
    """
    pass