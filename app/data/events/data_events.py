from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

class DataEventType(str, Enum):
    """Types of data events that can be published"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"

class DataEvent(BaseModel):
    """Base class for all data events"""
    event_type: DataEventType
    entity_type: str
    entity_id: UUID
    tenant_id: UUID
    timestamp: datetime = datetime.utcnow()
    data: Dict[str, Any] = {}
    user_id: Optional[UUID] = None

class DataEventPublisher:
    """Publishes data events to message broker"""
    
    @staticmethod
    async def publish(event: DataEvent):
        """Publish a data event
        
        Args:
            event: The event to publish
        """
        # Implementation depends on your message broker (RabbitMQ, Kafka, etc.)
        # For now, just log the event
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Data event published: {event.model_dump_json()}")
        
        # TODO: Implement actual message broker integration