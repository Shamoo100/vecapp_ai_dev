from typing import Dict, Any
from datetime import datetime, timedelta
from .base_agent import BaseAgent
import openai
from langchain_openai import ChatOpenAI


class FollowupNoteAgent(BaseAgent):
    def __init__(self, agent_id: str, schema: str, openai_key: str):
        super().__init__(agent_id, schema)
        self.openai = openai.AsyncOpenAI(api_key=openai_key)  # Use async client

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visitor insights and follow-up recommendations"""
        try:
            visitor_data = data['visitor_data']
            if not isinstance(visitor_data, dict):
                raise ValueError("visitor_data must be a dictionary")
            
            # Generate visitor persona
            persona = await self._generate_persona(visitor_data)
            
            # Generate follow-up recommendations
            recommendations = await self._generate_recommendations(visitor_data, persona)
            
            # Determine optimal follow-up time
            follow_up_time = await self._determine_follow_up_time(visitor_data, persona)
            
            processed_data = {
                'visitor_id': visitor_data.get('visitor_id'),
                'schema': self.schema,
                'persona': persona,
                'recommendations': recommendations,
                'follow_up_time': follow_up_time
            }

            self.log_activity(f"Generated insights for visitor {visitor_data.get('email', '')}")
            return processed_data

        except Exception as e:
            self.log_activity(f"Error generating insights: {str(e)}", "error")
            raise

    async def _generate_persona(self, visitor_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visitor persona using OpenAI"""
        prompt = self._create_persona_prompt(visitor_dict)
        response = await self.openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a church visitor analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        return self._parse_persona_response(response.choices[0].message.content)

    async def _generate_recommendations(self, visitor_dict: Dict[str, Any], persona: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized follow-up recommendations"""
        prompt = self._create_recommendations_prompt(visitor_dict, persona)
        response = await self.openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a church engagement specialist."},
                {"role": "user", "content": prompt}
            ]
        )
        return self._parse_recommendations_response(response.choices[0].message.content)

    async def _determine_follow_up_time(self, visitor_dict: Dict[str, Any], persona: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal follow-up time and channel"""
        # Implementation for follow-up time determination
        visit_date = visitor_dict.get('visit_date')
        if not isinstance(visit_date, datetime):
            visit_date = datetime.fromisoformat(visit_date) if visit_date else datetime.now()
        return {
            'suggested_time': visit_date + timedelta(days=2),
            'preferred_channel': 'email',
            'alternative_channels': ['phone', 'sms']
        }

    def _create_persona_prompt(self, visitor_dict: Dict[str, Any]) -> str:
        return f"""
        Analyze this first-time church visitor:
        Name: {visitor_dict.get('first_name', '')} {visitor_dict.get('last_name', '')}
        Visit Date: {visitor_dict.get('visit_date', '')}
        
        Generate a visitor persona including:
        1. Likely demographic information
        2. Potential interests and ministry connections
        3. Engagement readiness level
        """

    def _parse_persona_response(self, response: str) -> Dict[str, Any]:
        # Implementation for parsing OpenAI response
        pass

    async def generate_note(self, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a follow-up note in optimized JSONB format based on visitor data.
        """
        try:
            if 'visitor' not in visitor_data:
                raise ValueError("Missing 'visitor' in visitor_data")
            visitor_dict = visitor_data['visitor']  # Use dict directly
            
            # Extract required fields with defaults/validation
            first_name = visitor_dict.get('first_name', '')
            last_name = visitor_dict.get('last_name', '')
            email = visitor_dict.get('email', '')
            phone = visitor_dict.get('phone', '')
            first_time_visit = visitor_dict.get('first_time_visit', True)
            # Add more fields as needed
            
            # Pass dict to private methods (update them to accept dict instead of Visitor)
            persona = await self._generate_persona(visitor_dict)
            recommendations = await self._generate_recommendations(visitor_dict, persona)
            follow_up = await self._determine_follow_up_time(visitor_dict, persona)
            
            now = datetime.now()
            created_at = now.isoformat()
            created_str = now.strftime("%B %d, %Y at %I:%M %p")
            
            # Update raw_content to use dict fields
            raw_content = f"Visitor Summary\n\n## Visitor Name\n{first_name} {last_name}  \n\n## Email\n{email}  \n\n## Phone Number\n{phone}  \n\n## Most Convenient Time To Contact Them\n{follow_up.get('suggested_time', '').strftime('%I%p on weekdays') if follow_up.get('suggested_time') else ''}  \n\n## Channel To Contact Them\n{follow_up.get('preferred_channel', '')}  \n\n## Primary Interests\n{', '.join(persona.get('interests', []))}  \n\n## Special Requests\n{', '.join(recommendations.get('special_requests', []))}  \n\n## Sentiment\n{persona.get('sentiment', 'Positive')} (Confidence {persona.get('confidence', 92)}%)  \n\n## Recommended Actions\n{chr(10).join([f'- {action}' for action in recommendations.get('actions', [])])}  \n\nCreated: {created_str}"
            
            # Compile structured note (update to use dict fields)
            note = {
                "template_type": "visitor_summary",
                "header": {
                    "title": "Visitor Summary",
                    "created_at": created_at
                },
                "profile": {
                    "visitor_name": f"{first_name} {last_name}",
                    "email": email,
                    "phone": phone
                },
                "preferences": {
                    "contact_time": follow_up.get("suggested_time", "").strftime("%I%p on weekdays") if follow_up.get("suggested_time") else "",
                    "contact_channel": follow_up.get("preferred_channel", "")
                },
                "interests": persona.get("interests", []),
                "requests": recommendations.get("special_requests", []),
                "sentiment_analysis": {
                    "label": persona.get("sentiment", "Positive"),
                    "confidence": persona.get("confidence", 0.92)
                },
                "recommendations": [
                    {"action": action, "assignee": rec.get("assignee", ""), "priority": rec.get("priority", "medium")}
                    for action, rec in zip(recommendations.get("actions", []), recommendations.get("details", []))  # Adjust based on actual structure
                ],
                "raw_content": raw_content
            }
            
            self.log_activity(f"Generated note for visitor {email}")
            return note
        except Exception as e:
            self.log_activity(f"Error generating note: {str(e)}", "error")
            raise

    def _parse_persona_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured format"""
        # Implementation for parsing OpenAI response
        pass
