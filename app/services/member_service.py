"""
Member Service for cross-service integration with VecApp Member Service.

This service provides business logic for member data operations and 
orchestrates the member repository for database access.
"""

from typing import Dict, Any, Optional, List, Union
from uuid import UUID
import logging
from datetime import datetime, timedelta, timezone

from app.data.interfaces.member_service_interface import IMemberRepository
from app.data.repositories.member_service_repository import MemberRepository
from app.data.models.member_service_models import PersonProfile, FamilyMember, PersonNote, FollowUpTask, PrayerRequest, PersonFeedback, PersonDecision, JourneyReportData

logger = logging.getLogger(__name__)


class MemberService:
    """
    Service for managing member data integration with external Member Service.
    
    This service handles business logic for member operations and provides
    a clean interface for AI agents and other services to access member data.
    """
    
    def __init__(self, schema_name: str, repository: Optional[IMemberRepository] = None):
        """
        Initialize the member service.
        
        Args:
            schema_name: The tenant-specific schema name
            member_repository: Optional repository injection for testing
        """
        self.schema_name = schema_name
        self._repository = repository or MemberRepository(schema_name)
    
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        await self._repository.initialize()
        logger.info(f"Member service initialized for schema: {self.schema_name}")
    
    async def close(self) -> None:
        """Close the service and its dependencies."""
        await self._repository.close()
        logger.info("Member service closed")
    
#==============Business logic methods for member operations========================#
    #TODO: fetch church info for better context for ai
    # async def get_church_info(self) -> Dict[str, Any]:
    #     """
    #     Get church information.
        
    #     Returns:
    #         Dictionary containing church information
    #     """
    #     return await self._repository.get_church_info()

    

    async def get_person_profile(self, person_id: UUID) -> Optional[PersonProfile]:

        try:
                # Convert string to UUID if needed
            if isinstance(person_id, str):
                    person_id = UUID(person_id)
            person = await self._repository.get_person_by_id(person_id)
            if not person:
                return None
            if person.fam_id:
                members = await self._repository.get_family_members(person.fam_id)
                # enrich immutably
                person = person.model_copy(update={"family_members": members})
            return person
        
        except Exception as e:
            logger.error(f"Error getting member profile for {person_id}: {str(e)}")
            raise

    async def get_family_members(self, fam_id: UUID) -> List[FamilyMember]:    
        try:
            if isinstance(fam_id, str):
                fam_id = UUID(fam_id)
            return await self._repository.get_family_members(fam_id)
        except Exception as e:
            logger.error(f"Error getting family members for {fam_id}: {str(e)}")
            raise

    
    async def get_family_by_id(self, fam_id: UUID) -> Optional[FamilyMember]:
        try:
            if isinstance(fam_id, str):
                fam_id = UUID(fam_id)
            return await self._repository.get_family_by_id(fam_id)
        except Exception as e:
            logger.error(f"Error getting family by id for {fam_id}: {str(e)}")
            raise


    async def get_family_members_profiles(self, member_ids: List[str]) -> List[PersonProfile]:

        return await self._repository.get_family_members_profiles(member_ids)
    
    

    async def search_persons(self, search_term: str, limit: int = 50) -> List[PersonProfile]:
        return await self._repository.search_persons(search_term, limit)

    async def get_person_by_email(self, email: str) -> Optional[PersonProfile]:
        return await self._repository.get_person_by_email(email)


    async def get_visitor_welcome_form_data(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive visitor welcome form data by person ID.
        
        Args:
            person_id: The person's unique identifier (string for SQS compatibility)
            
        Returns:
            Complete Enhanced welcome form data dictionary or None if not found
        """
        try:
            # Convert string to UUID if needed
            if isinstance(person_id, str):
                person_uuid = UUID(person_id)
                
            # Get welcome form data from repository
            welcome_form_data = await self._repository.get_visitor_welcome_form_data(person_uuid)
            
            if not welcome_form_data:
                return None
            
            # Enhance with business logic and formatting
            enhanced_data = {
                'person_info': {
                    'id': str(welcome_form_data.get('person_id')),
                    'title': welcome_form_data.get('title'),
                    'first_name': welcome_form_data.get('first_name'),
                    'middle_name': welcome_form_data.get('middle_name'),
                    'last_name': welcome_form_data.get('last_name'),
                    'email': welcome_form_data.get('email'),
                    'phone': welcome_form_data.get('phone'),
                    'date_of_birth': welcome_form_data.get('dob'),
                    'gender': welcome_form_data.get('gender'),
                    'race': welcome_form_data.get('race'),
                    'occupation': welcome_form_data.get('occupation'),
                    'marital_status': welcome_form_data.get('marital_status'),
                    'address': {
                        'street': welcome_form_data.get('address'),
                        'city': welcome_form_data.get('city'),
                        'state': welcome_form_data.get('state'),
                        'country': welcome_form_data.get('country'),
                        'zip': welcome_form_data.get('zip')
                    }
                },
                'visit_info': {
                    'visit_date': welcome_form_data.get('created_at'),
                    'visit_type': welcome_form_data.get('visit_type'),
                    'best_contact_time': welcome_form_data.get('best_contact_time'),
                    'how_heard_about_church': welcome_form_data.get('how_heard_about_us'),
                    'recently_relocated': welcome_form_data.get('recently_relocated'),
                    'considering_joining': welcome_form_data.get('considering_joining'),
                    'preferred_communication_method': welcome_form_data.get('preferred_communication_method'),
                    'joined_via': welcome_form_data.get('joined_via')
                },
                'interests': {
                    'membership': welcome_form_data.get('interested_in_membership', False),
                    'baptism': welcome_form_data.get('interested_in_baptism', False),
                    'bible_study': welcome_form_data.get('interested_in_bible_study', False),
                    'small_group': welcome_form_data.get('interested_in_small_group', False)
                },
                'spiritual_info': {
                    'spiritual_need': welcome_form_data.get('spiritual_need'),
                    'spiritual_challenge': welcome_form_data.get('spiritual_challenge'),
                    'prayer_request': welcome_form_data.get('prayer_request'),
                    'feedback': welcome_form_data.get('feedback'),
                    'interest_in_daily_devotional': welcome_form_data.get('daily_devotional'),
                    'joining_our_church': welcome_form_data.get('joining_our_church')
                },
                'form_metadata': {
                    'form_id': welcome_form_data.get('form_id'),
                    'comments': welcome_form_data.get('comments'),
                    'created_at': welcome_form_data.get('created_at'),
                    'updated_at': welcome_form_data.get('updated_at')
                }
            }
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error getting visitor welcome form data for {person_id}: {str(e)}")
            raise


    async def get_recent_visitors(self, days: int = 30, limit: int = 100) -> List[PersonProfile]:
        return await self._repository.get_recent_visitors(days, limit)
    
    async def get_visitors_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[PersonProfile]:
        return await self._repository.get_visitors_by_date_range(start_date, end_date)

    async def get_new_individual_added_to_existing_family(self, person_id: UUID, fam_id: UUID) -> Optional[PersonProfile]:
        return await self._repository.get_new_individual_added_to_existing_family(person_id, fam_id)

    
    
    ##Notes
    async def create_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a note with enhanced business logic validation for AI-generated notes.
        
        Args:
            note_data: Dictionary containing note information
            
        Returns:
            Created note with metadata
        """
        try:
            # Enhanced validation for required fields - task_id is optional
            required_fields = ['person_id', 'title', 'notes_body', 'type', 'meta']
            missing_fields = [field for field in required_fields if not note_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Required fields missing: {', '.join(missing_fields)}")
            
            # Validate UUIDs
            try:
                if note_data.get('person_id'):
                    UUID(str(note_data['person_id']))
                if note_data.get('recipient_id'):
                    UUID(str(note_data['recipient_id']))
                if note_data.get('recipient_fam_id'):
                    UUID(str(note_data['recipient_fam_id']))
            except ValueError as e:
                raise ValueError(f"Invalid UUID format: {str(e)}")

            # CRITICAL: Add schema validation to prevent cross-tenant contamination
            if not self._repository.schema_name:
                raise ValueError("Schema name not set - potential data contamination risk")
            
            logger.info(f"Creating note for person {note_data.get('person_id')} in schema {self._repository.schema_name}")
            
            # Enhance note data with service metadata
            enhanced_note_data = {
                **note_data,
                'created_by_service': 'ai_service',
                'schema_name': self._repository.schema_name,
                # Preserve existing meta and add service metadata
                'meta': {
                    'service_metadata': {
                        'created_by_service': 'ai_service',
                        'service_version': '1.0',
                        'created_at': datetime.now(timezone.utc).isoformat()
                    },
                    **note_data.get('meta', {})
                }
            }
            # Call repository with enhanced validation
            result = await self._repository.create_note(enhanced_note_data)
            
            # # Create note via repository
            # created_note = await self._repository.create_note(enhanced_note_data)
            
            # if not created_note:
            #     raise ValueError("Failed to create note - no data returned")
            
            logger.info(
                f"AI note created successfully - ID: {result.get('id')}, in schema: {self._repository.schema_name}, "
                f"Person: {note_data['person_id']}, Type: {note_data['type']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating member note in schema {self._repository.schema_name}: {str(e)}")
            raise
    
    async def get_person_notes(self, person_id: UUID, limit: int = 20) -> List[PersonNote]:
        return await self._repository.get_person_notes(person_id=person_id, limit=limit)

    
    async def get_updated_person_data(self, person_id: UUID, since: datetime) -> List[PersonProfile]:
        return await self._repository.get_updated_person_data(person_id, since)

    
    async def get_updated_notes(self, since: datetime) -> List[PersonNote]:
        return await self._repository.get_updated_notes(since)

    async def get_prayer_requests(self, person_id: str) -> List[Dict[str, Any]]:
        """
        Get prayer requests for a specific person using title-based filtering.
        
        Args:
            person_id: The person's unique identifier (string for SQS compatibility)
            
        Returns:
            List of prayer request notes
        """
        try:
            # Convert string to UUID if needed
            if isinstance(person_id, str):
                person_uuid = UUID(person_id)
                
            # Get notes with prayer-related titles
            prayer_title_patterns = [
                "Prayer Request",
                "Prayer",
                "Pray for",
                "Prayer Need"
            ]
            
            prayer_notes = await self._repository.get_notes_by_title_pattern(
                person_uuid, 
                prayer_title_patterns, 
                limit=20
            )
            
            # Enhance with prayer-specific metadata
            enhanced_prayers = []
            for note in prayer_notes:
                enhanced_note = {
                    **(note if isinstance(note, dict) else {}),
                    'request_type': 'prayer',
                    'urgency': self._assess_prayer_urgency(note.notes_body or ""),
                    'category': self._categorize_prayer_request(note.notes_body or "")
                }
                enhanced_prayers.append(enhanced_note)
            
            return enhanced_prayers
            
        except Exception as e:
            logger.error(f"Error getting prayer requests for {person_id}: {str(e)}")
            raise

    async def get_first_timer_notes(self, person_id: str) -> List[Dict[str, Any]]:
        """
        Get first-timer specific notes using title-based filtering with fallback.
        
        Args:
            person_id: The person's unique identifier (string for SQS compatibility)
            
        Returns:
            List of first-timer notes
        """
        try:
            # Convert string to UUID if needed
            if isinstance(person_id, str):
                person_uuid = UUID(person_id)
                
            # First try title-based filtering
            first_timer_patterns = [
                "First Timer",
                "First-Timer", 
                "First Visit",
                "New Visitor",
                "Welcome Note",
                "Visit Note",
                "Prayer Request",
                "Prayer",
                "Feedback",
                "Visitor Summary",
                "Initial",
                "Welcome"
            ]
            
            first_timer_notes = await self._repository.get_notes_by_title_pattern(
                person_uuid,
                first_timer_patterns,
                limit=10
            )
            
            # If no title-based notes found, fallback to recent notes
            if not first_timer_notes:
                logger.warning(f"No title-based first timer notes found for {person_id}, falling back to recent notes")
                all_notes = await self._repository.get_person_notes(person_uuid, limit=5)
                
                # Filter for recent notes (within last 30 days) as potential first-timer notes
                from datetime import datetime, timedelta, timezone
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                
                first_timer_notes = [
                    note for note in all_notes 
                    if note.created_at and note.created_at >= cutoff_date
                ]
                
                logger.info(f"Found {len(first_timer_notes)} recent notes as fallback for {person_id}")
            
            # Enhance with first-timer specific metadata
            enhanced_notes = []
            for note in first_timer_notes:
                # Convert to dict if it's not already
                if hasattr(note, '__dict__'):
                    note_dict = note.__dict__
                elif hasattr(note, 'model_dump'):
                    note_dict = note.model_dump()
                elif isinstance(note, dict):
                    note_dict = note
                else:
                    note_dict = {"notes_body": str(note)}
                    
                enhanced_note = {
                    **note_dict,
                    'note_type': 'first_timer',
                    'relevance_score': self._calculate_first_timer_relevance(note_dict.get('notes_body', "")),
                    'visit_context': self._extract_visit_context(note_dict.get('notes_body', ""))
                }
                enhanced_notes.append(enhanced_note)
            
            logger.debug(f"Returning {len(enhanced_notes)} enhanced first timer notes for {person_id}")
            return enhanced_notes
            
        except Exception as e:
            logger.error(f"Error getting first timer notes for {person_id}: {str(e)}")
            raise

    async def get_feedback_fields(self, person_id: str) -> List[Dict[str, Any]]:
        """
        Get feedback notes using title-based filtering.
        
        Args:
            person_id: The person's unique identifier (string for SQS compatibility)
            
        Returns:
            List of feedback notes
        """
        try:
            # Convert string to UUID if needed
            if isinstance(person_id, str):
                person_uuid = UUID(person_id)
                
            # Get notes with feedback-related titles
            feedback_patterns = [
                "Feedback",
                "Service Feedback",
                "Experience",
                "Rating",
                "Comment",
                "Suggestion"
            ]
            
            feedback_notes = await self._repository.get_notes_by_title_pattern(
                person_uuid,
                feedback_patterns,
                limit=15
            )
            
            # Enhance with feedback-specific metadata
            enhanced_feedback = []
            for note in feedback_notes:
                enhanced_note = {
                     **(note if isinstance(note, dict) else {}),
                    'feedback_type': self._categorize_feedback_type(note.notes_body or ""),
                    'sentiment': self._analyze_feedback_sentiment(note.notes_body or ""),
                    'note_type': 'feedback'
                }
                enhanced_feedback.append(enhanced_note)
            
            return enhanced_feedback
            
        except Exception as e:
            logger.error(f"Error getting feedback fields for {person_id}: {str(e)}")
            raise


    ##   # Private helper methods for business logic

    def _extract_visit_context(self, note_content: str) -> str:
        """Extract visit context from note content."""
        visit_keywords = ['first visit', 'new visitor', 'welcome', 'church event']
        for keyword in visit_keywords:
            if keyword in note_content.lower():
                return keyword
        return 'general'


    def _categorize_feedback_type(self, note_content: str) -> str:
        """Categorize feedback type from note content."""
        if any(keyword in note_content for keyword in ['service', 'worship', 'sermon']):
            return 'service_feedback'
        elif any(keyword in note_content for keyword in ['facility', 'building', 'room']):
            return 'facility_feedback'
        elif any(keyword in note_content for keyword in ['staff', 'pastor', 'leader']):
            return 'staff_feedback'
        elif any(keyword in note_content for keyword in ['program', 'event', 'activity']):
            return 'program_feedback'
        else:
            return 'general_feedback'

    def _analyze_feedback_sentiment(self, note_content: str) -> str:
        """Analyze sentiment of feedback."""
        positive_keywords = ['great', 'excellent', 'wonderful', 'amazing', 'love', 'blessed']
        negative_keywords = ['poor', 'bad', 'terrible', 'disappointed', 'frustrated']
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in note_content)
        negative_count = sum(1 for keyword in negative_keywords if keyword in note_content)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _calculate_first_timer_relevance(self, note_content: str) -> float:
        """Calculate relevance score for first-timer notes."""
        keywords_weights = {
            'first time': 1.0,
            'first visit': 1.0,
            'new visitor': 0.9,
            'welcome': 0.7,
            'first-timer': 1.0
        }
        
        score = 0.0
        for keyword, weight in keywords_weights.items():
            if keyword in note_content:
                score += weight
        
        return min(score, 1.0)  # Cap at 1.0

    def _assess_prayer_urgency(self, note_content: str) -> str:
        """Assess urgency of prayer requests."""
        urgent_keywords = ['urgent', 'emergency', 'critical', 'immediate']
        high_keywords = ['serious', 'important', 'significant']
        
        if any(keyword in note_content for keyword in urgent_keywords):
            return 'urgent'
        elif any(keyword in note_content for keyword in high_keywords):
            return 'high'
        else:
            return 'normal'

    def _categorize_prayer_request(self, note_content: str) -> str:
        """Categorize prayer requests by type."""
        categories = {
            'health': ['health', 'sick', 'illness', 'surgery', 'medical', 'healing'],
            'family': ['family', 'marriage', 'children', 'relationship', 'divorce'],
            'financial': ['financial', 'job', 'work', 'money', 'employment'],
            'spiritual': ['spiritual', 'faith', 'salvation', 'growth', 'discipleship'],
            'general': []
        }
        
        for category, keywords in categories.items():
            if any(keyword in note_content for keyword in keywords):
                return category
        
        return 'general'

    def _has_action_items(self, note_content: str) -> bool:
        """Check if note contains action items."""
        action_keywords = ['call', 'email', 'visit', 'contact', 'schedule', 'arrange', 'send']
        return any(keyword in note_content for keyword in action_keywords)

    def _assess_followup_priority(self, note_content: str) -> int:
        """Assess priority of follow-up notes (1-5, 5 being highest)."""
        high_priority_keywords = ['urgent', 'asap', 'important', 'critical']
        medium_priority_keywords = ['soon', 'this week', 'follow up']
        
        if any(keyword in note_content for keyword in high_priority_keywords):
            return 5
        elif any(keyword in note_content for keyword in medium_priority_keywords):
            return 3
        else:
            return 1

    def _assess_engagement_level(self, notes: List[Dict[str, Any]]) -> str:
        """Assess overall engagement level based on notes."""
        if not notes:
            return 'unknown'
        
        positive_keywords = ['engaged', 'interested', 'active', 'participating', 'enthusiastic']
        negative_keywords = ['disengaged', 'uninterested', 'inactive', 'distant']
        
        positive_count = sum(1 for note in notes 
                            if any(keyword in note.get('note', '').lower() 
                                for keyword in positive_keywords))
        negative_count = sum(1 for note in notes 
                            if any(keyword in note.get('note', '').lower() 
                                for keyword in negative_keywords))
        
        if positive_count > negative_count:
            return 'high'
        elif negative_count > positive_count:
            return 'low'
        else:
            return 'medium'

    def _extract_communication_preferences(self, person: Dict[str, Any], notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract communication preferences from person data and notes."""
        preferences = {
            'preferred_method': 'email',  # Default
            'best_time_to_contact': 'evening',  # Default
            'frequency': 'weekly'  # Default
        }
        
        # Check notes for communication preferences
        for note in notes:
            note_content = note.get('note', '').lower()
            if 'prefers phone' in note_content or 'call' in note_content:
                preferences['preferred_method'] = 'phone'
            elif 'prefers text' in note_content or 'text message' in note_content:
                preferences['preferred_method'] = 'text'
            
            if 'morning' in note_content:
                preferences['best_time_to_contact'] = 'morning'
            elif 'afternoon' in note_content:
                preferences['best_time_to_contact'] = 'afternoon'
        
        return preferences

    def _extract_interests(self, notes: List[Dict[str, Any]]) -> List[str]:
        """Extract interests from notes."""
        interest_keywords = {
            'music': ['music', 'choir', 'worship', 'singing'],
            'children': ['children', 'kids', 'youth', 'nursery'],
            'bible_study': ['bible study', 'small group', 'study'],
            'volunteering': ['volunteer', 'serve', 'help', 'ministry'],
            'prayer': ['prayer', 'pray', 'intercession']
        }
        
        interests = []
        for note in notes:
            note_content = note.get('note', '').lower()
            for interest, keywords in interest_keywords.items():
                if any(keyword in note_content for keyword in keywords):
                    if interest not in interests:
                        interests.append(interest)
        
        return interests

    def _extract_concerns(self, notes: List[Dict[str, Any]]) -> List[str]:
        """Extract concerns from notes."""
        concerns = []
        concern_keywords = ['concern', 'worried', 'problem', 'issue', 'difficulty']
        
        for note in notes:
            note_content = note.get('note', '').lower()
            if any(keyword in note_content for keyword in concern_keywords):
                concerns.append(note.get('note', '')[:100] + '...')  # First 100 chars
        
        return concerns[:5]  # Return top 5 concerns

    def _extract_positive_feedback(self, notes: List[Dict[str, Any]]) -> List[str]:
        """Extract positive feedback from notes."""
        positive_feedback = []
        positive_keywords = ['love', 'enjoy', 'great', 'wonderful', 'amazing', 'blessed', 'grateful']
        
        for note in notes:
            note_content = note.get('note', '').lower()
            if any(keyword in note_content for keyword in positive_keywords):
                positive_feedback.append(note.get('note', '')[:100] + '...')
        
        return positive_feedback[:5]

    def _extract_improvement_areas(self, notes: List[Dict[str, Any]]) -> List[str]:
        """Extract areas for improvement from notes."""
        improvement_areas = []
        improvement_keywords = ['improve', 'better', 'suggestion', 'feedback', 'change']
        
        for note in notes:
            note_content = note.get('note', '').lower()
            if any(keyword in note_content for keyword in improvement_keywords):
                improvement_areas.append(note.get('note', '')[:100] + '...')
        
        return improvement_areas[:3]

    def _get_last_feedback_date(self, notes: List[Dict[str, Any]]) -> Optional[datetime]:
        """Get the date of the last feedback."""
        feedback_keywords = ['feedback', 'comment', 'suggestion', 'opinion']
        
        for note in sorted(notes, key=lambda x: x.get('created_at', datetime.min), reverse=True):
            note_content = note.get('note', '').lower()
            if any(keyword in note_content for keyword in feedback_keywords):
                return note.get('created_at')
        
        return None

    def _determine_relationship(self, primary_person: Dict[str, Any], family_member: Dict[str, Any]) -> str:
        """Determine relationship between primary person and family member."""
        # This is a simplified implementation - can be enhanced with actual relationship data
        if family_member['id'] == primary_person['id']:
            return 'self'
        
        # Basic age-based relationship determination
        primary_age = self._calculate_age(primary_person.get('dob', datetime.now()))
        member_age = self._calculate_age(family_member.get('dob', datetime.now()))
        
        age_diff = abs(primary_age - member_age)
        
        if age_diff < 5:
            return 'spouse/partner'
        elif member_age < 18 and primary_age > 25:
            return 'child'
        elif member_age > primary_age + 20:
            return 'parent'
        else:
            return 'family_member'

    def _assess_member_engagement(self, notes: List[Dict[str, Any]]) -> str:
        """Assess engagement level for a family member."""
        if not notes:
            return 'unknown'
        
        recent_notes = [n for n in notes if self._is_recent(n.get('created_at'), 30)]
        
        if len(recent_notes) >= 3:
            return 'high'
        elif len(recent_notes) >= 1:
            return 'medium'
        else:
            return 'low'

    def _categorize_age_group(self, dob: Optional[datetime]) -> str:
        """Categorize person into age group."""
        if not dob:
            return 'unknown'
        
        age = self._calculate_age(dob)
        
        if age < 13:
            return 'child'
        elif age < 18:
            return 'teen'
        elif age < 30:
            return 'young_adult'
        elif age < 50:
            return 'adult'
        elif age < 65:
            return 'middle_aged'
        else:
            return 'senior'

    def _calculate_age(self, dob: datetime) -> int:
        """Calculate age from date of birth."""
        today = datetime.now(timezone.utc).date()
        if isinstance(dob, datetime):
            dob = datetime.combine(dob.date(), datetime.min.time())
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def _is_recent(self, date_value: Union[datetime, str, None], days_threshold: int = 30) -> bool:
        """
        Check if a date is within the specified threshold of days from now.

        Args:
            date_value: The datetime to check (can be timezone-aware, naive, or ISO string)
            days_threshold: Number of days to consider as recent

        Returns:
            True if the date is recent, False otherwise
        """
        if not date_value:
            return False

        try:
            # Handle string input
            if isinstance(date_value, str):
                # Strip whitespace and handle 'Z' suffix specifically
                s = date_value.strip()
                if s.upper().endswith('Z'):
                    s = s[:-1] + '+00:00'
                # Parse the modified string
                parsed_date = datetime.fromisoformat(s)
                # Convert to UTC if naive
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                date_value = parsed_date

            # Ensure all datetimes are timezone-aware (convert naive to UTC)
            if isinstance(date_value, datetime) and date_value.tzinfo is None:
                date_value = date_value.replace(tzinfo=timezone.utc)

            # Calculate cutoff and compare
            now_utc = datetime.now(timezone.utc)
            cutoff_date = now_utc - timedelta(days=days_threshold)
            return date_value >= cutoff_date

        except Exception as e:
            logger.warning(f"Error parsing date value {date_value}: {str(e)}")
            return False

    # Journey Report Methods
    async def get_person_journey_data(self, person_id: UUID, date_range: Optional[tuple] = None) -> JourneyReportData:
        """Get comprehensive journey report data for a person."""
        return await self._repository.get_journey_report_data(person_id, date_range)
    
    async def get_family_journey_data(self, fam_id: UUID, date_range: Optional[tuple] = None) -> List[JourneyReportData]:
        """Get comprehensive journey report data for all family members."""
        return await self._repository.get_family_journey_report_data(fam_id, date_range)
    
    async def get_visitors_journey_data(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[JourneyReportData]:
        """Get journey report data for visitors within a date range."""
        return await self._repository.get_visitors_journey_data(start_date, end_date, limit)
    
    async def get_person_follow_up_tasks(self, person_id: UUID, limit: int = 100) -> List[FollowUpTask]:
        """Get all follow-up tasks for a person."""
        return await self._repository.get_person_follow_up_tasks(person_id, limit)
    
    async def get_person_prayer_requests(self, person_id: UUID) -> List[PrayerRequest]:
        """Get prayer requests for a person."""
        return await self._repository.get_person_prayer_requests(person_id)
    
    async def get_person_feedback(self, person_id: UUID) -> List[PersonFeedback]:
        """Get feedback entries for a person."""
        return await self._repository.get_person_feedback(person_id)
    
    async def get_person_decisions(self, person_id: UUID) -> List[PersonDecision]:
        """Get decision data for a person."""
        return await self._repository.get_person_decisions(person_id)

    