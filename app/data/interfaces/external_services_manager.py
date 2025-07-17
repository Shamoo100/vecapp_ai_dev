from typing import Optional
from uuid import UUID
import logging
from contextlib import asynccontextmanager

from app.services.member_service import MemberService
from app.services.calendar_service import CalendarService
from app.services.connect_service import ConnectService

logger = logging.getLogger(__name__)

class ExternalServicesManager:
    """
    Manager for all external database services.
    
    This class provides a centralized way to manage connections
    to all external databases and ensures proper initialization
    and cleanup of resources.
    """
    
    def __init__(self):
        """Initialize the services manager."""
        self.member_service: Optional[MemberService] = None
        self.calendar_service: Optional[CalendarService] = None
        self.connect_service: Optional[ConnectService] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all external services."""
        if self._initialized:
            return
            
        try:
            # Initialize Member Service
            self.member_service = MemberService()
            await self.member_service.initialize()
            
            # Initialize Calendar Service
            self.calendar_service = CalendarService()
            await self.calendar_service.initialize()
            
            # Initialize Connect Service
            self.connect_service = ConnectService()
            await self.connect_service.initialize()
            
            self._initialized = True
            logger.info("All external services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize external services: {str(e)}")
            await self.close()
            raise
    
    async def close(self) -> None:
        """Close all external service connections."""
        if self.member_service:
            await self.member_service.close()
        
        if self.calendar_service:
            await self.calendar_service.close()
        
        if self.connect_service:
            await self.connect_service.close()
        
        self._initialized = False
        logger.info("All external services closed")
    
    @asynccontextmanager
    async def get_services(self):
        """Context manager for getting all services."""
        if not self._initialized:
            await self.initialize()
        
        try:
            yield {
                'member': self.member_service,
                'calendar': self.calendar_service,
                'connect': self.connect_service
            }
        finally:
            # Services remain open for reuse
            pass

# Global instance
external_services = ExternalServicesManager()