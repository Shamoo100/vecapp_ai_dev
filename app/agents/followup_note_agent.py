from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import re
import json
import asyncio
import logging
from dotenv import load_dotenv
from .base_agent import BaseAgent
from app.api.schemas.event_schemas import VisitorContextData
from app.llm.prompts import PromptLibrary

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class QualityResult:
    """Result of quality validation."""
    def __init__(self, passed: bool, score: float, issues: List[str]):
        self.passed = passed
        self.score = score
        self.issues = issues


class FollowupNoteAgent(BaseAgent):
    """
    AI agent for generating comprehensive visitor follow-up notes with fallbacks.
    """

    def __init__(self, agent_id: str, schema: str):
        super().__init__(agent_id, schema)
        self.prompts = PromptLibrary()
        self.temperature = 0.3
        logger.info(f"FollowupNoteAgent initialized: {agent_id}")

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method to generate AI follow-up notes.
        """
        try:
            visitor_context = VisitorContextData(**data)
            ai_note = await self.generate_comprehensive_note(visitor_context)

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
                    "confidence_score": ai_note.get("confidence_score", 0.85),
                },
            }
            self.log_activity(f"Generated note for visitor {person_id}")
            return processed_data

        except Exception as e:
            logger.error(f"Error processing visitor data: {e}")
            raise

    async def generate_comprehensive_note(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Generate a comprehensive AI note with fallbacks.
        """
        try:
            visitor_data = self._extract_visitor_data(visitor_context)
            analysis_results = await self._perform_parallel_analysis(visitor_context)
            contact_info = await self._determine_optimal_contact(
                visitor_context, analysis_results['profile']
            )
            natural_summary = self._create_natural_language_summary(
                visitor_data, analysis_results['profile'],
                analysis_results['family'], analysis_results['sentiment']
            )
            raw_content = self._create_raw_content(
                visitor_data, analysis_results, contact_info, natural_summary
            )

            ai_note = self._build_ai_note_structure(
                visitor_data, analysis_results, contact_info,
                natural_summary, raw_content, visitor_context
            )

            quality = self._validate_quality({
                "content": raw_content,
                "recommended_next_steps": ai_note.get("recommended_next_steps", {}),
                "ai_note": ai_note,
            })

            if not quality.passed:
                logger.warning(f"Quality issues detected: {quality.issues}")

            self.log_activity(f"Generated note for {visitor_data.get('email', 'unknown')}")

            return ai_note

        except Exception as e:
            logger.error(f"Error in comprehensive note generation: {e}")
            return self._create_fallback_note(visitor_context)

    def _extract_visitor_data(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """Extract and consolidate visitor data from welcome form and profile."""
        welcome_form = visitor_context.visitor_welcome_form or {}
        person_info = welcome_form.get('person_info', {})
        visit_info = welcome_form.get('visit_info', {})
        spiritual_info = welcome_form.get('spiritual_info', {})

        return {
            "title": person_info.get('title', ''),
            "first_name": person_info.get('first_name', ''),
            "middle_name": person_info.get('middle_name', ''),
            "last_name": person_info.get('last_name', ''),
            "address": person_info.get('address', {}),
            "gender": person_info.get('gender', ''),
            "race": person_info.get('race', ''),
            "occupation": person_info.get('occupation', ''),
            "email": person_info.get('email', ''),
            "phone": person_info.get('phone', ''),
            "person_id": person_info.get('id', ''),

            "visit_date": self._format_visit_date(visit_info.get('visit_date')),
            "how_heard_about_church": visit_info.get('how_heard_about_church', ''),
            "recently_relocated": visit_info.get('recently_relocated', ''),
            "best_contact_time": visit_info.get('best_contact_time', ''),
            "preferred_communication_method": visit_info.get('preferred_communication_method', ''),
            "joined_via": visit_info.get('joined_via', ''),
            "considering_joining": visit_info.get('considering_joining', ''),
            "joining_our_church": visit_info.get('joining_our_church', ''),

            "spiritual_need": spiritual_info.get('spiritual_need', ''),
            "spiritual_challenge": spiritual_info.get('spiritual_challenge', ''),
            "prayer_request": spiritual_info.get('prayer_request', ''),
            "feedback": spiritual_info.get('feedback', ''),
            "interested_in_devotional": spiritual_info.get('interested_in_daily_devotional', ''),

            "interests": welcome_form.get('interests', {}),
            "profile": visitor_context.visitor_profile,
            "welcome_form": welcome_form,
        }

    async def _perform_parallel_analysis(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """Run profile, family, sentiment, and recommendations in parallel."""
        defaults = {
            'profile': self._fallback_profile(),
            'family': self._fallback_family(visitor_context),
            'sentiment': self._fallback_sentiment(),
            'recommendations': self._fallback_recommendations(visitor_context),
        }

        tasks = [
            self._analyze_visitor_profile(visitor_context),
            self._analyze_family_context(visitor_context),
            self._perform_sentiment_analysis(visitor_context),
            self._generate_recommendations(visitor_context),
        ]

        results = {}
        for task_name, task, default in zip(defaults.keys(), tasks, defaults.values()):
            try:
                result = await task
                results[task_name] = result if result else default
            except Exception as e:
                logger.warning(f"Analysis failed for {task_name}: {e}")
                results[task_name] = default

        return results

    # --- ANALYSIS METHODS ---

    async def _analyze_visitor_profile(self, visitor_context: VisitorContextData) -> Optional[Dict[str, Any]]:
        try:
            visitor_data = self._extract_visitor_data(visitor_context)
            
            # Log input data quality
            logger.info(f"Analyzing visitor profile with data: {len(visitor_data)} fields")
            key_fields = ['first_name', 'email', 'phone', 'spiritual_need', 'interests']
            populated_fields = [field for field in key_fields if visitor_data.get(field)]
            logger.info(f"Key populated fields: {populated_fields}")
            
            # Generate prompt with better error handling
            try:
                prompt = self.prompts.get_visitor_profile_analysis_prompt(visitor_data, "First time visitor seeking spiritual growth")
                logger.debug(f"Generated prompt length: {len(prompt)} characters")
                
                # Add validation for prompt content
                if not prompt or len(prompt) < 100:
                    logger.error(f"Generated prompt is too short or empty: {len(prompt)} characters")
                    return self._fallback_profile()
                    
            except Exception as prompt_error:
                logger.error(f"Prompt generation failed: {prompt_error}", exc_info=True)
                return self._fallback_profile()
            
            # Enhanced LLM call with retry logic and adaptive token limits
            max_retries = 3
            base_tokens = 2500
            
            for attempt in range(max_retries + 1):
                try:
                    # Increase tokens on retry if previous attempt hit limit
                    token_limit = base_tokens + (attempt * 100)  # 1200, 1600, 2000
                    
                    response = await self.generate_llm_content(
                        prompt, 
                        max_tokens=token_limit, 
                        temperature=self.temperature
                    )
                    
                    logger.info(f"LLM response attempt {attempt + 1} (tokens: {token_limit}): {len(response) if response else 0} characters")
                    
                    if response and response.strip():
                        logger.debug(f"Raw LLM response: {response[:500]}...")
                        break
                    else:
                        logger.warning(f"Empty LLM response on attempt {attempt + 1}")
                        if attempt < max_retries:
                            await asyncio.sleep(1)  # Brief delay before retry
                            continue
                        else:
                            logger.error("All LLM attempts returned empty responses")
                            return self._fallback_profile()
                            
                except RuntimeError as e:
                    if "token limit" in str(e).lower() and attempt < max_retries:
                        logger.warning(f"Token limit hit on attempt {attempt + 1}, retrying with more tokens")
                        continue
                    else:
                        raise
                except Exception as llm_error:
                    logger.error(f"LLM call attempt {attempt + 1} failed: {llm_error}")
                    if attempt < max_retries:
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise
            
            # Enhanced JSON parsing
            parsed_response = self._parse_json_response(response)
            if not parsed_response:
                logger.warning(f"Failed to parse LLM response as JSON. Response: {response[:500]}...")
                # Try to extract partial data
                partial_data = self._extract_partial_json_data(response)
                if partial_data:
                    logger.info("Successfully extracted partial data from malformed JSON")
                    return partial_data
                return self._fallback_profile()
            
            logger.info(f"Successfully parsed visitor profile analysis: {list(parsed_response.keys())}")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Visitor profile analysis failed with exception: {e}", exc_info=True)
            return self._fallback_profile()

    async def _analyze_family_context(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        scenario_info = getattr(visitor_context, "scenario_info", None)
        if not scenario_info:
            return self._fallback_family(visitor_context)

        fam_id = getattr(scenario_info, "fam_id", None)
        family_head_id = getattr(scenario_info, "family_head_id", None)
        members_to_query = getattr(scenario_info, "family_members_to_query", [])
        scenario_type = (getattr(scenario_info, "scenario_type", "") or "").strip().lower()

        is_family = scenario_type.startswith("family")
        is_existing = "existing" in scenario_type

        family_members = list(visitor_context.family_members or [])
        member_count = len(family_members)  if is_family else 1

        def _is_child(m: Dict[str, Any]) -> bool:
            age = m.get("age")
            if age is not None:
                try:
                    return int(age) < 18
                except:
                    pass
            rel = (m.get("relationship") or m.get("relation") or "").lower()
            return rel in {"child", "son", "daughter"}

        children_count = sum(1 for m in family_members if isinstance(m, dict) and _is_child(m))

        context_desc = (
            f"{'Existing' if is_existing else 'New'} family visit with {member_count} member{'s' if member_count != 1 else ''}. "
            f"{'Includes children.' if children_count else 'All adults.'}"
            if is_family else "Individual visit."
        )

        return {
            "context": context_desc,
            "is_family": is_family,
            "is_existing": is_existing,
            "member_count": member_count,
            "has_children": children_count > 0,
            "children_count": children_count,
            "family_id": fam_id,
            "family_head_id": family_head_id,
            "family_members_to_query": members_to_query,
        }

    async def _perform_sentiment_analysis(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        visitor_data = self._extract_visitor_data(visitor_context)
        feedback = visitor_data.get("feedback", visitor_data.get("comments", ""))
        if not feedback.strip():
            return self._fallback_sentiment()

        try:
            prompt = self.prompts.get_sentiment_analysis_prompt({
                "feedback_text": feedback,
                "rating": visitor_data.get("rating"),
                "concerns": visitor_data.get("concerns", []),
                "positive_aspects": visitor_data.get("positive_feedback", [])
            }, "Historical context")
            response = await self.generate_llm_content(prompt, max_tokens=500, temperature=self.temperature)
            parsed = self._parse_json_response(response)
            return parsed if self._validate_sentiment_analysis(parsed) else self._fallback_sentiment()
        except Exception as e:
            logger.warning(f"Sentiment analysis failed, using fallback: {e}")
            return self._fallback_sentiment()

    async def _generate_recommendations(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        visitor_data = self._extract_visitor_data(visitor_context)
        teams = self._extract_opportunity_names(visitor_context.public_teams or [])
        groups = self._extract_opportunity_names(visitor_context.public_groups or [])
        events = self._extract_opportunity_names(visitor_context.upcoming_events or [])

        try:
            prompt = self.prompts.get_recommendations_prompt(visitor_data, visitor_data["welcome_form"], teams, groups, events)
            response = await self.generate_llm_content(prompt, max_tokens=3500, temperature=self.temperature)
            parsed = self._parse_json_response(response)
            return parsed if self._validate_recommendations(parsed) else self._fallback_recommendations(visitor_context)
        except Exception as e:
            logger.warning(f"Recommendations generation failed, using fallback: {e}")
            return self._fallback_recommendations(visitor_context)

    async def _determine_optimal_contact(self, visitor_context: VisitorContextData, profile_analysis: Dict[str, Any]) -> Dict[str, Any]:
        welcome_form = visitor_context.visitor_welcome_form or {}
        visit_info = welcome_form.get('visit_info', {})
    
        time_map = {
            'weekday_morning': 'Weekday mornings (9 AM - 12 PM)',
            'weekday_afternoon': 'Weekday afternoons (1 PM - 5 PM)', 
            'weekday_evening': 'Weekday evenings (6 PM - 8 PM)',
            'weekend_morning': 'Weekend mornings (9 AM - 12 PM)',
            'weekend_afternoon': 'Weekend afternoons (1 PM - 5 PM)',
            'weekend_evening': 'Weekend evenings (6 PM - 8 PM)',
            # Add mappings for simple form values
            'morning': 'Weekday mornings (9 AM - 12 PM)',
            'afternoon': 'Weekday afternoons (1 PM - 5 PM)',
            'evening': 'Weekday evenings (6 PM - 8 PM)',
        }
    
        preferred_time = visit_info.get('best_contact_time', 'weekday_evening')
        # Convert to lowercase for case-insensitive matching
        preferred_time_lower = preferred_time.lower() if preferred_time else 'weekday_evening'
        
        urgency = "high" if profile_analysis.get('follow_up_priority') == "high" else "normal"
        follow_up_days = 2 if urgency == "high" else 3
    
        return {
            "method": visit_info.get('preferred_communication_method', 'email'),
            "best_time": time_map.get(preferred_time_lower, time_map.get(preferred_time, 'Weekday evenings (6 PM - 8 PM)')),
            "urgency": urgency,
            "follow_up_days": follow_up_days,
        }

    # --- BUILDERS ---

    def _build_ai_note_structure(
        self, visitor_data: Dict[str, Any], analysis_results: Dict[str, Any], contact_info: Dict[str, Any],
        natural_summary: str, raw_content: str, visitor_context: VisitorContextData
    ) -> Dict[str, Any]:
        recs = analysis_results['recommendations']
        church_recs = self._transform_recommendations(recs.get("community_integration", []), "community_integration")
        event_recs = self._transform_recommendations(recs.get("event_engagement", []), "event_engagement")

        return {
            "visitor_full_name": self._format_full_name(visitor_data),
            "visitor_phone": visitor_data.get("phone", ""),
            "visitor_email": visitor_data.get("email", ""),
            "first_visit": self._format_visit_date_for_output(visitor_data.get("visit_date")),
            "best_contact_time": contact_info["best_time"],
            "channel_to_contact": contact_info["method"],
            "key_interests_summary": analysis_results['profile'].get("interests", []),
            "family_context_info": analysis_results['family'].get("context", ""),
            "sentiment_analysis": analysis_results['sentiment'],
            "church_integration_recommendations": church_recs,
            "event_engagement_recommendations": event_recs,
            "personal_needs_response": self._process_personal_needs(recs.get("personal_needs")),
            "feedback_insight": self._process_feedback_insights(recs.get("feedback_insights")),
            "ai_generated_label": True,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "person_id": str(visitor_data.get("person_id", "")),
            "fam_id": str(visitor_context.scenario_info.fam_id) if visitor_context.scenario_info else "",
            "raw_content": raw_content,
            "natural_summary": natural_summary,
            "confidence_score": analysis_results['sentiment'].get("confidence", 0.85),
            "data_sources_used": self._get_data_sources_used(visitor_context),
            "recommended_next_steps": self._format_next_steps(church_recs, event_recs,
                self._process_personal_needs(recs.get("personal_needs")),
                self._process_feedback_insights(recs.get("feedback_insights"))
            ),
        }

    def _create_natural_language_summary(
        self, visitor_data: Dict[str, Any], profile_analysis: Dict[str, Any],
        family_analysis: Dict[str, Any], sentiment_analysis: Dict[str, Any]
    ) -> str:
        first_name = visitor_data.get('first_name', 'This visitor')
        full_name = f"{first_name} {visitor_data.get('last_name', '')}".strip()
        title = self._determine_title(visitor_data)
        
        # Fix: Only use title if it's different from first_name to avoid duplication
        if title and title != first_name:
            name_to_use = f"{title} {full_name}"
        else:
            name_to_use = full_name

        parts = [f"{name_to_use} is a new member of our community who "]
        if family_analysis.get("is_family"):
            parts[0] += "visited with their family"
            if family_analysis.get("has_children"):
                parts[0] += ", including children."
            else:
                parts[0] += "."
        else:
            parts[0] += "visited our church."

        
        # Add address information when available
        if visitor_data.get('address'):
            address = visitor_data.get('address', {})
            if address and isinstance(address, dict):
                address_parts = []
                if address.get('city'):
                    address_parts.append(address['city'])
                if address.get('state'):
                    address_parts.append(address['state'])
                if address.get('zip'):
                    address_parts.append(address['zip'])
                
                if address_parts:
                    location = ', '.join(address_parts)
            parts.append(f"They are from {location}.")

        sentiment = sentiment_analysis.get("overall_sentiment", "neutral").lower()
        if sentiment == "positive":
            parts.append("They enjoyed their visit and had a positive experience.")
        elif sentiment == "negative":
            parts.append("They had some concerns during their visit that we should address.")
        else:
            parts.append("They had a good experience and are interested in learning more.")

        interests = profile_analysis.get("interests", [])
        if interests:
            interest_list = ', '.join(interests[:-1]) + (f" and {interests[-1]}" if len(interests) > 1 else interests[0])
            parts.append(f"They expressed interest in {interest_list.lower()}.")

        how_heard = visitor_data.get("how_heard_about_church")
        if how_heard:
            parts.append(f"They learned about our church through {how_heard.lower()}.")

        return " ".join(parts)

    def _create_raw_content(
        self, visitor_data: Dict[str, Any], analysis_results: Dict[str, Any],
        contact_info: Dict[str, Any], natural_summary: str = ""
    ) -> str:
        content = [
            "=== AI-Generated Visitor Follow-up Summary ===",
            "",
        ]
        if natural_summary:
            content.append(natural_summary + "\n")

        content.extend([
            "VISITOR INFORMATION:",
            f"Name: {visitor_data.get('first_name', '')} {visitor_data.get('last_name', '')}",
            f"Email: {visitor_data.get('email', '')}",
            f"Phone: {visitor_data.get('phone', '')}",
            f"Best Contact Time: {contact_info['best_time']}",
            f"Channel To Contact Them: {contact_info['method']}",
            f"First Visit: {visitor_data.get('visit_date', '')}",
            "",
            "KEY INTERESTS:",
            ", ".join(analysis_results['profile'].get('interests', ['General Fellowship'])),
            "",
            "FAMILY CONTEXT:",
            analysis_results['family'].get('context', 'Individual visitor'),
            "",
            "SENTIMENT ANALYSIS:",
            f"Overall: {analysis_results['sentiment'].get('overall_sentiment', 'Neutral')}",
            f"Confidence: {analysis_results['sentiment'].get('confidence', 0.5)*100:.0f}%",
            "",
            "=== Generation Metadata ===",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Confidence Score: {analysis_results['sentiment'].get('confidence', 0.85):.2f}",
            "",
            "[This note was automatically generated by AI and may require review]"
        ])
        return "\n".join(content)

    # --- UTILITIES & FALLBACKS ---

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        if not text or not text.strip():
            logger.warning("Empty text provided to JSON parser")
            return None
            
        # Clean the text
        text = text.strip()
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        # Try to find JSON object boundaries
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx]
        
        try:
            parsed = json.loads(text)
            logger.debug(f"Successfully parsed JSON with keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}. Text: {text[:200]}...")
            # Try partial extraction as fallback
            partial_data = self._extract_partial_json_data(text)
            if partial_data:
                return partial_data
            return None

    def _parse_llm_response(self, response_text: str, response_type: str = "general") -> Dict[str, Any]:
        """Enhanced LLM response parser with type-specific fallbacks."""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Try to extract JSON from markdown code blocks
            if '```json' in cleaned_text:
                start = cleaned_text.find('```json') + 7
                end = cleaned_text.find('```', start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            elif '```' in cleaned_text:
                start = cleaned_text.find('```') + 3
                end = cleaned_text.find('```', start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            
            parsed = json.loads(cleaned_text)
            return parsed if isinstance(parsed, dict) else self._get_fallback_structure(response_type)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for {response_type}: {e}. Response: {response_text[:500]}")
            # Try partial extraction
            partial_data = self._extract_partial_json_data(response_text)
            if partial_data:
                return partial_data
            # Return type-specific fallback
            return self._get_fallback_structure(response_type)

    def _get_fallback_structure(self, response_type: str) -> Dict[str, Any]:
        """Return appropriate fallback structure based on response type."""
        fallbacks = {
            "profile": {
                "interests": [],
                "needs": [],
                "engagement_opportunities": [],
                "sentiment": "neutral",
                "follow_up_actions": [],
                "confidence": 0.5
            },
            "sentiment": {
                "overall_sentiment": "neutral",
                "confidence": 0.5,
                "key_themes": [],
                "emotional_indicators": []
            },
            "recommendations": {
                "community_integration": [],
                "event_engagement": [],
                "personal_needs": [],
                "feedback_insights": []
            },
            "general": {
                "interests": [],
                "needs": [],
                "engagement_opportunities": [],
                "sentiment": "neutral",
                "follow_up_actions": [],
                "confidence": 0.5
            }
        }
        return fallbacks.get(response_type, fallbacks["general"])

    def _extract_partial_json_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract partial data from malformed JSON responses."""
        try:
            # Look for key-value patterns in the text
            partial_data = {}
            
            # Extract interests
            interests_match = re.search(r'"interests"\s*:\s*\[(.*?)\]', text, re.DOTALL)
            if interests_match:
                interests_str = interests_match.group(1)
                interests = [item.strip('"\' ') for item in interests_str.split(',') if item.strip()]
                partial_data['interests'] = interests
            
            # Extract sentiment
            sentiment_match = re.search(r'"sentiment"\s*:\s*"(.*?)"', text)
            if sentiment_match:
                partial_data['sentiment'] = sentiment_match.group(1)
            
            # Extract follow_up_actions
            actions_match = re.search(r'"follow_up_actions"\s*:\s*\[(.*?)\]', text, re.DOTALL)
            if actions_match:
                actions_str = actions_match.group(1)
                actions = [item.strip('"\' ') for item in actions_str.split(',') if item.strip()]
                partial_data['follow_up_actions'] = actions
            
            if partial_data:
                logger.info(f"Extracted partial data: {list(partial_data.keys())}")
                return partial_data
                
        except Exception as e:
            logger.warning(f"Partial data extraction failed: {e}")
        
        return None

    def _validate_quality(self, data: Dict[str, Any]) -> QualityResult:
        issues = []
        score = 1.0
        content = data.get("content", "")
        
        logger.info(f"Validating content quality - length: {len(content)} characters")
        
        if len(content) < 300:
            issues.append("content_too_short")
            score -= 0.2
            logger.warning(f"Content too short: {len(content)} < 300 characters")
        
        # More flexible section checking
        required_sections = ["summary", "contact", "family", "recommendation"]
        missing_sections = []
        for section in required_sections:
            if section.lower() not in content.lower():
                issues.append(f"missing_section_{section.lower()}")
                missing_sections.append(section)
                score -= 0.15  # Reduced penalty
        
        if missing_sections:
            logger.warning(f"Missing suggested sections: {missing_sections}")
        
        if "[PLACEHOLDER]" in content or "TODO" in content:
            issues.append("contains_placeholders")
            score -= 0.4
            logger.warning("Content contains placeholders")
        
        # Check if we have structured recommendations data instead of text sections
        recommendations_data = data.get("recommended_next_steps")
        if not recommendations_data and "recommendation" in [s.lower() for s in missing_sections]:
            issues.append("invalid_recommendations_format")
            score -= 0.1  # Reduced penalty since we have structured data
            logger.warning("Missing recommendations in both content and structured format")
        
        final_score = max(0.0, score)
        passed = final_score >= 0.6  # Lowered threshold
        
        logger.info(f"Quality validation result - Score: {final_score:.2f}, Passed: {passed}, Issues: {issues}")
        
        return QualityResult(
            passed=passed,
            score=final_score,
            issues=issues
        )

    def _format_full_name(self, data: Dict[str, Any]) -> str:
        return ' '.join(filter(None, [
            data.get('title'),
            data.get('first_name'),
            data.get('middle_name'),
            data.get('last_name')
        ])).strip()

    def _format_visit_date(self, date: Any) -> str:
        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return str(date) if date else ""

    def _format_visit_date_for_output(self, date: Any) -> str:
        return date.isoformat() if isinstance(date, datetime) else str(date) if date else ""

    def _determine_title(self, data: Dict[str, Any]) -> str:
        title = data.get('title')
        if title:
            return title
        first_name = data.get('first_name')
        return first_name if first_name else "This visitor"

    def _extract_opportunity_names(self, items: List[Dict[str, Any]]) -> List[str]:
        name_fields = ['name', 'title', 'team_name', 'group_name', 'event_name']
        names = []
        for item in items:
            if isinstance(item, dict):
                for field in name_fields:
                    if field in item and item[field]:
                        names.append(str(item[field]))
                        break
        return names

    def _transform_recommendations(self, recs: List[Any], rec_type: str) -> List[Dict[str, Any]]:
        result = []
        for rec in recs:
            if isinstance(rec, str):
                result.append({"type": rec_type, "title": rec, "description": rec, "priority": "medium"})
            elif isinstance(rec, dict):
                result.append(rec)
        return result

    def _process_personal_needs(self, data: Any) -> Optional[Dict[str, Any]]:
        if isinstance(data, str):
            return {"type": "personal_needs", "summary": data, "action_required": True, "escalation_required": False}
        return data if isinstance(data, dict) else None

    def _process_feedback_insights(self, data: Any) -> Optional[Dict[str, Any]]:
        if isinstance(data, str):
            return {"type": "feedback_insight", "tone": "positive", "category": "general", "action_step": data}
        return data if isinstance(data, dict) else None

    def _format_next_steps(
        self, church_recs, event_recs, personal, feedback
    ) -> Dict[str, List[str]]:
        def extract_titles(items):
            titles = []
            if isinstance(items, str):
                titles.extend([s.strip() for s in items.split(",") if s.strip()])
            elif isinstance(items, list):
                for i in items:
                    if isinstance(i, dict):
                        titles.append((i.get("title") or i.get("description") or "").strip())
                    else:
                        titles.append(str(i).strip())
            elif items:
                titles.append(str(items).strip())
            return titles

        return {
            "church_integration": extract_titles(church_recs),
            "event_engagement": extract_titles(event_recs),
            "personal_needs": extract_titles(personal) if personal else [],
            "feedback_insights": extract_titles(feedback) if feedback else [],
        }

    def _get_data_sources_used(self, visitor_context: VisitorContextData) -> List[str]:
        sources = ['visitor_profile']
        fields = [
            'visitor_welcome_form', 'first_timer_notes', 'prayer_requests',
            'existing_followup_notes', 'feedback_fields', 'public_teams',
            'public_groups', 'upcoming_events', 'family_members'
        ]
        for field in fields:
            if getattr(visitor_context, field, None):
                sources.append(field)
        return sources

    # --- FALLBACKS ---

    def _fallback_profile(self) -> Dict[str, Any]:
        return {
            "interests": ["General Fellowship"],
            "ministry_areas": ["Sunday Service"],
            "life_stage": "Unknown",
            "spiritual_background": "Unknown",
            "specific_needs": [],
            "engagement_level": "medium",
            "follow_up_priority": "medium"
        }

    def _fallback_family(self, ctx: VisitorContextData) -> Dict[str, Any]:
        return {
            "context": "Individual visit.",
            "is_family": False,
            "is_existing": False,
            "member_count": 1,
            "has_children": False,
            "children_count": 0,
        }

    def _fallback_sentiment(self) -> Dict[str, Any]:
        return {
            "overall_sentiment": "neutral",
            "confidence": 0.5,
            "key_emotions": ["Curious"],
            "concerns": [],
            "positive_indicators": []
        }

    def _fallback_recommendations(self, ctx: VisitorContextData) -> Dict[str, Any]:
        teams = self._extract_opportunity_names(ctx.public_teams or [])
        groups = self._extract_opportunity_names(ctx.public_groups or [])
        events = self._extract_opportunity_names(ctx.upcoming_events or [])
        return {
            "community_integration": teams[:2] or groups[:2] or ["Connect with a small group"],
            "event_engagement": events[:2] or ["Attend next Sunday service"],
            "personal_needs": {"identified_needs": ["General spiritual growth"]},
            "feedback_insights": {"key_takeaways": ["New visitor seeking community"]}
        }

    def _create_fallback_note(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
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
            "sentiment_analysis": self._fallback_sentiment(),
            "church_integration_recommendations": [],
            "event_engagement_recommendations": [],
            "personal_needs_response": None,
            "feedback_insight": None,
            "ai_generated_label": True,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "person_id": str(person_info.get("id", "")),
            "fam_id": "",
            "raw_content": "Fallback note due to processing error.",
            "natural_summary": "This visitor requires manual follow-up.",
            "confidence_score": 0.5,
            "data_sources_used": ["visitor_profile"],
            "recommended_next_steps": {
                "church_integration": [],
                "event_engagement": [],
                "personal_needs": [],
                "feedback_insights": []
            }
        }

    # --- VALIDATIONS ---

    def _validate_recommendations(self, recs: Optional[Dict[str, Any]]) -> bool:
        if not recs:
            return False
        expected = ['community_integration', 'event_engagement', 'personal_needs', 'feedback_insights']
        return any(k in recs for k in expected)

    def _validate_sentiment_analysis(self, analysis: Optional[Dict[str, Any]]) -> bool:
        if not analysis:
            return False
        return "overall_sentiment" in analysis and "confidence" in analysis


###Visitor Snapshot Fuctions####

    async def generate_visitor_snapshot_summary(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Generate a concise visitor snapshot summary for the visitor snapshot feature.
        
        Args:
            visitor_context (VisitorContextData): Complete visitor context information
        
        Returns:
            Dict[str, Any]: Structured summary with natural language description
        """
        try:
            # Extract visitor data
            visitor_data = self._extract_visitor_data(visitor_context)
            
            # Perform lightweight analysis for snapshot
            profile_analysis = await self._analyze_visitor_profile(visitor_context)
            family_analysis = await self._analyze_family_context(visitor_context)
            sentiment_analysis = await self._perform_sentiment_analysis(visitor_context)
            
            # Create concise natural summary for snapshot
            natural_summary = self._create_snapshot_summary(
                visitor_data, profile_analysis, family_analysis, sentiment_analysis
            )
            
            # Return structured data
            return {
                "natural_summary": natural_summary,
                "sentiment_classification": sentiment_analysis.get("overall_sentiment", "Neutral"),
                "key_interests": profile_analysis.get("interests", []),
                "family_context": family_analysis.get("context", ""),
                "confidence_score": sentiment_analysis.get("confidence", 0.85)
            }
            
        except Exception as e:
            logger.error(f"Error generating visitor snapshot summary: {e}")
            return self._create_fallback_snapshot_summary(visitor_context)
    
    def _create_snapshot_summary(
        self, 
        visitor_data: Dict[str, Any], 
        profile_analysis: Dict[str, Any], 
        family_analysis: Dict[str, Any], 
        sentiment_analysis: Dict[str, Any]
    ) -> str:
        """
        Create a concise snapshot summary for the visitor.
        
        Args:
            visitor_data: Consolidated visitor data
            profile_analysis: Analyzed visitor interests and characteristics
            family_analysis: Family context information
            sentiment_analysis: Emotional sentiment analysis
            
        Returns:
            str: Concise natural language summary
        """
        first_name = visitor_data.get('first_name', 'This visitor')
        
        summary_parts = []
        
        # Basic introduction
        if family_analysis.get('is_family', False):
            if family_analysis.get('has_children', False):
                summary_parts.append(f"{first_name} visited with their family, including children.")
            else:
                summary_parts.append(f"{first_name} visited with their family.")
        else:
            summary_parts.append(f"{first_name} is a new visitor to our church.")
        
        # Add key interests if available - FIX: Handle None values in interests
        interests = profile_analysis.get('interests', [])
        if interests and len(interests) > 0:
            # Filter out None values and ensure all items are strings with safe strip checking
            valid_interests = []
            for interest in interests:
                if interest is not None:
                    interest_str = str(interest)
                    if interest_str and interest_str.strip():
                        valid_interests.append(interest_str.strip().lower())
            
            if valid_interests:
                if len(valid_interests) == 1:
                    summary_parts.append(f"They showed interest in {valid_interests[0]}.")
                else:
                    summary_parts.append(f"They expressed interest in {', '.join(valid_interests[:2])}.")
        
        # Add sentiment context
        sentiment = sentiment_analysis.get('overall_sentiment', 'neutral')
        if sentiment == 'positive':
            summary_parts.append("They had a positive experience and seem engaged.")
        elif sentiment == 'negative':
            summary_parts.append("They had some concerns that may need follow-up.")
        # Add how they heard about church if available #TODO: map data correctly from welcome form 
        how_heard = visitor_data.get('how_heard_about_church', '')
        if how_heard and how_heard is not None:
            how_heard_str = str(how_heard)
            if how_heard_str and how_heard_str.strip() and how_heard_str.lower() != 'none':
                summary_parts.append(f"They found us through {how_heard_str.strip().lower()}.")
        
        return " ".join(summary_parts)
    
    def _create_fallback_snapshot_summary(self, visitor_context: VisitorContextData) -> Dict[str, Any]:
        """
        Create a fallback snapshot summary when AI generation fails.
        
        Args:
            visitor_context: The visitor context data
            
        Returns:
            Dict[str, Any]: Basic fallback summary
        """
        visitor_profile = visitor_context.visitor_profile or {}
        first_name = visitor_profile.get('first_name', 'This visitor')
        
        return {
            "natural_summary": f"{first_name} is a new visitor to our church community. We look forward to connecting with them further.",
            "sentiment_classification": "Neutral",
            "key_interests": ["General Fellowship"],
            "family_context": "Individual visit",
            "confidence_score": 0.5
        }