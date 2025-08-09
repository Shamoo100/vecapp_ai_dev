"""
Connect Repository implementation for cross-service database access.

This repository provides direct database access to the Connect Service 
MongoDB database using database-per-tenant approach.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError
from tenacity import retry, stop_after_attempt, wait_exponential
from bson.codec_options import CodecOptions
from bson.binary import UuidRepresentation

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ConnectRepository:
    """
    Repository for connecting to the Connect Service MongoDB database.
    
    This repository provides direct database access to connection and relationship data
    using tenant-specific database naming convention for MongoDB multi-tenancy.
    """
    
    def __init__(self, tenant_identifier: str):
        """
        Initialize the connect repository with MongoDB client.
        
        Args:
            tenant_identifier: The tenant identifier for database naming
        """
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self.tenant_identifier = tenant_identifier
        self.connection_string = getattr(settings, 'CONNECT_SERVICE_MONGODB_URL', None)
        
        if not self.connection_string:
            logger.warning("CONNECT_SERVICE_MONGODB_URL not configured")
    
    async def initialize(self) -> None:
        """Initialize the MongoDB client and database connection."""
        if not self.connection_string:
            raise ValueError("Connect service MongoDB URL not configured")
            
        try:
            self._client = AsyncIOMotorClient(
                self.connection_string,
                connectTimeoutMS=30000,
                socketTimeoutMS=45000,
                serverSelectionTimeoutMS=30000,
                maxPoolSize=30,
                minPoolSize=5,
                heartbeatFrequencyMS=10000,
                retryWrites=True,
                retryReads=True
            )
            
            # Test the connection
            await self._client.admin.command('ping')
            logger.info(f"Connect service MongoDB connection established for tenant: {self.tenant_identifier}")
        except Exception as e:
            logger.error(f"Failed to connect to Connect service MongoDB: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close the MongoDB client connection."""
        if self._client:
            self._client.close()
            logger.info("Connect service MongoDB connection closed")
    
    async def get_tenant_connection(self, tenant_identifier: str) -> AsyncIOMotorDatabase:
        """
        Get a database connection for a specific tenant.
        
        Args:
            tenant_identifier: The tenant identifier for MongoDB database naming
            
        Returns:
            AsyncIOMotorDatabase instance for the tenant
        """
        if not self._client:
            await self.initialize()
        
        # Determine environment and construct database name using tenant identifier
        environment = 'prod' if getattr(settings, 'ENVIRONMENT', 'development') == 'prod' else 'dev'
        database_name = f"vecapp_{environment}_{tenant_identifier}"
        
        # Create proper CodecOptions instance with correct UuidRepresentation
        codec_options = CodecOptions(uuid_representation=UuidRepresentation.STANDARD)
        
        # Get database instance with proper codec options
        database = self._client.get_database(
            database_name,
            codec_options=codec_options
        )
        
        return database
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_person_connections(self, person_id: UUID, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get connections for a specific person.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB operations)
            
        Returns:
            List of connection documents
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.connections
            
            # Find connections where the person is either the initiator or recipient
            cursor = collection.find({
                "$or": [
                    {"person_id": str(person_id)},
                    {"connected_person_id": str(person_id)}
                ],
                "status": "active"
            })
            
            connections = await cursor.to_list(length=None)
            logger.debug(f"Found {len(connections)} connections for person {person_id} in tenant {tenant_identifier}")
            return connections
        except PyMongoError as e:
            logger.error(f"Error fetching connections for person {person_id} in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_interaction_history(self, person_id: UUID, tenant_identifier: str, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get interaction history for a person.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB operations)
            days_back: Number of days to look back for interactions
            
        Returns:
            List of interaction documents
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.interactions
            start_date = datetime.now() - timedelta(days=days_back)
            
            cursor = collection.find({
                "$or": [
                    {"initiator_id": str(person_id)},
                    {"recipient_id": str(person_id)}
                ],
                "interaction_date": {"$gte": start_date}
            }).sort("interaction_date", -1)
            
            interactions = await cursor.to_list(length=100)  # Limit to 100 recent interactions
            logger.debug(f"Found {len(interactions)} interactions for person {person_id} in tenant {tenant_identifier}")
            return interactions
        except PyMongoError as e:
            logger.error(f"Error fetching interactions for person {person_id} in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_public_groups(self, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get all public groups.
        Backend query: Group.find({privacy: "Public"})
        
        Args:
            tenant_identifier: The tenant identifier (required for MongoDB operations)
        
        Returns:
            List of public group documents
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.groups
            
            # Backend team query: Group.find({privacy: "Public"})
            cursor = collection.find({"privacy": "Public"})
            groups = await cursor.to_list(length=None)
            logger.debug(f"Found {len(groups)} public groups in tenant {tenant_identifier}")
            return groups
        except PyMongoError as e:
            logger.error(f"Error fetching public groups in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_all_teams(self, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get all teams.
        Backend query: Team.find()
        
        Args:
            tenant_identifier: The tenant identifier (required for MongoDB operations)
        
        Returns:
            List of team documents
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.teams
            
            # Backend team query: Team.find() - no filter, get all teams
            cursor = collection.find({})
            teams = await cursor.to_list(length=None)
            logger.debug(f"Found {len(teams)} teams in tenant {tenant_identifier}")
            return teams
        except PyMongoError as e:
            logger.error(f"Error fetching teams in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_group_connections(self, tenant_identifier: str, group_type: str = None) -> List[Dict[str, Any]]:
        """
        Get group connections and small group information.
        
        Args:
            tenant_identifier: The tenant identifier (required for MongoDB operations)
            group_type: Optional filter by group type
            
        Returns:
            List of group connection documents
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.groups
            
            query = {"status": "active"}
            
            if group_type:
                query["group_type"] = group_type
            
            cursor = collection.find(query)
            groups = await cursor.to_list(length=None)
            logger.debug(f"Found {len(groups)} group connections in tenant {tenant_identifier}")
            return groups
        except PyMongoError as e:
            logger.error(f"Error fetching group connections in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_person_groups(self, person_id: UUID, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get groups that a person belongs to.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB operations)
            
        Returns:
            List of group membership documents
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.group_memberships
            
            cursor = collection.find({
                "person_id": str(person_id),
                "status": "active"
            })
            
            memberships = await cursor.to_list(length=None)
            logger.debug(f"Found {len(memberships)} group memberships for person {person_id} in tenant {tenant_identifier}")
            return memberships
        except PyMongoError as e:
            logger.error(f"Error fetching groups for person {person_id} in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def create_interaction(self, interaction_data: Dict[str, Any], tenant_identifier: str) -> Dict[str, Any]:
        """
        Create a new interaction record.
        
        Args:
            interaction_data: Dictionary containing interaction information
            tenant_identifier: The tenant identifier (required for MongoDB operations)
            
        Returns:
            Created interaction document
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.interactions
            
            # Add timestamp if not provided
            if 'interaction_date' not in interaction_data:
                interaction_data['interaction_date'] = datetime.utcnow()
            
            result = await collection.insert_one(interaction_data)
            
            # Return the created document
            created_doc = await collection.find_one({"_id": result.inserted_id})
            logger.info(f"Created interaction {result.inserted_id} in tenant {tenant_identifier}")
            return created_doc
        except PyMongoError as e:
            logger.error(f"Error creating interaction in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_connection_strength(self, person_id: UUID, connected_person_id: UUID, tenant_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get connection strength metrics between two people.
        
        Args:
            person_id: The first person's unique identifier
            connected_person_id: The second person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB operations)
            
        Returns:
            Connection strength data or None if no connection exists
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.connections
            
            # Find the connection between the two people
            connection = await collection.find_one({
                "$or": [
                    {"person_id": str(person_id), "connected_person_id": str(connected_person_id)},
                    {"person_id": str(connected_person_id), "connected_person_id": str(person_id)}
                ],
                "status": "active"
            })
            
            if connection:
                logger.debug(f"Found connection between {person_id} and {connected_person_id} in tenant {tenant_identifier}")
            
            return connection
        except PyMongoError as e:
            logger.error(f"Error fetching connection strength in tenant {tenant_identifier}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_recent_interactions(self, person_id: UUID, tenant_identifier: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent interactions for a person.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (required for MongoDB operations)
            limit: Maximum number of interactions to return
            
        Returns:
            List of recent interaction documents
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for MongoDB operations")
            
            database = await self.get_tenant_connection(tenant_identifier)
            collection = database.interactions
            
            cursor = collection.find({
                "$or": [
                    {"initiator_id": str(person_id)},
                    {"recipient_id": str(person_id)}
                ]
            }).sort("interaction_date", -1).limit(limit)
            
            interactions = await cursor.to_list(length=limit)
            logger.debug(f"Found {len(interactions)} recent interactions for person {person_id} in tenant {tenant_identifier}")
            return interactions
        except PyMongoError as e:
            logger.error(f"Error fetching recent interactions for person {person_id} in tenant {tenant_identifier}: {str(e)}")
            raise
    
    async def health_check(self, tenant_identifier: str) -> Dict[str, Any]:
        """
        Perform health check on the MongoDB connection for a specific tenant.
        
        Args:
            tenant_identifier: The tenant identifier for health check context
            
        Returns:
            Health status information
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for health check")
            
            if not self._client:
                await self.initialize()
            
            # Test connection with a simple ping
            await self._client.admin.command('ping')
            
            # Test tenant-specific database access
            database = await self.get_tenant_connection(tenant_identifier)
            collections = await database.list_collection_names()
            
            return {
                'status': 'healthy',
                'service': 'connect_mongodb',
                'tenant_identifier': tenant_identifier,
                'collections_count': len(collections),
                'checked_at': datetime.utcnow()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'connect_mongodb',
                'tenant_identifier': tenant_identifier,
                'error': str(e),
                'checked_at': datetime.utcnow()
            }