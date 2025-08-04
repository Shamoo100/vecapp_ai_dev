"""
Interface for Calendar Service operations.

This interface defines the contract for on-demand calendar data access from 
the external Calendar Service database.
"""

from typing import Dict, Any, Optional, List, Protocol
from uuid import UUID
from datetime import datetime


class ICalendarService(Protocol):
    """
    Interface for calendar service operations.
    
    This service handles on-demand data pulling from the Calendar Service
    PostgreSQL database for real-time event and scheduling information.
    
    The tenant_schema is set during initialization and used internally.
    """
    
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        ...
    
    async def close(self) -> None:
        """Close the database connection pool."""
        ...
    
    async def get_upcoming_events(self, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """
        Get upcoming events for a tenant.
        
        Args:
            days_ahead: Number of days to look ahead for events
            
        Returns:
            List of upcoming event dictionaries
        """
        ...
    
    async def get_event_attendees(self, event_id: UUID) -> List[Dict[str, Any]]:
        """
        Get attendees for a specific event.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            List of attendee dictionaries
        """
        ...
    
    async def get_member_events(self, member_id: UUID, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get events a member has attended or registered for.
        
        Args:
            member_id: The member's unique identifier as id:uuid in the table
            days_back: Number of days to look back for events
            
        Returns:
            List of member's event participation
        """
        ...
    
    async def get_event_by_id(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get event details by ID.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            Event data dictionary or None if not found
        """
        ...
    
    async def get_events_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get events within a specific date range.
        
        Args:
            start_date: Start date for the range
            end_date: End date for the range
            
        Returns:
            List of event dictionaries within the date range
        """
        ...
    
    async def get_recurring_events(self) -> List[Dict[str, Any]]:
        """
        Get all recurring events for a tenant.
        
        Returns:
            List of recurring event dictionaries
        """
        ...

    async def get_event_categories(self) -> List[Dict[str, Any]]:
        """
        Get all event categories with usage statistics.
        
        Returns:
            List of event categories with statistics
        """
        ...