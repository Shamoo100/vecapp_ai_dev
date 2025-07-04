"""Core messaging module for VecApp AI Service."""

from typing import Any, Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class MessageQueue:
    """Basic message queue implementation for internal messaging."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self._queue = asyncio.Queue()
        self._subscribers = []
        
    async def publish(self, message: Dict[str, Any], topic: Optional[str] = None):
        """Publish a message to the queue."""
        try:
            await self._queue.put({"topic": topic, "data": message})
            logger.debug(f"Message published to queue {self.name}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            
    async def subscribe(self, callback, topic: Optional[str] = None):
        """Subscribe to messages from the queue."""
        self._subscribers.append({"callback": callback, "topic": topic})
        
    async def consume(self):
        """Consume messages from the queue."""
        while True:
            try:
                message = await self._queue.get()
                for subscriber in self._subscribers:
                    if subscriber["topic"] is None or subscriber["topic"] == message["topic"]:
                        await subscriber["callback"](message["data"])
                self._queue.task_done()
            except Exception as e:
                logger.error(f"Error consuming message: {e}")
                
    def size(self) -> int:
        """Get the current queue size."""
        return self._queue.qsize()
        
    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()