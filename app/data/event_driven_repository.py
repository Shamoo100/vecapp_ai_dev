from typing import Dict, Any, Optional, List, Type
from uuid import UUID
from app.data.base_repository import BaseRepository
from app.data.events.data_events import DataEvent, DataEventType, DataEventPublisher

class EventDrivenRepository(BaseRepository):
    """Repository that publishes events on data changes"""
    
    def __init__(self, table_name: str, entity_type: str):
        """Initialize the repository
        
        Args:
            table_name: Name of the database table
            entity_type: Type of entity this repository manages
        """
        super().__init__(table_name)
        self.entity_type = entity_type
        self.event_publisher = DataEventPublisher()
    
    async def create(self, data: Dict[str, Any], tenant_id: Optional[UUID] = None) -> str:
        """Create a record and publish a creation event"""
        entity_id = await super().create(data, tenant_id)
        
        # Publish creation event
        event = DataEvent(
            event_type=DataEventType.CREATED,
            entity_type=self.entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            data=data,
            user_id=data.get('created_by')
        )
        await self.event_publisher.publish(event)
        
        return entity_id
    
    async def update(self, id: UUID, data: Dict[str, Any], tenant_id: Optional[UUID] = None) -> bool:
        """Update a record and publish an update event"""
        success = await super().update(id, data, tenant_id)
        
        if success:
            # Publish update event
            event = DataEvent(
                event_type=DataEventType.UPDATED,
                entity_type=self.entity_type,
                entity_id=id,
                tenant_id=tenant_id,
                data=data,
                user_id=data.get('updated_by')
            )
            await self.event_publisher.publish(event)
        
        return success
    
    async def delete(self, id: UUID, tenant_id: Optional[UUID] = None) -> bool:
        """Delete a record and publish a deletion event"""
        # Get the entity before deletion to include in event
        entity = await self.get_by_id(id, tenant_id)
        
        success = await super().delete(id, tenant_id)
        
        if success and entity:
            # Publish deletion event
            event = DataEvent(
                event_type=DataEventType.DELETED,
                entity_type=self.entity_type,
                entity_id=id,
                tenant_id=tenant_id,
                data=entity,
                user_id=entity.get('deleted_by')
            )
            await self.event_publisher.publish(event)
        
        return success