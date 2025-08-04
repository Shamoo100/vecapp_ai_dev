"""
Simplified Visitor Context Builder for AI Follow-up Notes.
Consolidates family scenario resolution and data collection rules.
Direct SQS data-driven context generation for accurate AI note generation.
"""
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import logging

from app.api.schemas.event_schemas import (
    VisitorEventData, 
    FamilyScenario, 
    VisitorContextData
)
from app.services.member_service import MemberService
from app.services.calendar_service import CalendarService
from app.services.connect_service import ConnectService

logger = logging.getLogger(__name__)


class VisitorContextBuilder:
    """
    Context-aware visitor context builder that stores event data and services
    within the instance for cleaner, more maintainable data collection methods.
    """
    
    def __init__(self, event_data: Optional[VisitorEventData] = None, schema_name: Optional[str] = None):
        """
        Initialize the visitor context builder with optional context data.
        
        Args:
            event_data: The visitor event data from SQS (optional for testing)
            schema_name: The tenant schema name (optional for testing)
        """
        self.event_data = event_data
        self.schema_name = schema_name
        self.member_service: Optional[MemberService] = None
        self.calendar_service: Optional[CalendarService] = None
        self.connect_service: Optional[ConnectService] = None
        self.tenant_identifier: Optional[str] = None
    
    def _initialize_services(self, schema_name: str) -> None:
        """Initialize all required services for the given schema."""
        self.schema_name = schema_name
        self.member_service = MemberService(schema_name=schema_name)
        self.calendar_service = CalendarService(tenant_schema=schema_name)
        
        # Extract tenant identifier from schema name (remove 'tenant_' prefix) specifically for connect service
        self.tenant_identifier = schema_name.replace('tenant_', '') if schema_name.startswith('tenant_') else schema_name
        self.connect_service = ConnectService(tenant_identifier=self.tenant_identifier)

    async def _initialize_service_connections(self) -> None:
        """Initialize database connections for all services."""
        try:
            if self.member_service:
                await self.member_service.initialize()
            if self.calendar_service:
                await self.calendar_service.initialize()
            if self.connect_service:
                await self.connect_service.initialize()
            logger.info(f"All services initialized for schema: {self.schema_name}")
        except Exception as e:
            logger.error(f"Error initializing service connections: {str(e)}")
            raise

    
    async def _cleanup_services(self) -> None:
        """Clean up service connections."""
        try:
            if self.member_service:
                await self.member_service.close()
            if self.calendar_service:
                await self.calendar_service.close()
            if self.connect_service:
                await self.connect_service.close()
        except Exception as e:
            logger.warning(f"Error during service cleanup: {str(e)}")

    async def build_context(self, event_data: VisitorEventData) -> VisitorContextData:
        """
        Build visitor context directly from SQS event data.
        Uses family_context and family_history to determine data collection strategy.
        
        Args:
            event_data: The visitor event data from SQS
            
        Returns:
            VisitorContextData: Complete context for AI note generation
        """
        try:
            # Store event data in instance
            self.event_data = event_data
            
            # Derive schema name from tenant
            schema_name = event_data.tenant
            
            # Initialize services
            self._initialize_services(schema_name)
            
            # Initialize database connections
            await self._initialize_service_connections()
            
            # Create family scenario from event data
            scenario_info = FamilyScenario.from_visitor_event(event_data)
            logger.info(f"Resolved scenario: {scenario_info.scenario_type} for person {event_data.person_id}")
            
            # Collect data based on scenario
            collected_data = await self._collect_scenario_based_data(scenario_info.scenario_type)
            
            # Build final context structure
            visitor_context = VisitorContextData(
                # Primary visitor data (required fields)
                visitor_profile=collected_data.get("primary_visitor", {}),
                visitor_welcome_form=collected_data.get("visitor_welcome_form_data", {}),
                
                # Family and relationship data
                family_members=collected_data.get("family_members", []),
                
                # Historical and engagement data
                first_timer_notes=collected_data.get("first_timer_notes", []),
                prayer_requests=collected_data.get("prayer_requests", []),
                existing_followup_notes=collected_data.get("existing_followup_notes", []),
                feedback_fields=collected_data.get("feedback_fields", []),
                
                # Public tenant data for recommendations
                public_teams=collected_data.get("public_teams", []),
                public_groups=collected_data.get("public_groups", []),
                upcoming_events=collected_data.get("upcoming_events", []),
                
                # Metadata (required field)
                scenario_info=scenario_info
            )
            
            logger.info(f"Successfully built context for scenario: {scenario_info.scenario_type}")
            return visitor_context
            
        except Exception as e:
            logger.error(f"Error building visitor context: {str(e)}")
            return self._build_fallback_context(event_data, str(e))
        finally:
            # Clean up services
            await self._cleanup_services()
    
    def _resolve_family_scenario(self, event_data: VisitorEventData) -> str:
        """
        Resolve family scenario directly from event data.
        Uses the family_context and family_history to determine scenario.
        """
        # Use family_context to determine scenario
        family_context = event_data.family_context or "individual"
        
        # Determine scenario based on event data
        if event_data.fam_id and event_data.new_family_members_id:
            if len(event_data.new_family_members_id) > 1:
                return "new_family_multiple_members"
            else:
                return "new_family_single_member"
        elif event_data.fam_id and not event_data.new_family_members_id:
            return "existing_family_new_member"
        elif not event_data.fam_id:
            return "individual_visitor"
        else:
            return "unknown_scenario"
    
    async def _collect_scenario_based_data(self, scenario: str) -> Dict[str, Any]:
        """
        Collect data based on the resolved scenario.
        Each scenario has specific data requirements.
        """
        if not self.event_data or not self.member_service:
            raise ValueError("Event data and services must be initialized before collecting data")
        
        # Collect data in parallel
        tasks = []
        
        # Always collect primary visitor data
        tasks.append(("primary_visitor", self._collect_primary_visitor_data()))
        
        # Always collect comprehensive visitor welcome form data (primary data source)
        tasks.append(("visitor_welcome_form_data", self._collect_visitor_welcome_form_data()))
        
        # Scenario-specific data collection
        if scenario in ["new_family_multiple_members", "new_family_single_member"]:
            # New family scenarios
            tasks.extend([
                ("family_members", self._collect_family_members_data(
                    self.event_data.new_family_members_id or [self.event_data.person_id]
                )),
                ("first_timer_notes", self._collect_first_timer_notes()),
                ("prayer_requests", self._collect_prayer_requests())
            ])
        elif scenario == "existing_family_new_member":
            # Existing family with new member
            family_member_ids = [self.event_data.person_id]
            if self.event_data.fam_head_id:
                family_member_ids.append(self.event_data.fam_head_id)
            
            tasks.extend([
                ("family_members", self._collect_family_members_data(family_member_ids)),
                ("existing_followup_notes", self._collect_existing_followup_notes()),
                ("prayer_requests", self._collect_prayer_requests())
            ])
        else:
            # Individual visitor or unknown scenario
            tasks.extend([
                ("first_timer_notes", self._collect_first_timer_notes()),
                ("prayer_requests", self._collect_prayer_requests())
            ])
        
        # Always collect feedback fields
        tasks.append(("feedback_fields", self._collect_feedback_fields()))
        
        # Always collect public data for recommendations (with tenant context)
        tasks.extend([
            ("public_teams", self._collect_public_teams()),
            ("public_groups", self._collect_public_groups()),
            ("upcoming_events", self._collect_upcoming_events())
        ])
        
        # Execute all tasks in parallel
        results = {}
        if tasks:
            task_results = await asyncio.gather(
                *[task for _, task in tasks], 
                return_exceptions=True
            )
            
            # Process results
            for i, (data_type, _) in enumerate(tasks):
                result = task_results[i]
                if isinstance(result, Exception):
                    logger.error(f"Error collecting {data_type}: {str(result)}")
                    results[data_type] = [] if data_type.endswith('s') else {}
                else:
                    results[data_type] = result or ([] if data_type.endswith('s') else {})
        
        return results
    
    async def _collect_primary_visitor_data(self, person_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect primary visitor profile data.
        
        Args:
            person_id: Optional person ID (for testing). Uses event_data.person_id if not provided.
        """
        try:
            target_person_id = person_id or (self.event_data.person_id if self.event_data else None)
            if not target_person_id:
                raise ValueError("Person ID is required")
            
            if not self.member_service:
                # For testing without full context
                if self.schema_name:
                    self.member_service = MemberService(schema_name=self.schema_name)
                else:
                    raise ValueError("Member service not initialized")
            
            return await self.member_service.get_member_profile(target_person_id) or {}
        except Exception as e:
            logger.error(f"Error collecting primary visitor data: {str(e)}")
            return {}

    async def _collect_visitor_welcome_form_data(self, person_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect visitor welcome form data.
        
        Args:
            person_id: Optional person ID (for testing). Uses event_data.person_id if not provided.
        """
        try:
            target_person_id = person_id or (self.event_data.person_id if self.event_data else None)
            if not target_person_id:
                raise ValueError("Person ID is required")
            
            if not self.member_service:
                # For testing without full context
                if self.schema_name:
                    self.member_service = MemberService(schema_name=self.schema_name)
                else:
                    raise ValueError("Member service not initialized")
            
            return await self.member_service.get_visitor_welcome_form_data(target_person_id) or {}
        except Exception as e:
            logger.error(f"Error collecting visitor welcome form data: {str(e)}")
            return {}
    
    async def _collect_family_members_data(self, family_member_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Collect family members data for context.
        
        Args:
            family_member_ids: Optional list of family member IDs. Uses event data if not provided.
        """
        try:
            if not family_member_ids:
                if self.event_data and self.event_data.new_family_members_id:
                    family_member_ids = self.event_data.new_family_members_id
                else:
                    return []
            
            if not self.member_service:
                raise ValueError("Member service not initialized")
            
            # Use the member service to get family member profiles
            family_profiles = []
            for member_id in family_member_ids:
                profile = await self.member_service.get_member_profile(member_id)
                if profile:
                    family_profiles.append(profile)
            
            return family_profiles
        except Exception as e:
            logger.warning(f"Could not collect family members data: {str(e)}")
            return []
    
    async def _collect_prayer_requests(self, person_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Collect prayer requests from both existing notes and welcome form data.
        
        Args:
            person_id: Optional person ID (for testing). Uses event_data.person_id if not provided.
        """
        try:
            target_person_id = person_id or (self.event_data.person_id if self.event_data else None)
            if not target_person_id or not self.member_service:
                return []
            
            prayer_requests = []
            
            # First, try to get existing prayer request notes
            existing_prayers = await self.member_service.get_prayer_requests(target_person_id) or []
            prayer_requests.extend(existing_prayers)
            
            # Extract prayer requests from welcome form data
            welcome_form_data = await self.member_service.get_visitor_welcome_form_data(target_person_id)
            
            if welcome_form_data and welcome_form_data.get('spiritual_info'):
                spiritual_info = welcome_form_data['spiritual_info']
                form_metadata = welcome_form_data.get('form_metadata', {})
                
                prayer_text = spiritual_info.get('prayer_request', '').strip() if spiritual_info.get('prayer_request') else ''
                if prayer_text:
                    prayer_requests.append({
                        'id': f"welcome_form_prayer_{target_person_id}",
                        'title': 'Prayer Request from Welcome Form',
                        'notes_body': prayer_text,
                        'request_type': 'prayer',
                        'source': 'welcome_form',
                        'created_at': form_metadata.get('created_at'),
                        'urgency': 'normal',
                        'category': 'general'
                    })
            
            return prayer_requests
            
        except Exception as e:
            logger.error(f"Error collecting prayer requests: {str(e)}")
            return []
    
    async def _collect_feedback_fields(self, person_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Collect feedback from both existing notes and welcome form data.
        
        Args:
            person_id: Optional person ID (for testing). Uses event_data.person_id if not provided.
        """
        try:
            target_person_id = person_id or (self.event_data.person_id if self.event_data else None)
            if not target_person_id or not self.member_service:
                return []
            
            feedback_data = []
            
            # First, try to get existing feedback notes
            existing_feedback = await self.member_service.get_feedback_fields(target_person_id) or []
            feedback_data.extend(existing_feedback)
            
            # Extract feedback from welcome form data
            welcome_form_data = await self.member_service.get_visitor_welcome_form_data(target_person_id)
            
            if welcome_form_data and welcome_form_data.get('spiritual_info'):
                spiritual_info = welcome_form_data['spiritual_info']
                form_metadata = welcome_form_data.get('form_metadata', {})
                
                # Extract main feedback field
                feedback_text = spiritual_info.get('feedback', '').strip() if spiritual_info.get('feedback') else ''
                if feedback_text:
                    feedback_data.append({
                        'id': f"welcome_form_feedback_{target_person_id}",
                        'title': 'General Feedback from Welcome Form',
                        'notes_body': feedback_text,
                        'feedback_type': 'general_feedback',
                        'source': 'welcome_form',
                        'created_at': form_metadata.get('created_at'),
                        'sentiment': 'positive',
                        'note_type': 'feedback'
                    })
                
                # Extract spiritual needs as feedback
                spiritual_need = spiritual_info.get('spiritual_need', '').strip() if spiritual_info.get('spiritual_need') else ''
                if spiritual_need:
                    feedback_data.append({
                        'id': f"welcome_form_spiritual_need_{target_person_id}",
                        'title': 'Spiritual Need from Welcome Form',
                        'notes_body': spiritual_need,
                        'feedback_type': 'spiritual_feedback',
                        'source': 'welcome_form',
                        'created_at': form_metadata.get('created_at'),
                        'sentiment': 'neutral',
                        'note_type': 'spiritual_need'
                    })
                
                # Extract spiritual challenges as feedback
                spiritual_challenge = spiritual_info.get('spiritual_challenge', '').strip() if spiritual_info.get('spiritual_challenge') else ''
                if spiritual_challenge:
                    feedback_data.append({
                        'id': f"welcome_form_spiritual_challenge_{target_person_id}",
                        'title': 'Spiritual Challenge from Welcome Form',
                        'notes_body': spiritual_challenge,
                        'feedback_type': 'spiritual_feedback',
                        'source': 'welcome_form',
                        'created_at': form_metadata.get('created_at'),
                        'sentiment': 'neutral',
                        'note_type': 'spiritual_challenge'
                    })
            
            return feedback_data
            
        except Exception as e:
            logger.error(f"Error collecting feedback fields: {str(e)}")
            return []

    async def _collect_first_timer_notes(self, person_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Collect first timer notes from both existing notes and welcome form insights.
        
        Args:
            person_id: Optional person ID (for testing). Uses event_data.person_id if not provided.
        """
        try:
            target_person_id = person_id or (self.event_data.person_id if self.event_data else None)
            if not target_person_id or not self.member_service:
                return []
            
            first_timer_notes = []
            
            # First, try to get existing first-timer notes
            existing_notes = await self.member_service.get_first_timer_notes(target_person_id) or []
            first_timer_notes.extend(existing_notes)
            
            # Create comprehensive first-timer note from welcome form data
            welcome_form_data = await self.member_service.get_visitor_welcome_form_data(target_person_id)
            
            if welcome_form_data:
                first_timer_insights = []
                
                # Extract data from structured sections
                visit_info = welcome_form_data.get('visit_info', {})
                interests = welcome_form_data.get('interests', {})
                spiritual_info = welcome_form_data.get('spiritual_info', {})
                form_metadata = welcome_form_data.get('form_metadata', {})
                
                # How they heard about the church
                how_heard = visit_info.get('how_heard_about_church', '').strip() if visit_info.get('how_heard_about_church') else ''
                if how_heard and how_heard.lower() not in ['none', 'other', 'not_specified', '']:
                    first_timer_insights.append(f"Heard about church through: {how_heard}")
                
                # Contact preferences
                best_contact_time = visit_info.get('best_contact_time', '').strip() if visit_info.get('best_contact_time') else ''
                if best_contact_time and best_contact_time.lower() not in ['none', '']:
                    first_timer_insights.append(f"Best contact time: {best_contact_time}")
                
                preferred_communication = visit_info.get('preferred_communication_method', '').strip() if visit_info.get('preferred_communication_method') else ''
                if preferred_communication and preferred_communication.lower() not in ['none', '']:
                    first_timer_insights.append(f"Preferred communication: {preferred_communication}")
                
                # Relocation status
                recently_relocated = visit_info.get('recently_relocated')
                if recently_relocated:
                    first_timer_insights.append("Recently relocated to the area")
                
                # Considering joining
                considering_joining = visit_info.get('considering_joining')
                if considering_joining:
                    first_timer_insights.append("Considering joining the church")
                
                # Interest indicators
                if interests.get('membership'):
                    first_timer_insights.append("Expressed interest in membership")
                if interests.get('baptism'):
                    first_timer_insights.append("Interested in baptism")
                if interests.get('bible_study'):
                    first_timer_insights.append("Interested in bible study")
                if interests.get('small_group'):
                    first_timer_insights.append("Interested in small groups")
                
                # Daily devotional interest
                daily_devotional = spiritual_info.get('interest_in_daily_devotional')
                if daily_devotional:
                    first_timer_insights.append("Interested in daily devotionals")
                
                # Create the note if we have insights
                if first_timer_insights:
                    notes_body = "First-timer insights from welcome form:\n" + "\n".join(f"• {insight}" for insight in first_timer_insights)
                    
                    first_timer_notes.append({
                        'id': f"welcome_form_first_timer_{target_person_id}",
                        'title': 'First-Timer Insights from Welcome Form',
                        'notes_body': notes_body,
                        'note_type': 'first_timer',
                        'source': 'welcome_form',
                        'created_at': form_metadata.get('created_at'),
                        'relevance_score': 'high',
                        'visit_context': 'new_visitor'
                    })
            
            return first_timer_notes
            
        except Exception as e:
            logger.error(f"Error collecting first timer notes: {str(e)}")
            return []

    async def _collect_existing_followup_notes(self, person_id: Optional[str] = None, family_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Collect existing followup notes for person or family.
        Since get_followup_task_notes doesn't exist, we'll use person notes instead.
        
        Args:
            person_id: Optional person ID. Uses event_data.person_id if not provided.
            family_id: Optional family ID. Uses event_data.fam_id if not provided.
        """
        try:
            target_person_id = person_id or (self.event_data.person_id if self.event_data else None)
            if not target_person_id or not self.member_service:
                return []
            
            # Since get_followup_task_notes doesn't exist, we'll get person notes
            # and filter for followup-related notes
            from uuid import UUID
            person_uuid = UUID(target_person_id)
            notes = await self.member_service._repository.get_person_notes(person_uuid, limit=20)
            
            # Filter for followup-related notes
            followup_notes = []
            if notes:
                for note in notes:
                    note_type = note.get('type', '').lower()
                    note_title = note.get('title', '').lower()
                    if 'followup' in note_type or 'follow-up' in note_type or 'followup' in note_title or 'follow-up' in note_title:
                        followup_notes.append(note)
            
            return followup_notes
        except Exception as e:
            logger.error(f"Error collecting existing followup notes: {str(e)}")
            return []

    async def _collect_public_teams(self) -> List[Dict[str, Any]]:
        """Collect public teams data for recommendations."""
        try:
            if not self.connect_service or not self.tenant_identifier:
                print("DEBUG: ConnectService not initialized or missing tenant_identifier - no teams available")
                return []
            
            teams = await self.connect_service.get_all_teams(self.tenant_identifier)
            print(f"DEBUG: Collected {len(teams)} teams from connect service")
            
            # Debug first team structure if available
            if teams:
                print(f"DEBUG: Sample team structure: {teams[0]}")
            
            return teams
        except Exception as e:
            print(f"DEBUG: Error collecting teams: {str(e)}")
            return []

    async def _collect_public_groups(self) -> List[Dict[str, Any]]:
        """Collect public groups data for recommendations."""
        try:
            if not self.connect_service or not self.tenant_identifier:
                print("DEBUG: ConnectService not initialized or missing tenant_identifier - no groups available")
                return []
            
            groups = await self.connect_service.get_public_groups(self.tenant_identifier)
            print(f"DEBUG: Collected {len(groups)} groups from connect service")
            
            # Debug first group structure if available
            if groups:
                print(f"DEBUG: Sample group structure: {groups[0]}")
            
            return groups
        except Exception as e:
            print(f"DEBUG: Error collecting groups: {str(e)}")
            return []

    async def _collect_upcoming_events(self) -> List[Dict[str, Any]]:
        """Collect upcoming events data for recommendations."""
        try:
            if not self.calendar_service:
                print("DEBUG: CalendarService not initialized - no events available")
                return []
            
            events = await self.calendar_service.get_upcoming_events(days_ahead=14)
            print(f"DEBUG: Collected {len(events)} events from calendar service")
            
            # Debug first event structure if available
            if events:
                print(f"DEBUG: Sample event structure: {events[0]}")
            
            return events
        except Exception as e:
            print(f"DEBUG: Error collecting events: {str(e)}")
            return []
    
    def _build_fallback_context(self, event_data: VisitorEventData, error_msg: str) -> VisitorContextData:
        """
        Build a minimal fallback context when data collection fails.
        """
        # Create a fallback scenario
        fallback_scenario = FamilyScenario(
            scenario_type="fallback",
            primary_person_id=str(event_data.person_id),
            family_members_to_query=[],
            fam_id=str(event_data.fam_id) if event_data.fam_id else "unknown",
            context_strategy="fallback_strategy"
        )
        
        return VisitorContextData(
            visitor_profile={"person_id": str(event_data.person_id), "error": error_msg, "tenant": event_data.tenant},
            visitor_welcome_form={},
            family_members=[],
            first_timer_notes=[],
            prayer_requests=[],
            existing_followup_notes=[],
            feedback_fields=[],
            public_teams=[],
            public_groups=[],
            upcoming_events=[],
            scenario_info=fallback_scenario
        )