"""
Interface for Connect Service operations.

This interface defines the contract for on-demand connection data access from 
the external Connect Service MongoDB database with proper tenant handling.
"""

from typing import Dict, Any, Optional, List, Protocol
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorDatabase


class IConnectService(Protocol):
    """
    Interface for connect service operations.
    
    This service handles on-demand data pulling from the Connect Service
    MongoDB database for real-time connection and relationship information.
    MongoDB uses database naming convention (vecapp_env_tenant) for multi-tenancy.
    """
    
    async def initialize(self) -> None:
        """Initialize the MongoDB client and database connection."""
        ...
    
    async def close(self) -> None:
        """Close the MongoDB client connection."""
        ...
    
    async def get_tenant_connection(self, tenant_identifier: str) -> AsyncIOMotorDatabase:
        """
        Get a database connection for a specific tenant.
        
        Args:
            tenant_identifier: The tenant identifier for MongoDB database naming
            
        Returns:
            AsyncIOMotorDatabase instance for the tenant
        """
        ...
    
    async def get_person_connections(self, person_id: UUID, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get connections for a specific person.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB)
            
        Returns:
            List of connection documents
        """
        ...
    
    async def get_interaction_history(self, person_id: UUID, tenant_identifier: str, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get interaction history for a person.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB)
            days_back: Number of days to look back for interactions
            
        Returns:
            List of interaction documents
        """
        ...
    
    async def get_public_groups(self, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get all public groups.
        
        Args:
            tenant_identifier: The tenant identifier (required for MongoDB)
        
        Returns:
            List of public group documents
        """
        ...
    
    # Removed get_public_teams since all teams are private in VecApp
    
    async def get_all_teams(self, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get all teams (all teams are private in VecApp).
        
        Args:
            tenant_identifier: The tenant identifier (required for MongoDB)
        
        Returns:
            List of team documents
        """
        ...
    
    async def get_group_connections(self, tenant_identifier: str, group_type: str = None) -> List[Dict[str, Any]]:
        """
        Get group connections and small group information.
        
        Args:
            tenant_identifier: The tenant identifier (required for MongoDB)
            group_type: Optional filter by group type
            
        Returns:
            List of group connection documents
        """
        ...
    
    async def get_person_groups(self, person_id: UUID, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get groups that a person belongs to.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB)
            
        Returns:
            List of group membership documents
        """
        ...
    
    async def create_interaction(self, interaction_data: Dict[str, Any], tenant_identifier: str) -> Dict[str, Any]:
        """
        Create a new interaction record.
        
        Args:
            interaction_data: Dictionary containing interaction information
            tenant_identifier: The tenant identifier (required for MongoDB)
            
        Returns:
            Created interaction document
        """
        ...
    
    async def get_connection_strength(self, person_id: UUID, connected_person_id: UUID, tenant_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get connection strength metrics between two people.
        
        Args:
            person_id: The first person's unique identifier
            connected_person_id: The second person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB)
            
        Returns:
            Connection strength data or None if no connection exists
        """
        ...
    
    async def get_recent_interactions(self, person_id: UUID, tenant_identifier: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent interactions for a person.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB)
            limit: Maximum number of interactions to return
            
        Returns:
            List of recent interaction documents
        """
        ...
    
    async def health_check(self, tenant_identifier: str) -> Dict[str, Any]:
        """
        Perform health check on the MongoDB connection for a specific tenant.
        
        Args:
            tenant_identifier: The tenant identifier for health check context
            
        Returns:
            Health status information
        """
        ...