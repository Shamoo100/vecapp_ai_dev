from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import asyncio
from .base_agent import BaseAgent
from app.api.schemas.event_schemas import AIGeneratedNoteStructure, VisitorContextData
from app.llm.prompts import PromptLibrary
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langsmith import trace
import google as genai
import os
from dotenv import load_dotenv

# Load the Gemini API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError('GOOGLE_API_KEY not found in .env')

genai.configure(api_key=GEMINI_API_KEY)


class FollowupNoteAgent(BaseAgent):
    """
    Enhanced AI agent for generating comprehensive visitor follow-up notes
    based on acceptance criteria and visitor context data.
    """
    
    # def __init__(self, agent_id: str, schema: str, openai_key: str):
    #     super().__init__(agent_id, schema)
    #     self.llm = ChatOpenAI(
    #         model="gpt-4o",
    #         temperature=0.3,
    #         openai_api_key=openai_key
    #     )
    #     self.prompts = PromptLibrary()

    def __init__(self, agent_id: str, schema: str, gemini_api_key: str): # Renamed parameter
        super().__init__(agent_id, schema)
        self.model = genai.GenerativeModel(
            model="gemini-1.5-pro", # Use a Gemini model
            temperature=0.3,
            google_api_key=GEMINI_API_KEY # Use the loaded key
        )
        self.prompts = PromptLibrary()

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visitor insights and follow-up recommendations"""
        try:
            visitor_context = VisitorContextData(**data)
            
            # Generate comprehensive AI note
            ai_note = await self.generate_comprehensive_note(visitor_context)
            
            processed_data = {
                'visitor_id': visitor_context.visitor_profile.get('person_id'),
                'schema': self.schema,
                'ai_note': ai_note,
                'generation_metadata': {
                    'agent_id': self.agent_id,
                    'model_version': 'gemini-1.5-pro',
                    'generated_at': datetime.now().isoformat(),
                    'confidence_score': ai_note.get('confidence_score', 0.85)
                }
            }

            self.log_activity(f"Generated comprehensive note for visitor {visitor_context.visitor_profile.get('person_id')}")
            return processed_data

        except Exception as e:
            self.log_activity(f"Error generating insights: {str(e)}", "error")
            raise

    async def generate_comprehensive_note(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """Generate a comprehensive follow-up note for a visitor."""
        try:
            visitor = visitor_context.visitor_profile
            
            # Run analysis tasks concurrently with proper exception handling
            analysis_tasks = await asyncio.gather(
                self._analyze_visitor_profile(visitor_context),
                self._analyze_family_context(visitor_context),
                self._perform_sentiment_analysis(visitor_context),
                self._generate_recommendations(visitor_context),
                return_exceptions=True
            )
            
            # Handle exceptions from asyncio.gather by replacing them with default values
            default_values = [
                {'interests': ['General Fellowship'], 'ministry_areas': ['Sunday Service'], 'life_stage': 'Unknown', 'spiritual_background': 'Unknown', 'specific_needs': []},
                {'context': 'Individual visit', 'is_family': False, 'member_count': 1, 'has_children': False, 'children_count': 0, 'is_existing': False},
                {'overall_sentiment': 'Neutral', 'confidence': 0.5, 'key_emotions': ['Curious'], 'concerns': [], 'positive_indicators': []},
                {'community_integration': [], 'event_engagement': [], 'personal_needs': None, 'feedback_insights': None}
            ]
            
            processed_tasks = []
            for i, task in enumerate(analysis_tasks):
                if isinstance(task, Exception):
                    self.log_activity(f"Analysis task {i} failed: {str(task)}", "error")
                    processed_tasks.append(default_values[i])
                else:
                    processed_tasks.append(task)
            
            profile_analysis, family_analysis, sentiment_analysis, recommendations = processed_tasks
            
            # Determine best contact time and method
            contact_info = await self._determine_optimal_contact(visitor_context, profile_analysis)
            
            # Create raw content for display
            raw_content = self._create_raw_content(visitor, profile_analysis, family_analysis, sentiment_analysis, recommendations, contact_info)
            
            # Transform recommendations to match schema requirements
            church_integration_recs = []
            for rec in recommendations.get('community_integration', []):
                if isinstance(rec, str):
                    church_integration_recs.append({
                        'type': 'community_integration',
                        'title': rec,
                        'description': rec,
                        'priority': 'medium'
                    })
                elif isinstance(rec, dict):
                    church_integration_recs.append(rec)
            
            event_engagement_recs = []
            for rec in recommendations.get('event_engagement', []):
                if isinstance(rec, str):
                    event_engagement_recs.append({
                        'type': 'event_engagement',
                        'title': rec,
                        'description': rec,
                        'priority': 'medium'
                    })
                elif isinstance(rec, dict):
                    event_engagement_recs.append(rec)
            
            # Transform personal_needs to Dict format
            personal_needs_response = None
            if recommendations.get('personal_needs'):
                if isinstance(recommendations['personal_needs'], str):
                    personal_needs_response = {
                        'type': 'personal_needs',
                        'summary': recommendations['personal_needs'],
                        'action_required': True,
                        'escalation_required': False
                    }
                elif isinstance(recommendations['personal_needs'], dict):
                    personal_needs_response = recommendations['personal_needs']
            
            # Transform feedback_insights to Dict format
            feedback_insight = None
            if recommendations.get('feedback_insights'):
                if isinstance(recommendations['feedback_insights'], str):
                    feedback_insight = {
                        'type': 'feedback_insight',
                        'tone': 'positive',
                        'category': 'general',
                        'action_step': recommendations['feedback_insights']
                    }
                elif isinstance(recommendations['feedback_insights'], dict):
                    feedback_insight = recommendations['feedback_insights']
            
            # Compile structured note using AIGeneratedNoteStructure schema
            ai_note = {
                'visitor_full_name': f"{visitor.get('first_name', '')} {visitor.get('last_name', '')}".strip(),
                'visitor_phone': visitor.get('phone', ''),
                'visitor_email': visitor.get('email', ''),
                'best_contact_time': contact_info.get('best_time', ''),
                'key_interests_summary': profile_analysis.get('interests', []),
                'family_context_info': family_analysis.get('context', ''),
                'sentiment_analysis': sentiment_analysis,
                'church_integration_recommendations': church_integration_recs,
                'event_engagement_recommendations': event_engagement_recs,
                'personal_needs_response': personal_needs_response,
                'feedback_insight': feedback_insight,
                'ai_generated_label': True,
                'generation_timestamp': datetime.utcnow().isoformat(),
                'person_id': str(visitor.get('person_id', '')),
                'task_id': str(visitor_context.scenario_info.fam_id),  # Using fam_id as task_id
                'raw_content': raw_content
            }
            
            self.log_activity(f"Generated comprehensive note for {visitor.get('email', 'unknown visitor')}")
            return ai_note

        except Exception as e:
            self.log_activity(f"Error generating comprehensive note: {str(e)}", "error")
            raise

    def _create_raw_content(self, visitor: Dict[str, Any], profile_analysis: Dict[str, Any], 
                           family_analysis: Dict[str, Any], sentiment_analysis: Dict[str, Any], 
                           recommendations: Dict[str, Any], contact_info: Dict[str, Any]) -> str:
        """Create formatted raw content for display."""
        
        content_parts = [
            f"# Visitor Follow-up Note",
            f"",
            f"## Visitor Information",
            f"**Name:** {visitor.get('first_name', '')} {visitor.get('last_name', '')}",
            f"**Email:** {visitor.get('email', 'Not provided')}",
            f"**Phone:** {visitor.get('phone', 'Not provided')}",
            f"**Best Contact Time:** {contact_info.get('best_time', 'Not specified')}",
            f"",
            f"## Key Interests",
            f"{', '.join(profile_analysis.get('interests', ['General Fellowship']))}",
            f"",
            f"## Family Context",
            f"{family_analysis.get('context', 'Individual visitor')}",
            f"",
            f"## Sentiment Analysis",
            f"**Overall Sentiment:** {sentiment_analysis.get('overall_sentiment', 'Neutral')}",
            f"**Confidence:** {sentiment_analysis.get('confidence', 0.5):.0%}",
            f"**Key Emotions:** {', '.join(sentiment_analysis.get('key_emotions', ['Curious']))}",
            f"",
            f"## Recommended Next Steps",
            f"",
            f"### Church Community Integration",
        ]
        
        # Handle both string and dict recommendations for display
        community_recs = recommendations.get('community_integration', [])
        if isinstance(community_recs, list):
            for rec in community_recs:
                if isinstance(rec, str):
                    content_parts.append(f"- {rec}")
                elif isinstance(rec, dict):
                    content_parts.append(f"- {rec.get('title', rec.get('description', str(rec)))}")
        
        content_parts.extend([
            f"",
            f"### Event Engagement",
        ])
        
        event_recs = recommendations.get('event_engagement', [])
        if isinstance(event_recs, list):
            for rec in event_recs:
                if isinstance(rec, str):
                    content_parts.append(f"- {rec}")
                elif isinstance(rec, dict):
                    content_parts.append(f"- {rec.get('title', rec.get('description', str(rec)))}")
        
        content_parts.extend([
            f"",
            f"### Personal Needs Response",
        ])
        
        personal_needs = recommendations.get('personal_needs')
        if personal_needs:
            if isinstance(personal_needs, str):
                content_parts.append(f"- {personal_needs}")
            elif isinstance(personal_needs, dict):
                content_parts.append(f"- {personal_needs.get('summary', str(personal_needs))}")
        
        content_parts.extend([
            f"",
            f"### Feedback Insights",
        ])
        
        feedback_insights = recommendations.get('feedback_insights')
        if feedback_insights:
            if isinstance(feedback_insights, str):
                content_parts.append(f"- {feedback_insights}")
            elif isinstance(feedback_insights, dict):
                content_parts.append(f"- {feedback_insights.get('action_step', str(feedback_insights))}")
        
        content_parts.extend([
            f"",
            f"---",
            f"*This note was generated by AI on {datetime.now().strftime('%Y-%m-%d at %H:%M')}*"
        ])
        
        return "\n".join(content_parts)

    async def _analyze_visitor_profile(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """Analyze visitor profile data to extract key interests and characteristics."""
        visitor = visitor_context.visitor_profile
        welcome_form = visitor_context.visitor_welcome_form
        
        prompt = f"""
        Analyze this church visitor's profile and welcome form data:
        
        VISITOR PROFILE:
        - Name: {visitor.get('first_name', '')} {visitor.get('last_name', '')}
        - Email: {visitor.get('email', '')}
        - Phone: {visitor.get('phone', '')}
        - First Time Visit: {visitor.get('first_time_visit', True)}
        - Visit Date: {visitor.get('visit_date', '')}
        
        WELCOME FORM DATA:
        {json.dumps(welcome_form, indent=2) if welcome_form else "No welcome form data available"}
        
        FIRST TIMER NOTES:
        {json.dumps(visitor_context.first_timer_notes, indent=2) if visitor_context.first_timer_notes else "No first timer notes available"}
        
        Extract and analyze:
        1. Key interests mentioned or implied
        2. Ministry areas they might be interested in
        3. Life stage indicators (young professional, family with kids, retiree, etc.)
        4. Spiritual background or experience level
        5. Any specific needs or requests mentioned
        
        Return as JSON with keys: interests, ministry_areas, life_stage, spiritual_background, specific_needs
        """
        
        # messages = [
        #     SystemMessage(content="You are a church visitor analyst. Analyze visitor data to identify key interests and characteristics."),
        #     HumanMessage(content=prompt)
        # ]
        
        response = await self.model.generate_content(prompt)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return {
                'interests': ['General Fellowship'],
                'ministry_areas': ['Sunday Service'],
                'life_stage': 'Unknown',
                'spiritual_background': 'Unknown',
                'specific_needs': []
            }

    async def _analyze_family_context(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """Analyze family context and relationships."""
        scenario_info = visitor_context.scenario_info 
        family_members = visitor_context.family_members

        # Create family scenario attributes from scenario_info
        is_family_visit = "family" in scenario_info.scenario_type
        is_existing_family = "existing" in scenario_info.scenario_type
        family_member_count = len(scenario_info.family_members_to_query) if scenario_info.family_members_to_query else 1
        
        context_description = ""
        if is_family_visit:
            context_description = f"Family visit with {family_member_count} members. "
            # Analyze family_members data for children info
            children_count = 0
            for member in family_members:
                # Check if member has age or birth_date indicating child
                age = member.get('age')
                if age and int(age) < 18:
                    children_count += 1
            
            if children_count > 0:
                context_description += f"Family includes {children_count} children. "
            else:
                context_description += "Adult family members. "
        else:
            context_description = "Individual visit. "
        
        if is_existing_family:
            context_description += "Family has previous church connections."
        else:
            context_description += "New family to the church."
        
        return {
            'context': context_description,
            'is_family': is_family_visit,
            'member_count': family_member_count,
            'has_children': len([m for m in family_members if m.get('age') and int(m.get('age', 0)) < 18]) > 0,
            'children_count': len([m for m in family_members if m.get('age') and int(m.get('age', 0)) < 18]),
            'is_existing': is_existing_family
        }

    async def _perform_sentiment_analysis(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """Perform sentiment analysis on visitor feedback and interactions."""
        feedback_data = []
        
        # Collect feedback from various sources using correct field names
        if visitor_context.visitor_welcome_form:
            feedback_data.append(f"Welcome Form: {json.dumps(visitor_context.visitor_welcome_form)}")
        
        if visitor_context.first_timer_notes:
            feedback_data.append(f"First Timer Notes: {json.dumps(visitor_context.first_timer_notes)}")
        
        if visitor_context.prayer_requests:
            feedback_data.append(f"Prayer Requests: {json.dumps(visitor_context.prayer_requests)}")
        
        if visitor_context.existing_followup_notes:
            feedback_data.append(f"Existing Notes: {json.dumps(visitor_context.existing_followup_notes)}")
        
        if visitor_context.feedback_fields:
            feedback_data.append(f"Feedback Fields: {json.dumps(visitor_context.feedback_fields)}")
        
        if not feedback_data:
            return {
                'overall_sentiment': 'Neutral',
                'confidence': 0.5,
                'key_emotions': ['Curious'],
                'concerns': [],
                'positive_indicators': []
            }
        
        prompt = f"""
        Analyze the sentiment and emotional tone from this visitor's interactions:
        
        FEEDBACK DATA:
        {chr(10).join(feedback_data)}
        
        Provide sentiment analysis including:
        1. Overall sentiment (Positive, Neutral, Negative)
        2. Confidence score (0.0 to 1.0)
        3. Key emotions detected
        4. Any concerns or hesitations expressed
        5. Positive indicators or enthusiasm shown
        
        Return as JSON with keys: overall_sentiment, confidence, key_emotions, concerns, positive_indicators
        """
        
        messages = [
            SystemMessage(content="You are a sentiment analysis expert. Analyze visitor feedback to understand their emotional state and attitude."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.model.generate_content(prompt)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                'overall_sentiment': 'Positive',
                'confidence': 0.7,
                'key_emotions': ['Interested'],
                'concerns': [],
                'positive_indicators': ['Attended service']
            }

    async def _generate_recommendations(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """Generate structured recommendations based on acceptance criteria categories."""
        visitor = visitor_context.visitor_profile
        # Use correct field names from VisitorContextData schema
        available_teams = visitor_context.public_teams or []
        available_groups = visitor_context.public_groups or []
        upcoming_events = visitor_context.upcoming_events or []
        
        prompt = f"""
        Generate specific follow-up recommendations for this church visitor:
        
        VISITOR INFO:
        - Name: {visitor.get('first_name', '')} {visitor.get('last_name', '')}
        - First Time: {visitor.get('first_time_visit', True)}
        - Visit Date: {visitor.get('visit_date', '')}
        
        AVAILABLE OPPORTUNITIES:
        Teams: {[team.get('name', '') for team in available_teams]}
        Groups: {[group.get('name', '') for group in available_groups]}
        Upcoming Events: {[event.get('name', '') for event in upcoming_events]}
        
        CONTEXT:
        Welcome Form: {json.dumps(visitor_context.visitor_welcome_form) if visitor_context.visitor_welcome_form else "None"}
        Prayer Requests: {json.dumps(visitor_context.prayer_requests) if visitor_context.prayer_requests else "None"}
        
        Generate 2-3 specific recommendations for each category:
        
        1. CHURCH COMMUNITY INTEGRATION: Ways to help them connect with the church community
        2. EVENT ENGAGEMENT: Specific events or activities they should be invited to
        3. PERSONAL NEEDS RESPONSE: How to address any personal needs or prayer requests (return single string or null)
        4. FEEDBACK INSIGHT: Actions based on their feedback or expressed interests (return single string or null)
        
        Return as JSON with keys: community_integration, event_engagement, personal_needs, feedback_insights
        - community_integration and event_engagement should be arrays of strings
        - personal_needs should be a single string or null
        - feedback_insights should be a single string or null
        """
        
        # messages = [
        #     SystemMessage(content="You are a church engagement specialist. Generate specific, actionable recommendations for visitor follow-up."),
        #     HumanMessage(content=prompt)
        # ]
        
        response = await self.model.generate_content(prompt)
        
        try:
            result = json.loads(response.content)
            
            # Ensure personal_needs and feedback_insights are single values, not arrays
            if isinstance(result.get('personal_needs'), list):
                result['personal_needs'] = result['personal_needs'][0] if result['personal_needs'] else None
            
            if isinstance(result.get('feedback_insights'), list):
                result['feedback_insights'] = result['feedback_insights'][0] if result['feedback_insights'] else None
            
            return result
        except json.JSONDecodeError:
            return {
                'community_integration': ['Invite to newcomer lunch', 'Connect with greeter team'],
                'event_engagement': ['Invite to next Sunday service', 'Share upcoming events calendar'],
                'personal_needs': 'Follow up on any prayer requests or personal needs mentioned',
                'feedback_insights': 'Address any questions or feedback they provided'
            }

    async def _determine_optimal_contact(self, visitor_context: VisitorContextData, profile_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Determine the best time and method to contact the visitor."""
        # Use visitor_welcome_form instead of welcome_form_data
        welcome_form = visitor_context.visitor_welcome_form
        
        # Default contact preferences
        best_time = "Weekday evenings (6-8 PM)"
        preferred_method = "email"
        
        # Analyze life stage and adjust contact preferences
        life_stage = profile_analysis.get('life_stage', '').lower()
        
        if 'young professional' in life_stage:
            best_time = "Weekday evenings (7-9 PM) or weekends"
            preferred_method = "text or email"
        elif 'family' in life_stage or 'parent' in life_stage:
            best_time = "Weekend mornings or weekday evenings after 7 PM"
            preferred_method = "email or phone"
        elif 'retiree' in life_stage or 'senior' in life_stage:
            best_time = "Weekday mornings (9 AM - 12 PM)"
            preferred_method = "phone or email"
        
        return {
            'best_time': best_time,
            'preferred_method': preferred_method,
            'alternative_methods': ['email', 'phone', 'text'] if preferred_method != 'email' else ['phone', 'text']
        }

    def _calculate_confidence_score(self, visitor_context: VisitorContextData, analysis_tasks: List[Any]) -> float:
        """Calculate confidence score based on data completeness and analysis quality."""
        base_score = 0.5
        
        # Increase confidence based on available data using correct field names
        if visitor_context.visitor_welcome_form:
            base_score += 0.15
        if visitor_context.first_timer_notes:
            base_score += 0.1
        if visitor_context.prayer_requests:
            base_score += 0.1
        if visitor_context.existing_followup_notes:
            base_score += 0.1
        if visitor_context.feedback_fields:
            base_score += 0.05
        if visitor_context.public_teams:
            base_score += 0.05
        if visitor_context.public_groups:
            base_score += 0.05
        if visitor_context.upcoming_events:
            base_score += 0.05
        
        # Reduce confidence if any analysis tasks failed
        failed_tasks = sum(1 for task in analysis_tasks if isinstance(task, Exception))
        if failed_tasks > 0:
            base_score -= (failed_tasks * 0.1)
        
        return min(max(base_score, 0.3), 0.95)  # Clamp between 0.3 and 0.95

    def _get_data_sources_used(self, visitor_context: VisitorContextData) -> List[str]:
        """Get list of data sources that were used in the analysis."""
        sources = ['visitor_profile']
        
        # Use correct field names from VisitorContextData schema
        if visitor_context.visitor_welcome_form:
            sources.append('visitor_welcome_form')
        if visitor_context.first_timer_notes:
            sources.append('first_timer_notes')
        if visitor_context.prayer_requests:
            sources.append('prayer_requests')
        if visitor_context.existing_followup_notes:
            sources.append('existing_followup_notes')
        if visitor_context.feedback_fields:
            sources.append('feedback_fields')
        if visitor_context.public_teams:
            sources.append('public_teams')
        if visitor_context.public_groups:
            sources.append('public_groups')
        if visitor_context.upcoming_events:
            sources.append('upcoming_events')
        
        return sources

    # async def generate_note(self, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Legacy method for backward compatibility.
    #     Converts old format to new VisitorContextData and generates note.
    #     """
    #     try:
    #         # Convert legacy format to new VisitorContextData
    #         visitor_context = self._convert_legacy_data(visitor_data)
            
    #         # Generate comprehensive note
    #         ai_note = await self.generate_comprehensive_note(visitor_context)
            
    #         # Convert to legacy format for backward compatibility
    #         legacy_note = self._convert_to_legacy_format(ai_note)
            
    #         return legacy_note

    #     except Exception as e:
    #         self.log_activity(f"Error in legacy generate_note: {str(e)}", "error")
    #         raise

    # def _convert_legacy_data(self, visitor_data: Dict[str, Any]) -> VisitorContextData:
    #     """Convert legacy visitor data format to new VisitorContextData structure."""
    #     # This is a simplified conversion - adjust based on actual legacy format
    #     visitor = visitor_data.get('visitor', {})
        
    #     # Create mock VisitorContextData for backward compatibility
    #     from app.api.schemas.event_schemas import FamilyScenario
        
    #     family_scenario = FamilyScenario(
    #         scenario_type="individual_new",
    #         primary_person_id=str(visitor.get('id', 0)),
    #         family_members_to_query=[str(visitor.get('id', 0))],
    #         fam_id=str(visitor.get('fam_id', 'unknown')),
    #         context_strategy="focus_on_individual_new_member"
    #     )
        
    #     return VisitorContextData(
    #         visitor_profile=visitor,
    #         visitor_welcome_form=visitor_data.get('welcome_form', {}),
    #         family_members=[],
    #         first_timer_notes=visitor_data.get('first_timer_notes', []),
    #         prayer_requests=visitor_data.get('prayer_requests', []),
    #         existing_followup_notes=visitor_data.get('existing_notes', []),
    #         feedback_fields=visitor_data.get('feedback_fields', []),
    #         public_teams=visitor_data.get('teams', []),
    #         public_groups=visitor_data.get('groups', []),
    #         upcoming_events=visitor_data.get('events', []),
    #         scenario_info=family_scenario
    #     )

    # def _convert_to_legacy_format(self, ai_note: Dict[str, Any]) -> Dict[str, Any]:
    #     """Convert new AI note format to legacy format for backward compatibility."""
    #     now = datetime.now()
        
    #     # Create legacy format structure
    #     legacy_note = {
    #         'visitor_name': ai_note.get('visitor_full_name', ''),
    #         'email': ai_note.get('visitor_email', ''),
    #         'phone': ai_note.get('visitor_phone', ''),
    #         'best_contact_time': ai_note.get('best_contact_time', ''),
    #         'interests': ai_note.get('key_interests_summary', []),
    #         'family_context': ai_note.get('family_context_info', ''),
    #         'sentiment': ai_note.get('sentiment_analysis', {}),
    #         'recommendations': {
    #             'community_integration': ai_note.get('church_integration_recommendations', []),
    #             'event_engagement': ai_note.get('event_engagement_recommendations', []),
    #             'personal_needs': ai_note.get('personal_needs_response', []),
    #             'feedback_insights': ai_note.get('feedback_insight', [])
    #         },
    #         'confidence_score': 0.85,  # Default confidence
    #         'generated_at': now.isoformat(),
    #         'raw_content': ai_note.get('raw_content', '')
    #     }
        
    #     return legacy_note
