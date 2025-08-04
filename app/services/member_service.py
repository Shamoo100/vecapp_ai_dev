"""
Member Service for cross-service integration with VecApp Member Service.

This service provides business logic for member data operations and 
orchestrates the member repository for database access.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime, timedelta, timezone

from app.data.interfaces.member_service_interface import IMemberRepository
from app.data.repositories.member_service_repository import MemberRepository

logger = logging.getLogger(__name__)


class MemberService:
    """
    Service for managing member data integration with external Member Service.
    
    This service handles business logic for member operations and provides
    a clean interface for AI agents and other services to access member data.
    """
    
    def __init__(self, schema_name: str, member_repository: Optional[IMemberRepository] = None):
        """
        Initialize the member service.
        
        Args:
            schema_name: The tenant-specific schema name
            member_repository: Optional repository injection for testing
        """
        self.schema_name = schema_name
        self._repository = member_repository or MemberRepository(schema_name)
    
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        await self._repository.initialize()
        logger.info(f"Member service initialized for schema: {self.schema_name}")
    
    async def close(self) -> None:
        """Close the service and its dependencies."""
        await self._repository.close()
        logger.info("Member service closed")
    
    async def get_member_profile(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive member profile including family information.
        
        Args:
            person_id: The person's unique identifier (string for SQS compatibility)
            
        Returns:
            Enhanced member profile with family context
        """
        try:
            # Convert string to UUID if needed
            if isinstance(person_id, str):
                person_id = UUID(person_id)
                
            person = await self._repository.get_person_by_id(person_id)
            if not person:
                return None
            
            # Enhance with family members if family ID exists
            if person.get('fam_id'):
                family_members = await self._repository.get_family_members(person['fam_id'])
                person['family_members'] = family_members
            
            # Add recent notes
            recent_notes = await self._repository.get_person_notes(person_id, limit=10)
            person['recent_notes'] = recent_notes
            
            return person
            
        except Exception as e:
            logger.error(f"Error getting member profile for {person_id}: {str(e)}")
            raise
    
    #preliminary implementation of the geet visitor snapshot requirement 
    #TODO:Implement this for visitor snapshot
    # async def get_visitor_insights(self, limit: int = 100) -> Dict[str, Any]:
    #     """
    #     Get visitor data with insights for AI processing.
        
    #     Args:
    #         limit: Maximum number of visitors to return
            
    #     Returns:
    #         Dictionary containing visitors and insights
    #     """
    #     try:
    #         visitors = await self._repository.get_visitors(limit)
            
    #         # Add business logic insights
    #         insights = {
    #             'total_visitors': len(visitors),
    #             'recent_visitors_30_days': len([v for v in visitors 
    #                                           if self._is_recent(v.get('created_at'), 30)]),
    #             'visitors_with_families': len([v for v in visitors if v.get('fam_id')]),
    #             'visitors_by_join_method': self._group_by_join_method(visitors)
    #         }
            
    #         return {
    #             'visitors': visitors,
    #             'insights': insights
    #         }
            
    #     except Exception as e:
    #         logger.error(f"Error getting visitor insights: {str(e)}")
    #         raise
    
    async def get_family_context(self, fam_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive family context for AI agents.
        
        Args:
            fam_id: The family's unique identifier
            
        Returns:
            Family context with member relationships
        """
        try:
            family_members = await self._repository.get_family_members(fam_id)
            
            # Add family insights
            family_context = {
                'family_id': fam_id,
                'members': family_members,
                'total_members': len(family_members),
                'member_types': self._analyze_member_types(family_members),
                'age_distribution': self._analyze_age_distribution(family_members)
            }
            
            return family_context
            
        except Exception as e:
            logger.error(f"Error getting family context for {fam_id}: {str(e)}")
            raise
    
    async def create_member_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
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
            
            # Enhance note data with service metadata
            enhanced_note_data = {
                **note_data,
                'created_by_service': 'ai_service',
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
            
            # Create note via repository
            created_note = await self._repository.create_note(enhanced_note_data)
            
            if not created_note:
                raise ValueError("Failed to create note - no data returned")
            
            logger.info(
                f"AI note created successfully - ID: {created_note.get('id')}, "
                f"Person: {note_data['person_id']}, Type: {note_data['type']}"
            )
            
            return created_note
            
        except Exception as e:
            logger.error(f"Error creating member note: {str(e)}")
            raise

    async def get_task_context(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get task context with related member information.
        
        Args:
            task_id: The task's unique identifier
            
        Returns:
            Task context with member details
        """
        try:
            task = await self._repository.get_task_by_id(task_id)
            if not task:
                return None
            
            # Enhance with recipient information if available
            if task.get('recipient_id'):
                recipient = await self._repository.get_person_by_id(task['recipient_id'])
                task['recipient_details'] = recipient
            
            return task
            
        except Exception as e:
            logger.error(f"Error getting task context for {task_id}: {str(e)}")
            raise

    async def get_visitor_welcome_form_data(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive visitor welcome form data by person ID.
        
        Args:
            person_id: The person's unique identifier (string for SQS compatibility)
            
        Returns:
            Complete welcome form data dictionary or None if not found
        """
        try:
            # Convert string to UUID if needed
            if isinstance(person_id, str):
                person_id = UUID(person_id)
                
            # Get welcome form data from repository
            welcome_form_data = await self._repository.get_visitor_welcome_form_data(person_id)
            
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
                person_id = UUID(person_id)
                
            # Get notes with prayer-related titles
            prayer_title_patterns = [
                "Prayer Request",
                "Prayer",
                "Pray for",
                "Prayer Need"
            ]
            
            prayer_notes = await self._repository.get_notes_by_title_pattern(
                person_id, 
                prayer_title_patterns, 
                limit=20
            )
            
            # Enhance with prayer-specific metadata
            enhanced_prayers = []
            for note in prayer_notes:
                enhanced_note = {
                    **note,
                    'request_type': 'prayer',
                    'urgency': self._assess_prayer_urgency(note.get('notes_body', '')),
                    'category': self._categorize_prayer_request(note.get('notes_body', ''))
                }
                enhanced_prayers.append(enhanced_note)
            
            return enhanced_prayers
            
        except Exception as e:
            logger.error(f"Error getting prayer requests for {person_id}: {str(e)}")
            raise

    async def get_first_timer_notes(self, person_id: str) -> List[Dict[str, Any]]:
        """
        Get first-timer specific notes using title-based filtering.
        
        Args:
            person_id: The person's unique identifier (string for SQS compatibility)
            
        Returns:
            List of first-timer notes
        """
        try:
            # Convert string to UUID if needed
            if isinstance(person_id, str):
                person_id = UUID(person_id)
                
            # Get notes with first-timer related titles
            first_timer_patterns = [
                "First Timer",
                "First-Timer", 
                "First Visit",
                "New Visitor",
                "Welcome Note"
            ]
            
            first_timer_notes = await self._repository.get_notes_by_title_pattern(
                person_id,
                first_timer_patterns,
                limit=10
            )
            
            # Enhance with first-timer specific metadata
            enhanced_notes = []
            for note in first_timer_notes:
                enhanced_note = {
                    **note,
                    'note_type': 'first_timer',
                    'relevance_score': self._calculate_first_timer_relevance(note.get('notes_body', '')),
                    'visit_context': self._extract_visit_context(note.get('notes_body', ''))
                }
                enhanced_notes.append(enhanced_note)
            
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
                person_id = UUID(person_id)
                
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
                person_id,
                feedback_patterns,
                limit=15
            )
            
            # Enhance with feedback-specific metadata
            enhanced_feedback = []
            for note in feedback_notes:
                enhanced_note = {
                    **note,
                    'feedback_type': self._categorize_feedback_type(note.get('notes_body', '')),
                    'sentiment': self._analyze_feedback_sentiment(note.get('notes_body', '')),
                    'note_type': 'feedback'
                }
                enhanced_feedback.append(enhanced_note)
            
            return enhanced_feedback
            
        except Exception as e:
            logger.error(f"Error getting feedback fields for {person_id}: {str(e)}")
            raise

    async def get_family_members_profiles(self, member_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed profiles for multiple family members by their IDs.
        
        Args:
            member_ids: List of person IDs (as strings for SQS compatibility)
            
        Returns:
            List of enhanced member profiles with family context
        """
        try:
            if not member_ids:
                return []
            
            # Get profiles from repository
            profiles = await self._repository.get_family_members_profiles(member_ids)
            
            # Enhance each profile with additional context
            enhanced_profiles = []
            for profile in profiles:
                # Add recent notes for context
                try:
                    person_id = UUID(str(profile['id']))
                    recent_notes = await self._repository.get_person_notes(person_id, limit=5)
                    profile['recent_notes'] = recent_notes
                    profile['engagement_level'] = self._assess_member_engagement(recent_notes)
                    profile['age_group'] = self._categorize_age_group(profile.get('dob'))
                except Exception as e:
                    logger.warning(f"Could not enhance profile for {profile.get('id')}: {str(e)}")
                    profile['recent_notes'] = []
                    profile['engagement_level'] = 'unknown'
                    profile['age_group'] = 'unknown'
                
                enhanced_profiles.append(profile)
            
            return enhanced_profiles
            
        except Exception as e:
            logger.error(f"Error getting family members profiles: {str(e)}")
            raise

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
            dob = dob.date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def _is_recent(self, date_value: Optional[datetime], days_threshold: int = 30) -> bool:
        """
        Check if a date is within the specified threshold of days from now.
        
        Args:
            date_value: The datetime to check (can be timezone-aware or naive)
            days_threshold: Number of days to consider as recent
            
        Returns:
            True if the date is recent, False otherwise
        """
        if not date_value:
            return False
        
        try:
            # Handle string conversion if needed
            if isinstance(date_value, str):
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            
            # Get current time in UTC
            now_utc = datetime.now(timezone.utc)
            
            # Ensure both datetimes have consistent timezone handling
            if date_value.tzinfo is None:
                # If date_value is naive, assume it's UTC and make it timezone-aware
                date_value = date_value.replace(tzinfo=timezone.utc)
            
            # Calculate cutoff date
            cutoff_date = now_utc - timedelta(days=days_threshold)
            
            return date_value >= cutoff_date
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing date value {date_value}: {str(e)}")
            return False
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        return date_value >= cutoff_date