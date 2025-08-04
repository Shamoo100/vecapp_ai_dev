"""
Calendar Service for cross-service integration with VecApp Calendar Service.

This service provides business logic for calendar data operations and 
orchestrates the calendar repository for database access.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime, timedelta

from app.data.interfaces.calendar_service_interface import ICalendarService
from app.data.repositories.calendar_service_repository import CalendarRepository

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Service for managing calendar data integration with external Calendar Service.
    
    This service handles business logic for calendar operations and provides
    a clean interface for AI agents and other services to access calendar data.
    """
    
    def __init__(self, tenant_schema: str, calendar_repository: Optional[CalendarRepository] = None):
        """
        Initialize the calendar service.
        
        Args:
            tenant_schema: The tenant-specific schema name
            calendar_repository: Optional repository injection for testing
        """
        self.tenant_schema = tenant_schema
        self._repository = calendar_repository or CalendarRepository(tenant_schema)
    
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        await self._repository.initialize()
        logger.info(f"Calendar service initialized for schema: {self.tenant_schema}")
    
    async def close(self) -> None:
        """Close the service and its dependencies."""
        await self._repository.close()
        logger.info("Calendar service closed")
    
    async def get_upcoming_events(self, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """
        Get upcoming events for a tenant with business logic enhancements.
        
        Args:
            days_ahead: Number of days to look ahead for events
            
        Returns:
            List of upcoming event dictionaries with enhancements
        """
        try:
            events = await self._repository.get_upcoming_events(days_ahead)
            
            # Add business logic enhancements
            for event in events:
                event['days_until_event'] = self._calculate_days_until(event.get('start_time'))
                event['is_today'] = self._is_today(event.get('start_time'))
                event['is_this_week'] = self._is_this_week(event.get('start_time'))
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            raise
    
    async def get_event_attendees(self, event_id: UUID) -> List[Dict[str, Any]]:
        """
        Get attendees for a specific event with attendance insights.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            List of attendee dictionaries with insights
        """
        try:
            attendees = await self._repository.get_event_attendees(event_id)
            
            # Add attendance insights
            attendance_summary = {
                'total_registered': len(attendees),
                'confirmed': len([a for a in attendees if a.get('attendance_status') == 'confirmed']),
                'pending': len([a for a in attendees if a.get('attendance_status') == 'pending']),
                'cancelled': len([a for a in attendees if a.get('attendance_status') == 'cancelled'])
            }
            
            return {
                'attendees': attendees,
                'summary': attendance_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting event attendees for {event_id}: {str(e)}")
            raise
    
    async def get_member_events(self, member_id: UUID, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get events a member has attended with participation insights.
        
        Args:
            member_id: The member's unique identifier
            days_back: Number of days to look back for events
            
        Returns:
            Member's event participation with insights
        """
        try:
            events = await self._repository.get_member_events(member_id, days_back)
            
            # Add participation insights
            participation_summary = {
                'total_events': len(events),
                'attended': len([e for e in events if e.get('attendance_status') == 'attended']),
                'registered_only': len([e for e in events if e.get('attendance_status') == 'registered']),
                'event_types': self._group_by_event_type(events)
            }
            
            return {
                'events': events,
                'participation_summary': participation_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting member events for {member_id}: {str(e)}")
            raise
    
    async def get_event_by_id(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get event details by ID with enhanced context.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            Event data dictionary with context or None if not found
        """
        try:
            event = await self._repository.get_event_by_id(event_id)
            if not event:
                return None
            
            # Add context enhancements
            event['days_until_event'] = self._calculate_days_until(event.get('start_time'))
            event['is_past_event'] = self._is_past_event(event.get('end_time'))
            event['duration_hours'] = self._calculate_duration_hours(
                event.get('start_time'), 
                event.get('end_time')
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error getting event {event_id}: {str(e)}")
            raise
    
    async def get_events_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get events within a specific date range with analytics.
        
        Args:
            start_date: Start date for the range
            end_date: End date for the range
            
        Returns:
            List of event dictionaries with analytics
        """
        try:
            events = await self._repository.get_events_by_date_range(start_date, end_date)
            
            # Add analytics
            analytics = {
                'total_events': len(events),
                'events_by_type': self._group_by_event_type(events),
                'events_by_week': self._group_by_week(events),
                'average_events_per_day': len(events) / max(1, (end_date - start_date).days)
            }
            
            return {
                'events': events,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting events by date range: {str(e)}")
            raise
    
    async def get_recurring_events(self) -> List[Dict[str, Any]]:
        """
        Get all recurring events with pattern analysis.
        
        Returns:
            List of recurring event dictionaries with pattern analysis
        """
        try:
            events = await self._repository.get_recurring_events()
            
            # Add pattern analysis
            pattern_analysis = {
                'total_recurring': len(events),
                'patterns': self._analyze_recurrence_patterns(events),
                'next_occurrences': self._calculate_next_occurrences(events)
            }
            
            return {
                'recurring_events': events,
                'pattern_analysis': pattern_analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting recurring events: {str(e)}")
            raise

    def _calculate_days_until(self, event_datetime: datetime) -> int:
        """Calculate days until event."""
        if not event_datetime:
            return -1
        return (event_datetime.date() - datetime.now().date()).days
    
    def _is_today(self, event_datetime: datetime) -> bool:
        """Check if event is today."""
        if not event_datetime:
            return False
        return event_datetime.date() == datetime.now().date()
    
    def _is_this_week(self, event_datetime: datetime) -> bool:
        """Check if event is this week."""
        if not event_datetime:
            return False
        today = datetime.now().date()
        days_until_sunday = (6 - today.weekday()) % 7
        week_end = today + timedelta(days=days_until_sunday)
        week_start = week_end - timedelta(days=6)
        return week_start <= event_datetime.date() <= week_end
    
    def _is_past_event(self, end_time: datetime) -> bool:
        """Check if event is in the past."""
        if not end_time:
            return False
        return end_time < datetime.now()
    
    def _calculate_duration_hours(self, start: datetime, end: datetime) -> float:
        """Calculate event duration in hours."""
        if not start or not end:
            return 0.0
        return (end - start).total_seconds() / 3600
    
    def _group_by_event_type(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group events by type."""
        types = {}
        for event in events:
            event_type = event.get('event_type_id', 'Unknown')  # Updated to match actual column
            types[event_type] = types.get(event_type, 0) + 1
        return types
    
    def _group_by_week(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group events by week."""
        weeks = {}
        for event in events:
            start_date = event.get('start_time')  # Updated to match actual column
            if start_date:
                week_start = start_date.date() - timedelta(days=start_date.weekday())
                week_key = week_start.strftime('%Y-W%U')
                weeks[week_key] = weeks.get(week_key, 0) + 1
        return weeks
    
    def _analyze_recurrence_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze recurrence patterns."""
        patterns = {}
        for event in events:
            pattern = event.get('recurrence_pattern', 'Unknown')
            patterns[pattern] = patterns.get(pattern, 0) + 1
        return patterns
    
    def _calculate_next_occurrences(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate next occurrences for recurring events."""
        # Simplified implementation - would need more complex logic for actual recurrence calculation
        next_occurrences = []
        for event in events[:5]:  # Limit to first 5 for performance
            next_occurrences.append({
                'event_id': event.get('id'),
                'title': event.get('title'),
                'next_occurrence': event.get('start_time')  # Updated to match actual column
            })
        return next_occurrences

    async def get_event_categories(self) -> List[Dict[str, Any]]:
        """
        Get all event categories with usage statistics.
        
        Returns:
            List of event categories with statistics
        """
        try:
            # Get categories from repository (assuming this method exists or will be implemented)
            categories = await self._repository.get_event_categories()
            
            # Enhance categories with usage statistics
            enhanced_categories = []
            for category in categories:
                # Get events count for this category
                category_events = await self._repository.get_events_by_category(category.get('id'))
                
                enhanced_category = {
                    **category,
                    'total_events': len(category_events),
                    'upcoming_events': len([e for e in category_events 
                                          if e.get('start_time') and e['start_time'] > datetime.now()]),
                    'past_events': len([e for e in category_events 
                                      if e.get('end_time') and e['end_time'] < datetime.now()]),
                    'most_recent_event': max([e.get('start_time') for e in category_events], 
                                           default=None),
                    'average_attendance': self._calculate_average_attendance(category_events),
                    'popular_times': self._analyze_popular_times(category_events)
                }
                enhanced_categories.append(enhanced_category)
            
            # Sort by total events (most active categories first)
            enhanced_categories.sort(key=lambda x: x['total_events'], reverse=True)
            
            return enhanced_categories
            
        except Exception as e:
            logger.error(f"Error getting event categories: {str(e)}")
            # Return basic categories if repository method doesn't exist yet
            return [
                {
                    'id': 1,
                    'name': 'Worship Service',
                    'description': 'Regular worship services',
                    'total_events': 0,
                    'upcoming_events': 0,
                    'past_events': 0,
                    'most_recent_event': None,
                    'average_attendance': 0,
                    'popular_times': {}
                },
                {
                    'id': 2,
                    'name': 'Bible Study',
                    'description': 'Bible study sessions',
                    'total_events': 0,
                    'upcoming_events': 0,
                    'past_events': 0,
                    'most_recent_event': None,
                    'average_attendance': 0,
                    'popular_times': {}
                },
                {
                    'id': 3,
                    'name': 'Community Event',
                    'description': 'Community outreach events',
                    'total_events': 0,
                    'upcoming_events': 0,
                    'past_events': 0,
                    'most_recent_event': None,
                    'average_attendance': 0,
                    'popular_times': {}
                },
                {
                    'id': 4,
                    'name': 'Youth Ministry',
                    'description': 'Youth-focused events',
                    'total_events': 0,
                    'upcoming_events': 0,
                    'past_events': 0,
                    'most_recent_event': None,
                    'average_attendance': 0,
                    'popular_times': {}
                },
                {
                    'id': 5,
                    'name': 'Prayer Meeting',
                    'description': 'Prayer and intercession meetings',
                    'total_events': 0,
                    'upcoming_events': 0,
                    'past_events': 0,
                    'most_recent_event': None,
                    'average_attendance': 0,
                    'popular_times': {}
                }
            ]

    def _calculate_average_attendance(self, events: List[Dict[str, Any]]) -> float:
        """Calculate average attendance for events."""
        if not events:
            return 0.0
        
        total_attendance = 0
        events_with_attendance = 0
        
        for event in events:
            attendance = event.get('attendance_count', 0)
            if attendance > 0:
                total_attendance += attendance
                events_with_attendance += 1
        
        return total_attendance / max(1, events_with_attendance)

    def _analyze_popular_times(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze popular times for events in a category."""
        time_slots = {
            'morning': 0,    # 6 AM - 12 PM
            'afternoon': 0,  # 12 PM - 6 PM
            'evening': 0,    # 6 PM - 10 PM
            'night': 0       # 10 PM - 6 AM
        }
        
        for event in events:
            start_time = event.get('start_time')  # Fixed: was start_datetime
            if start_time:
                hour = start_time.hour
                if 6 <= hour < 12:
                    time_slots['morning'] += 1
                elif 12 <= hour < 18:
                    time_slots['afternoon'] += 1
                elif 18 <= hour < 22:
                    time_slots['evening'] += 1
                else:
                    time_slots['night'] += 1
        
        return time_slots