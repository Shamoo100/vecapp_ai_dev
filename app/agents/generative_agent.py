from typing import Dict, Any
import openai
from .base_agent import BaseAgent
from models.visitor import Visitor
from core.messaging import MessageQueue

class GenerativeAgent(BaseAgent):
    def __init__(self, agent_id: str, tenant_id: str, openai_key: str, message_queue: MessageQueue):
        super().__init__(agent_id, tenant_id)
        self.openai = openai
        self.openai.api_key = openai_key
        self.message_queue = message_queue

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visitor insights and follow-up recommendations"""
        try:
            visitor = Visitor.from_dict(data['visitor_data'])
            
            # Generate visitor persona
            persona = await self._generate_persona(visitor)
            
            # Generate follow-up recommendations
            recommendations = await self._generate_recommendations(visitor, persona)
            
            # Determine optimal follow-up time
            follow_up_time = await self._determine_follow_up_time(visitor, persona)
            
            processed_data = {
                'visitor_id': visitor.visitor_id,
                'tenant_id': self.tenant_id,
                'persona': persona,
                'recommendations': recommendations,
                'follow_up_time': follow_up_time
            }

            # Send to Volunteer Coordination Agent
            await self.message_queue.publish(
                'volunteer_coordination',
                processed_data
            )

            self.log_activity(f"Generated insights for visitor {visitor.email}")
            return processed_data

        except Exception as e:
            self.log_activity(f"Error generating insights: {str(e)}", "error")
            raise

    async def _generate_persona(self, visitor: Visitor) -> Dict[str, Any]:
        """Generate visitor persona using OpenAI"""
        prompt = self._create_persona_prompt(visitor)
        response = await self.openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a church visitor analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        return self._parse_persona_response(response.choices[0].message.content)

    async def _generate_recommendations(self, visitor: Visitor, persona: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized follow-up recommendations"""
        prompt = self._create_recommendations_prompt(visitor, persona)
        response = await self.openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a church engagement specialist."},
                {"role": "user", "content": prompt}
            ]
        )
        return self._parse_recommendations_response(response.choices[0].message.content)

    async def _determine_follow_up_time(self, visitor: Visitor, persona: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal follow-up time and channel"""
        # Implementation for follow-up time determination
        return {
            'suggested_time': visitor.visit_date + timedelta(days=2),
            'preferred_channel': 'email',
            'alternative_channels': ['phone', 'sms']
        }

    def _create_persona_prompt(self, visitor: Visitor) -> str:
        return f"""
        Analyze this first-time church visitor:
        Name: {visitor.first_name} {visitor.last_name}
        Visit Date: {visitor.visit_date}
        
        Generate a visitor persona including:
        1. Likely demographic information
        2. Potential interests and ministry connections
        3. Engagement readiness level
        """

    def _parse_persona_response(self, response: str) -> Dict[str, Any]:
        # Implementation for parsing OpenAI response
        pass 