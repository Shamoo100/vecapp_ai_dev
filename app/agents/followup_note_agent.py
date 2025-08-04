from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import re
import json
import asyncio
import os
import logging
from dotenv import load_dotenv
from google import genai
from .base_agent import BaseAgent
from app.api.schemas.event_schemas import AIGeneratedNoteStructure, VisitorContextData
from app.llm.prompts import PromptLibrary
from langsmith import trace

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class FollowupNoteAgent(BaseAgent):
    """
    AI agent for generating comprehensive visitor follow-up notes using Google Gemini API.
    Handles visitor profile analysis, sentiment analysis, and recommendation generation.
    """
    
    def __init__(self, agent_id: str, schema: str):
        """
        Initialize the followup note agent.
        
        Args:
            agent_id (str): Unique identifier for this agent instance
            schema (str): Schema version for data validation
        """
        super().__init__(agent_id, schema)
        self.prompts = PromptLibrary()
        self.model = "gemini-2.5-flash"
        self.temperature = 0.3  # Add temperature control
        
        # Initialize Gemini client with API key from environment
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        try:
            self.client = genai.Client(api_key=gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method that generates comprehensive visitor follow-up notes.
        
        Args:
            data (Dict[str, Any]): Raw visitor context data
            
        Returns:
            Dict[str, Any]: Processed data with AI-generated insights
        """
        try:
            visitor_context = VisitorContextData(**data)
            ai_note = await self.generate_comprehensive_note(visitor_context)
            
            # Safely extract person_id from visitor_profile
            visitor_profile = visitor_context.visitor_profile or {}
            person_id = visitor_profile.get("person_id", "")
            
            processed_data = {
                "visitor_id": person_id,
                "schema": self.schema,
                "ai_note": ai_note,
                "generation_metadata": {
                    "agent_id": self.agent_id,
                    "model_version": self.model,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "confidence_score": ai_note.get("confidence_score", 0.85)
                }
            }
            
            self.log_activity(f"Generated comprehensive note for visitor {person_id}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing visitor data: {e}")
            raise
    
    async def generate_comprehensive_note(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Generate a comprehensive follow-up note by analyzing multiple aspects of visitor data.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context information
        
        Returns:
            Dict[str, Any]: Structured AI-generated note with recommendations
        """
        try:
            # Log data availability for debugging (use logger instead of print)
            logger.debug(f"Processing visitor context with {len(visitor_context.public_teams or [])} teams, "
                        f"{len(visitor_context.public_groups or [])} groups, "
                        f"{len(visitor_context.upcoming_events or [])} events")
            
            # Extract and consolidate visitor data
            visitor_data = self._extract_visitor_data(visitor_context)
            
            # Execute parallel analysis tasks with proper error handling
            analysis_results = await self._perform_parallel_analysis(visitor_context)
            
            # Generate contact strategy
            contact_info = await self._determine_optimal_contact(visitor_context, analysis_results['profile'])
            
            # Create summaries
            natural_summary = self._create_natural_language_summary(
                visitor_data, analysis_results['profile'], 
                analysis_results['family'], analysis_results['sentiment']
            )
            
            raw_content = self._create_raw_content(
                visitor_data, analysis_results, contact_info, natural_summary
            )
            
            # Build final AI note structure
            ai_note = self._build_ai_note_structure(
                visitor_data, analysis_results, contact_info, 
                natural_summary, raw_content, visitor_context
            )
            
            self.log_activity(f"Generated comprehensive note for {visitor_data.get('email', 'unknown visitor')}")
            return ai_note
            
        except Exception as e:
            logger.error(f"Error generating comprehensive note: {e}")
            # Return a minimal fallback note
            return self._create_fallback_note(visitor_context)

    def _extract_visitor_data(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Extract and consolidate visitor data from various sources.(mainly welcome form)
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context
            
        Returns:
            Dict[str, Any]: Consolidated visitor data
        """
        visitor_profile = visitor_context.visitor_profile or {}
        welcome_form_data = visitor_context.visitor_welcome_form or {}
        
        # Extract nested data safely
        person_info = welcome_form_data.get('person_info', {})
        visit_info = welcome_form_data.get('visit_info', {})
        spiritual_info = welcome_form_data.get('spiritual_info', {})
        
        return {
            # Personal information
            "title": person_info.get('title', ''),
            "first_name": person_info.get('first_name', ''),
            "middle_name": person_info.get('middle_name', ''),
            "last_name": person_info.get('last_name', ''),
            "gender": person_info.get('gender', ''),
            "race": person_info.get('race', ''),
            "occupation": person_info.get('occupation', ''),
            "email": person_info.get('email', ''),
            "phone": person_info.get('phone', ''),
            "person_id": person_info.get('id', ''),
            "address": person_info.get('address', {}),
            
            # Visit information
            "visit_date": self._format_visit_date(visit_info.get('visit_date', '')),
            "how_heard_about_church": visit_info.get('how_heard_about_church', ''),
            "recently_relocated": visit_info.get('recently_relocated', ''),
            "best_contact_time": visit_info.get('best_contact_time', ''),
            "preferred_communication_method": visit_info.get('preferred_communication_method', ''),
            "joined_via": visit_info.get('joined_via', ''),
            "considering_joining": visit_info.get('considering_joining', ''),
            "joining_our_church": visit_info.get('joining_our_church', ''),
            
            # Spiritual information
            "spiritual_need": spiritual_info.get('spiritual_need', ''),
            "spiritual_challenge": spiritual_info.get('spiritual_challenge', ''),
            "prayer_request": spiritual_info.get('prayer_request', ''),
            "feedback": spiritual_info.get('feedback', ''),
            "interested_in_devotional": spiritual_info.get('interested_in_daily_devotional', ''),
            
            # Additional data
            "interests": welcome_form_data.get('interests', {}),
            "profile": visitor_profile,
            "welcome_form": welcome_form_data
        }

    async def _perform_parallel_analysis(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Perform parallel analysis tasks with proper error handling.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context
            
        Returns:
            Dict[str, Any]: Analysis results with fallbacks
        """
        # Define default values for failed tasks
        default_values = {
            'profile': {
                "interests": ["General Fellowship"],
                "ministry_areas": ["Sunday Service"],
                "life_stage": "Unknown",
                "spiritual_background": "Unknown",
                "specific_needs": [],
                "engagement_level": "medium",
                "follow_up_priority": "medium"
            },
            'family': {
                "context": "Individual visit",
                "is_family": False,
                "member_count": 1,
                "has_children": False,
                "children_count": 0,
                "is_existing": False
            },
            'sentiment': {
                "overall_sentiment": "Neutral",
                "confidence": 0.5,
                "key_emotions": ["Curious"],
                "concerns": [],
                "positive_indicators": []
            },
            'recommendations': {
                "community_integration": [],
                "event_engagement": [],
                "personal_needs": None,
                "feedback_insights": None
            }
        }
        
        try:
            # Execute parallel analysis tasks
            analysis_tasks = await asyncio.gather(
                self._analyze_visitor_profile(visitor_context),
                self._analyze_family_context(visitor_context),
                self._perform_sentiment_analysis(visitor_context),
                self._generate_recommendations(visitor_context),
                return_exceptions=True
            )
            
            # Process results with fallbacks for exceptions
            task_names = ['profile', 'family', 'sentiment', 'recommendations']
            results = {}
            
            for i, (task_name, task_result) in enumerate(zip(task_names, analysis_tasks)):
                if isinstance(task_result, Exception):
                    logger.warning(f"Analysis task '{task_name}' failed: {task_result}")
                    results[task_name] = default_values[task_name]
                else:
                    results[task_name] = task_result
            
            return results
            
        except Exception as e:
            logger.error(f"Error in parallel analysis: {e}")
            return default_values

    def _build_ai_note_structure(
        self, 
        visitor_data: Dict[str, Any], 
        analysis_results: Dict[str, Any], 
        contact_info: Dict[str, Any],
        natural_summary: str, 
        raw_content: str, 
        visitor_context: VisitorContextData
    ) -> Dict[str, Any]:
        """
        Build the final AI note structure with all required fields.
        
        Args:
            visitor_data: Consolidated visitor data
            analysis_results: Results from parallel analysis
            contact_info: Optimal contact strategy
            natural_summary: Natural language summary
            raw_content: Formatted raw content
            visitor_context: Original visitor context
            
        Returns:
            Dict[str, Any]: Complete AI note structure
        """
        # Transform recommendations to match schema requirements
        recommendations = analysis_results['recommendations']
        
        church_integration_recs = self._transform_recommendations(
            recommendations.get("community_integration", []), "community_integration"
        )
        event_engagement_recs = self._transform_recommendations(
            recommendations.get("event_engagement", []), "event_engagement"
        )
        
        # Process personal needs and feedback insights
        personal_needs_response = self._process_personal_needs(recommendations.get("personal_needs"))
        feedback_insight = self._process_feedback_insights(recommendations.get("feedback_insights"))
        
        # Build the complete AI note
        ai_note = {
            # Basic visitor information
            "visitor_full_name": self._format_full_name(visitor_data),
            "visitor_phone": visitor_data.get("phone", ""),
            "visitor_email": visitor_data.get("email", ""),
            "first_visit": self._format_visit_date_for_output(visitor_data.get("visit_date")),
            "best_contact_time": visitor_data.get("best_contact_time", ""),
            "channel_to_contact": visitor_data.get("preferred_communication_method", ""),
            
            # Analysis results
            "key_interests_summary": analysis_results['profile'].get("interests", []),
            "family_context_info": analysis_results['family'].get("context", ""),
            "sentiment_analysis": analysis_results['sentiment'],
            
            # Recommendations
            "church_integration_recommendations": church_integration_recs,
            "event_engagement_recommendations": event_engagement_recs,
            "personal_needs_response": personal_needs_response,
            "feedback_insight": feedback_insight,
            
            # Metadata
            "ai_generated_label": True,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "person_id": str(visitor_data.get("person_id", "")),
            "fam_id": str(visitor_context.scenario_info.fam_id) if visitor_context.scenario_info else "",
            
            # Content
            "raw_content": raw_content,
            "natural_summary": natural_summary,
            
            # Compatibility aliases
            "email": visitor_data.get("email", ""),
            "phone": visitor_data.get("phone", ""),
            "key_interests": analysis_results['profile'].get("interests", []),
            "family_context": analysis_results['family'].get("context", ""),
            
            # Additional metadata
            "confidence_score": analysis_results['sentiment'].get("confidence", 0.85),
            "data_sources_used": self._get_data_sources_used(visitor_context),
            "recommended_next_steps": self._format_next_steps(
                church_integration_recs, event_engagement_recs, 
                personal_needs_response, feedback_insight
            )
        }
        
        return ai_note

    def _process_personal_needs(self, personal_needs: Any) -> Optional[Dict[str, Any]]:
        """Process personal needs response into structured format."""
        if not personal_needs:
            return None
            
        if isinstance(personal_needs, str):
            return {
                "type": "personal_needs",
                "summary": personal_needs,
                "action_required": True,
                "escalation_required": False
            }
        elif isinstance(personal_needs, dict):
            return personal_needs
        return None

    def _process_feedback_insights(self, feedback_insights: Any) -> Optional[Dict[str, Any]]:
        """Process feedback insights into structured format."""
        if not feedback_insights:
            return None
            
        if isinstance(feedback_insights, str):
            return {
                "type": "feedback_insight",
                "tone": "positive",
                "category": "general",
                "action_step": feedback_insights
            }
        elif isinstance(feedback_insights, dict):
            return feedback_insights
        return None


    def _create_natural_language_summary(
        self, 
        visitor_data: Dict[str, Any], 
        profile_analysis: Dict[str, Any], 
        family_analysis: Dict[str, Any], 
        sentiment_analysis: Dict[str, Any]
    ) -> str:
        """
        Create a natural language summary of the visitor.
        
        Args:
            visitor_data: Consolidated visitor data
            profile_analysis: Analyzed visitor interests and characteristics
            family_analysis: Family context information
            sentiment_analysis: Emotional sentiment analysis
            
        Returns:
            str: Natural language summary
        """
        first_name = visitor_data.get('first_name', 'This visitor')
        last_name = visitor_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        # Use more sophisticated title determination
        title = self._determine_title(visitor_data)
        
        summary_parts = []
        
        # Basic introduction
        if family_analysis.get('is_family', False):
            if family_analysis.get('has_children', False):
                summary_parts.append(f"{title} {full_name} is a new member of our community who visited with their family, including children.")
            else:
                summary_parts.append(f"{title} {full_name} is a new member of our community who visited with their family.")
        else:
            summary_parts.append(f"{title} {full_name} is a new member of our community who visited our church.")
        
        # Add sentiment and experience
        sentiment = sentiment_analysis.get('overall_sentiment', 'neutral').lower()
        if sentiment == 'positive':
            summary_parts.append("They enjoyed their visit and had a positive experience with our service.")
        elif sentiment == 'negative':
            summary_parts.append("They had some concerns during their visit that we should address.")
        else:
            summary_parts.append("They had a good experience and are interested in learning more about our community.")
        
        # Add interests
        interests = profile_analysis.get('interests', [])
        if interests:
            if len(interests) == 1:
                summary_parts.append(f"They expressed particular interest in {interests[0].lower()}.")
            else:
                interest_list = ', '.join(interests[:-1]) + f" and {interests[-1]}"
                summary_parts.append(f"They expressed interest in {interest_list.lower()}.")
        
        # Add how they heard about the church
        how_heard = visitor_data.get('how_heard_about_church', '')
        if how_heard:
            summary_parts.append(f"They learned about our church through {how_heard.lower()}.")
        
        return " ".join(summary_parts)


    def _create_raw_content(
        self, 
        visitor_data: Dict[str, Any], 
        analysis_results: Dict[str, Any], 
        contact_info: Dict[str, Any],
        natural_summary: str = ""
    ) -> str:
        """
        Create formatted markdown content for display in the UI.
        
        Args:
            visitor_data: Consolidated visitor data
            analysis_results: Results from parallel analysis
            contact_info: Optimal contact strategy
            natural_summary: Natural language summary of the visitor
            
        Returns:
            str: Formatted markdown content
        """
        content_parts = [
            "=== AI-Generated Visitor Follow-up Summary ===",
            "",
        ]
        
        if natural_summary:
            content_parts.extend([natural_summary, ""])
        
        content_parts.extend([
            "VISITOR INFORMATION:",
            f"Name: {visitor_data.get('first_name', '')} {visitor_data.get('last_name', '')}",
            f"Email: {visitor_data.get('email', '')}",
            f"Phone: {visitor_data.get('phone', '')}",
            f"Best Contact Time: {visitor_data.get('best_contact_time', 'Weekday evenings (6 PM - 8 PM)')}",
            f"Channel To Contact Them: {visitor_data.get('preferred_communication_method', 'Email')}",
            f"First Visit: {visitor_data.get('visit_date', '')}",
            "",
            "KEY INTERESTS:",
            f"{', '.join(analysis_results['profile'].get('interests', ['General Fellowship']))}",
            "",
            "FAMILY CONTEXT:",
            f"{analysis_results['family'].get('context', 'Individual visitor')}",
            "",
            "SENTIMENT ANALYSIS:",
            f"Overall: {analysis_results['sentiment'].get('overall_sentiment', 'Neutral')}",
            f"Confidence: {analysis_results['sentiment'].get('confidence', 0.5)*100:.0f}%",
            "",
            f"RECOMMENDED NEXT STEPS: {analysis_results['recommendations']}",
            "",
            "=== Generation Metadata ===",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Confidence Score: {analysis_results['sentiment'].get('confidence', 0.85):.2f}",
            "",
            "[This note was automatically generated by AI and may require review]"
        ])
        
        return "\n".join(content_parts)

    
    async def _analyze_visitor_profile(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Analyze visitor profile to extract interests, ministry areas, and engagement level.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context
            
        Returns:
            Dict[str, Any]: Analyzed profile data
        """
        try:
            visitor_profile = visitor_context.visitor_profile or {}
            welcome_form = visitor_context.visitor_welcome_form or {}
            
            # Extract visitor data for analysis
            person_info = welcome_form.get('person_info', {})
            visit_info = welcome_form.get('visit_info', {})
            spiritual_info = welcome_form.get('spiritual_info', {})
            
            prompt = f"""
            Analyze this visitor profile and provide insights:
            
            VISITOR DATA:
            - Name: {person_info.get('first_name', '')} {person_info.get('middle_name', '')} {person_info.get('last_name', '')}
            - Gender: {person_info.get('gender', '')}
            - Occupation: {person_info.get('occupation', '')}
            - Recently Relocated: {person_info.get('recently_relocated', '')}
            - How they heard about church: {visit_info.get('how_heard_about_church', '')}
            - Considering joining: {visit_info.get('considering_joining', '')}
            - Spiritual need: {spiritual_info.get('spiritual_need', '')}
            - Prayer request: {spiritual_info.get('prayer_request', '')}
            - Feedback: {spiritual_info.get('feedback', '')}
            - Interested In Getting Daily Devosionals: {spiritual_info.get('interest_in_daily_devotional', '')}
            
            Provide analysis as valid JSON only (no markdown) with these exact keys:
            {{
                "interests": ["list of inferred interests"],
                "ministry_areas": ["relevant ministry areas"],
                "life_stage": "inferred life stage",
                "spiritual_background": "assessment of spiritual background",
                "specific_needs": ["identified specific needs"],
                "engagement_level": "low/medium/high",
                "follow_up_priority": "low/medium/high"
            }}
            """
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model, 
                    contents=prompt,
                    config={"temperature": self.temperature}
                )
            )
            
            parsed_response = self._extract_json_from_response(response.text)
            
            if parsed_response:
                logger.debug(f"Profile analysis completed: {parsed_response}")
                return parsed_response
            else:
                logger.warning("Failed to parse profile analysis response")
                return self._create_fallback_profile_analysis()
                
        except Exception as e:
            logger.error(f"Error analyzing visitor profile: {e}")
            return self._create_fallback_profile_analysis()

    async def _analyze_family_context(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Analyze family context and relationships.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context
            
        Returns:
            Dict[str, Any]: Family context analysis results
        """
        try:
            scenario_info = visitor_context.scenario_info 
            family_members = visitor_context.family_members or []

            # Determine family context from scenario info
            is_family_visit = "family" in (scenario_info.scenario_type if scenario_info else "")
            is_existing_family = "existing" in (scenario_info.scenario_type if scenario_info else "")
            family_member_count = len(scenario_info.family_members_to_query) if scenario_info and scenario_info.family_members_to_query else 1
            
            # Count children from family members
            children_count = sum(1 for member in family_members 
                               if member.get('age') and int(member.get('age', 0)) < 18)
            
            # Build context description
            if is_family_visit:
                context_description = f"Family visit with {family_member_count} members. "
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
                'has_children': children_count > 0,
                'children_count': children_count,
                'is_existing': is_existing_family
            }
            
        except Exception as e:
            logger.error(f"Error analyzing family context: {e}")
            return {
                'context': "Individual visit",
                'is_family': False,
                'member_count': 1,
                'has_children': False,
                'children_count': 0,
                'is_existing': False
            }

    async def _perform_sentiment_analysis(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Perform sentiment analysis on visitor feedback and interactions.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context
            
        Returns:
            Dict[str, Any]: Sentiment analysis results
        """
        try:
            welcome_form = visitor_context.visitor_welcome_form or {}
            spiritual_info = welcome_form.get('spiritual_info', {})
            
            feedback = spiritual_info.get('feedback', '')
            prayer_request = spiritual_info.get('prayer_request', '')
            
            prompt = f"""
            Analyze the sentiment and emotional tone of this visitor's feedback:
            
            FEEDBACK: "{feedback}"
            PRAYER REQUEST: "{prayer_request}"
            
            Provide sentiment analysis as valid JSON only (no markdown) with these exact keys:
            {{
                "overall_sentiment": "Positive/Neutral/Negative",
                "confidence": 0.85,
                "key_emotions": ["list of detected emotions"],
                "concerns": ["any concerns identified"],
                "positive_indicators": ["positive aspects mentioned"]
            }}
            """
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model, 
                    contents=prompt,
                    config={"temperature": self.temperature}
                )
            )
            
            parsed_response = self._extract_json_from_response(response.text)
            
            if parsed_response:
                logger.debug(f"Sentiment analysis completed: {parsed_response}")
                return parsed_response
            else:
                logger.warning("Failed to parse sentiment analysis response")
                return self._create_fallback_sentiment_analysis()
                
        except Exception as e:
            logger.error(f"Error performing sentiment analysis: {e}")
            return self._create_fallback_sentiment_analysis()

    async def _generate_recommendations(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Generate structured recommendations for visitor follow-up using Gemini API.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context
            
        Returns:
            Dict[str, Any]: Structured recommendations by category
        """
        try:
            visitor_profile = visitor_context.visitor_profile or {}
            welcome_form = visitor_context.visitor_welcome_form or {}
            person_info = welcome_form.get('person_info', {})

            available_teams = visitor_context.public_teams or []
            available_groups = visitor_context.public_groups or []
            upcoming_events = visitor_context.upcoming_events or []
            
            logger.debug(f"Generating recommendations with {len(available_teams)} teams, "
                        f"{len(available_groups)} groups, {len(upcoming_events)} events")
            
            # Extract names from available opportunities
            team_names = self._extract_opportunity_names(available_teams)
            group_names = self._extract_opportunity_names(available_groups)
            event_names = self._extract_opportunity_names(upcoming_events)
            
            prompt = f"""
            Generate specific follow-up recommendations for this church visitor:

            VISITOR INFO:
            - Name: {person_info.get('first_name', '')} {person_info.get('middle_name', '')} {person_info.get('last_name', '')}
            - First Time: {visitor_profile.get('first_time_visit', True)}
            - Welcome Form: {json.dumps(welcome_form, indent=2, default=str)}

            AVAILABLE OPPORTUNITIES:
            Teams: {team_names}
            Groups: {group_names}
            Events: {event_names}

            INSTRUCTIONS:
            - If teams/groups/events are available, recommend specific ones by name
            - If no specific opportunities are available, provide general recommendations
            - Base recommendations on visitor's interests and feedback
            - Consider prayer requests for personal needs
            - For event_engagement, provide recommendations as a comma-separated string, not individual characters

            Provide specific recommendations as valid JSON only (no markdown) with these exact keys:
            {{
                "community_integration": ["specific team or group suggestion"],
                "event_engagement": "comma-separated list of specific event recommendations",
                "personal_needs": "pastoral care suggestion based on prayer requests",
                "feedback_insights": "church improvement suggestion based on feedback"
            }}
            """
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model, 
                    contents=prompt,
                    config={"temperature": self.temperature}
                )
            )
            
            parsed_response = self._extract_json_from_response(response.text)
            
            if parsed_response:
                logger.debug(f"Generated recommendations: {parsed_response}")
                return parsed_response
            else:
                logger.warning("Failed to parse recommendations response")
                return self._create_fallback_recommendations(team_names, group_names, event_names)
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "community_integration": ["Connect with a small group"],
                "event_engagement": "Attend next Sunday service, Join upcoming church event",
                "personal_needs": None,
                "feedback_insights": None
            }

    
    async def _determine_optimal_contact(
        self, 
        visitor_context: VisitorContextData, 
        profile_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine the optimal contact strategy based on visitor preferences and profile.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context
            profile_analysis (Dict[str, Any]): Analyzed visitor profile
            
        Returns:
            Dict[str, Any]: Optimal contact strategy
        """
        try:
            welcome_form = visitor_context.visitor_welcome_form or {}
            visit_info = welcome_form.get('visit_info', {})
            
            # Extract contact preferences
            preferred_contact = visit_info.get('preferred_communication_method', 'email')
            preferred_time = visit_info.get('best_contact_time', 'weekday_evening')
            
            # Map time preferences to readable format
            time_mapping = {
                'weekday_morning': 'Weekday mornings (9 AM - 12 PM)',
                'weekday_afternoon': 'Weekday afternoons (1 PM - 5 PM)',
                'weekday_evening': 'Weekday evenings (6 PM - 8 PM)',
                'weekend_morning': 'Weekend mornings (9 AM - 12 PM)',
                'weekend_afternoon': 'Weekend afternoons (1 PM - 5 PM)',
                'weekend_evening': 'Weekend evenings (6 PM - 8 PM)'
            }
            
            # Determine urgency based on profile analysis
            urgency = "high" if profile_analysis.get('follow_up_priority') == "high" else "normal"
            follow_up_days = 2 if urgency == "high" else 3
            
            return {
                "method": preferred_contact,
                "best_time": time_mapping.get(preferred_time, 'Weekday evenings (6 PM - 8 PM)'),
                "urgency": urgency,
                "follow_up_days": follow_up_days
            }
            
        except Exception as e:
            logger.error(f"Error determining optimal contact: {e}")
            return {
                "method": "email",
                "best_time": "Weekday evenings (6 PM - 8 PM)",
                "urgency": "normal",
                "follow_up_days": 3
            }
    
    def _get_data_sources_used(self, visitor_context: VisitorContextData) -> List[str]:
        """Get list of data sources that were used in the analysis."""
        sources = ['visitor_profile']
        
        # Check each field and add to sources if present
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
        if visitor_context.family_members:
            sources.append('family_members')
        
        return sources

    ## Util functions ##
    def _determine_title(self, visitor_data: Dict[str, Any]) -> str:
        """
        Determine appropriate title based on visitor data.
        
        Args:
            visitor_data: Consolidated visitor data
            
        Returns:
            str: Appropriate title
        """
        title = visitor_data.get('title', '')
        first_name = visitor_data.get('first_name', '')
        
        if title:
            return title
            
        if not first_name or first_name == 'This visitor':
            return "This visitor"
            
        # Fallback to neutral
        return "This visitor"

    def _format_full_name(self, visitor_data: Dict[str, Any]) -> str:
        """Format visitor's full name consistently."""
        parts = [
            visitor_data.get('title', ''),
            visitor_data.get('first_name', ''),
            visitor_data.get('middle_name', ''),
            visitor_data.get('last_name', '')
        ]
        return ' '.join(part for part in parts if part).strip()

    def _format_visit_date_for_output(self, visit_date: Any) -> str:
        """Format visit date for output in AI note."""
        if isinstance(visit_date, datetime):
            return visit_date.isoformat()
        return str(visit_date) if visit_date else ""

    def _format_next_steps(
        self,
        church_integration_recs: list,
        event_engagement_recs: list,
        personal_needs_response: dict | None,
        feedback_insight: dict | None
    ) -> dict:
        """Format recommended next steps for service consumption."""

        def extract_titles(recs):
            titles = []
            if not recs:
                return titles
            if isinstance(recs, str):
                # Treat the whole string as one recommendation
                titles.append(recs.strip())
            elif isinstance(recs, list):
                for rec in recs:
                    if isinstance(rec, dict):
                        title = rec.get("title") or rec.get("description")
                        if title:
                            titles.append(title.strip())
                    elif isinstance(rec, str):
                        titles.append(rec.strip())
                    else:
                        titles.append(str(rec).strip())
            else:
                titles.append(str(recs).strip())
            return titles

        church_integration_list = extract_titles(church_integration_recs)
        event_engagement_list = extract_titles(event_engagement_recs)

        personal_needs_list = []
        if personal_needs_response:
            if isinstance(personal_needs_response, dict):
                summary = personal_needs_response.get("summary")
                if summary:
                    personal_needs_list.append(summary.strip())
            else:
                personal_needs_list.append(str(personal_needs_response).strip())

        feedback_insights_list = []
        if feedback_insight:
            if isinstance(feedback_insight, dict):
                action_step = feedback_insight.get("action_step")
                if action_step:
                    feedback_insights_list.append(action_step.strip())
            else:
                feedback_insights_list.append(str(feedback_insight).strip())

        return {
            "church_integration": church_integration_list,
            "event_engagement": event_engagement_list,
            "personal_needs": personal_needs_list,
            "feedback_insights": feedback_insights_list
        }

    def _extract_opportunity_names(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """
        Extract names from opportunity data structures.
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            List[str]: Extracted names
        """
        names = []
        name_fields = ['name', 'title', 'team_name', 'group_name', 'event_name']
        
        for item in opportunities:
            if isinstance(item, dict):
                for field in name_fields:
                    if field in item and item[field]:
                        names.append(str(item[field]))
                        break
                else:
                    # If no name field found, use string representation
                    names.append(str(item))
            else:
                names.append(str(item))
        
        return names

    def _transform_recommendations(self, recs: List[Any], rec_type: str) -> List[Dict[str, Any]]:
        """Transform recommendation data to match expected schema format."""
        result = []
        for rec in recs:
            if isinstance(rec, str):
                result.append({
                    "type": rec_type,
                    "title": rec,
                    "description": rec,
                    "priority": "medium"
                })
            elif isinstance(rec, dict):
                result.append(rec)
        return result

    def _format_visit_date(self, visit_date: Any) -> str:
        """
        Format visit date to string for schema compatibility.
        
        Args:
            visit_date: Visit date value (could be datetime, string, or None)
            
        Returns:
            str: Formatted date string
        """
        if not visit_date:
            return ""
        
        if isinstance(visit_date, datetime):
            return visit_date.strftime("%Y-%m-%d")
        elif isinstance(visit_date, str):
            return visit_date
        else:
            return str(visit_date)

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Gemini API response with improved parsing.
        
        Args:
            response_text (str): Raw response from Gemini API
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data or None if parsing fails
        """
        if not response_text:
            return None
            
        try:
            # First try direct JSON parsing
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_patterns = [
            r'```(?:json)?\s*(\{.*?\})\s*```',
            r'```(?:json)?\s*(\[.*?\])\s*```',
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        logger.warning(f"Failed to extract JSON from response: {response_text[:200]}...")
        return None


    # Fallback methods
    def _create_fallback_note(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Create a minimal fallback note when full processing fails.
        
        Args:
            visitor_context: Original visitor context
            
        Returns:
            Dict[str, Any]: Minimal AI note structure
        """
        visitor_profile = visitor_context.visitor_profile or {}
        welcome_form = visitor_context.visitor_welcome_form or {}
        person_info = welcome_form.get('person_info', {})
        
        return {
            "visitor_full_name": f"{person_info.get('first_name', '')} {person_info.get('last_name', '')}".strip(),
            "visitor_phone": person_info.get("phone", ""),
            "visitor_email": person_info.get("email", ""),
            "first_visit": str(welcome_form.get('visit_info', {}).get('visit_date', '')),
            "best_contact_time": "Weekday evenings (6 PM - 8 PM)",
            "channel_to_contact": "Email",
            "key_interests_summary": ["General Fellowship"],
            "family_context_info": "Individual visit",
            "sentiment_analysis": {
                "overall_sentiment": "Neutral",
                "confidence": 0.5,
                "key_emotions": ["Curious"],
                "concerns": [],
                "positive_indicators": []
            },
            "church_integration_recommendations": [],
            "event_engagement_recommendations": [],
            "personal_needs_response": None,
            "feedback_insight": None,
            "ai_generated_label": True,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "person_id": str(person_info.get("id", "")),
            "fam_id": "",
            "raw_content": "Fallback note generated due to processing error.",
            "natural_summary": "This visitor requires manual follow-up due to processing limitations.",
            "confidence_score": 0.5,
            "data_sources_used": ["visitor_profile"],
            "recommended_next_steps": {
                "church_integration": [],
                "event_engagement": [],
                "personal_needs": [],
                "feedback_insights": []
            }
        }

    def _create_fallback_recommendations(
        self, 
        team_names: List[str], 
        group_names: List[str], 
        event_names: List[str]
    ) -> Dict[str, Any]:
        """
        Create fallback recommendations when AI generation fails.
        
        Args:
            team_names: Available team names
            group_names: Available group names
            event_names: Available event names
            
        Returns:
            Dict[str, Any]: Fallback recommendations
        """
        community_recs = team_names[:2] if team_names else group_names[:2] if group_names else ["Connect with a small group", "Explore volunteer opportunities"]
        event_recs = event_names[:2] if event_names else ["Attend next Sunday service", "Join upcoming church event"]
        
        return {
            "community_integration": community_recs,
            "event_engagement": ", ".join(event_recs),  # Join as comma-separated string
            "personal_needs": None,
            "feedback_insights": None
        }

    def _create_fallback_profile_analysis(self) -> Dict[str, Any]:
        """
        Create fallback profile analysis when AI generation fails.
        
        Returns:
            Dict[str, Any]: Fallback profile analysis
        """
        return {
            "interests": ["General Fellowship"],
            "ministry_areas": ["Sunday Service"],
            "life_stage": "Unknown",
            "spiritual_background": "Unknown",
            "specific_needs": [],
            "engagement_level": "medium",
            "follow_up_priority": "medium"
        }

    def _create_fallback_sentiment_analysis(self) -> Dict[str, Any]:
        """
        Create fallback sentiment analysis when AI generation fails.
        
        Returns:
            Dict[str, Any]: Fallback sentiment analysis
        """
        return {
            "overall_sentiment": "Neutral",
            "confidence": 0.5,
            "key_emotions": ["Curious"],
            "concerns": [],
            "positive_indicators": []
        }