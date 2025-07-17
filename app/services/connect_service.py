from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from tenacity import retry, stop_after_attempt, wait_exponential
from pymongo.errors import PyMongoError

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ConnectService:
    """
    Service for connecting to the Connect Service MongoDB database.
    
    This service provides direct database access to connection and relationship data
    using tenant-specific database collections, enabling the AI service to understand 
    member connections and interactions.
    """
    
    def __init__(self, tenant_schema: str):
        """Initialize the connect service with MongoDB client.
        
        Args:
            tenant_schema: The tenant-specific schema/database identifier
        """
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self.tenant_schema = tenant_schema
        self.connection_string = getattr(settings, 'CONNECT_SERVICE_MONGODB_URL', None)
        # Use tenant schema as database name for MongoDB multi-tenancy
        self.database_name = f"connect_{tenant_schema}"
        
        if not self.connection_string:
            logger.warning("CONNECT_SERVICE_MONGODB_URL not configured")
    
    async def initialize(self) -> None:
        """Initialize the MongoDB client and database connection."""
        if not self.connection_string:
            raise ValueError("Connect service MongoDB URL not configured")
            
        try:
            self._client = AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=10,
                minPoolSize=2,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
            )
            self._database = self._client[self.database_name]
            
            # Test the connection
            await self._client.admin.command('ping')
            logger.info(f"Connect service MongoDB connection established for tenant: {self.tenant_schema}")
        except Exception as e:
            logger.error(f"Failed to connect to Connect service MongoDB: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close the MongoDB client connection."""
        if self._client:
            self._client.close()
            logger.info("Connect service MongoDB connection closed")
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if not self._database:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._database
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_person_connections(self, person_id: UUID) -> List[Dict[str, Any]]:
        """
        Get connections for a specific person.
        
        Args:
            person_id: The person's unique identifier
            
        Returns:
            List of connection documents
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.connections
            
            # Find connections where the person is either the initiator or recipient
            cursor = collection.find({
                "$or": [
                    {"person_id": str(person_id)},
                    {"connected_person_id": str(person_id)}
                ],
                "status": "active"
            })
            
            connections = await cursor.to_list(length=None)
            return connections
        except PyMongoError as e:
            logger.error(f"Error fetching connections for person {person_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_interaction_history(self, person_id: UUID, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get interaction history for a person.
        
        Args:
            person_id: The person's unique identifier
            days_back: Number of days to look back for interactions
            
        Returns:
            List of interaction documents
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.interactions
            start_date = datetime.now() - timedelta(days=days_back)
            
            cursor = collection.find({
                "$or": [
                    {"initiator_id": str(person_id)},
                    {"recipient_id": str(person_id)}
                ],
                "interaction_date": {"$gte": start_date}
            }).sort("interaction_date", -1)
            
            interactions = await cursor.to_list(length=100)  # Limit to 100 recent interactions
            return interactions
        except PyMongoError as e:
            logger.error(f"Error fetching interactions for person {person_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_group_connections(self, group_type: str = None) -> List[Dict[str, Any]]:
        """
        Get group connections and small group information.
        
        Args:
            group_type: Optional filter by group type
            
        Returns:
            List of group connection documents
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.groups
            
            query = {"status": "active"}
            
            if group_type:
                query["group_type"] = group_type
            
            cursor = collection.find(query)
            groups = await cursor.to_list(length=None)
            return groups
        except PyMongoError as e:
            logger.error(f"Error fetching group connections: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_person_groups(self, person_id: UUID) -> List[Dict[str, Any]]:
        """
        Get groups that a person belongs to.
        
        Args:
            person_id: The person's unique identifier
            
        Returns:
            List of group membership documents
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.group_memberships
            
            cursor = collection.find({
                "person_id": str(person_id),
                "status": "active"
            })
            
            memberships = await cursor.to_list(length=None)
            return memberships
        except PyMongoError as e:
            logger.error(f"Error fetching groups for person {person_id}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def create_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new interaction record.
        
        Args:
            interaction_data: Dictionary containing interaction information
            
        Returns:
            Created interaction document
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.interactions
            
            # Add timestamp if not provided
            if "interaction_date" not in interaction_data:
                interaction_data["interaction_date"] = datetime.now()
            
            result = await collection.insert_one(interaction_data)
            
            # Return the created document
            created_doc = await collection.find_one({"_id": result.inserted_id})
            return created_doc
        except PyMongoError as e:
            logger.error(f"Error creating interaction: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_connection_strength(self, person_id: UUID, connected_person_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get connection strength metrics between two people.
        
        Args:
            person_id: The first person's unique identifier
            connected_person_id: The second person's unique identifier
            
        Returns:
            Connection strength data or None if no connection exists
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.connection_metrics
            
            # Look for connection in both directions
            connection = await collection.find_one({
                "$or": [
                    {"person_id": str(person_id), "connected_person_id": str(connected_person_id)},
                    {"person_id": str(connected_person_id), "connected_person_id": str(person_id)}
                ]
            })
            
            return connection
        except PyMongoError as e:
            logger.error(f"Error fetching connection strength: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_church_teams(self) -> List[Dict[str, Any]]:
        """
        Get all active church teams.
        
        Returns:
            List of team documents
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.teams
            
            cursor = collection.find({"status": "active"})
            teams = await cursor.to_list(length=None)
            return teams
        except PyMongoError as e:
            logger.error(f"Error fetching church teams: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_church_groups(self) -> List[Dict[str, Any]]:
        """
        Get all active church groups.
        
        Returns:
            List of group documents
        """
        try:
            if not self._database:
                await self.initialize()
            
            collection = self.database.groups
            
            cursor = collection.find({"status": "active"})
            groups = await cursor.to_list(length=None)
            return groups
        except PyMongoError as e:
            logger.error(f"Error fetching church groups: {str(e)}")
            raise