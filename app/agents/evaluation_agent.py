from typing import Dict, Any, List
from datetime import datetime
from app.base_agent import BaseAgent
from app.core.messaging import MessageQueue
from app.models.feedback import Feedback
from app.core.database import Database

class EvaluationAgent(BaseAgent):
    """Agent responsible for evaluating follow-up outcomes and feedback"""
    def __init__(
        self,
        agent_id: str,
        schema: str,
        message_queue: MessageQueue,
        database: Database
    ):
        super().__init__(agent_id, schema)
        self.message_queue = message_queue
        self.database = database

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process follow-up outcomes and feedback"""
        try:
            # Record interaction outcome
            interaction_data = await self._record_interaction(data)
            
            # Process feedback if available
            if 'feedback' in data:
                feedback_data = await self._process_feedback(data['feedback'])
                
                # Update visitor profile
                await self._update_visitor_profile(
                    data['visitor_id'],
                    feedback_data
                )
            
            processed_data = {
                'visitor_id': data['visitor_id'],
                'schema': self.schema,
                'interaction_data': interaction_data,
                'feedback_data': feedback_data if 'feedback' in data else None,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Send to Feedback Loop Agent
            await self.message_queue.publish(
                'feedback_loop',
                processed_data
            )

            self.log_activity(f"Processed evaluation for visitor {data['visitor_id']}")
            return processed_data

        except Exception as e:
            self.log_activity(f"Error processing evaluation: {str(e)}", "error")
            raise

    async def _record_interaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record follow-up interaction details"""
        interaction = {
            'visitor_id': data['visitor_id'],
            'volunteer_id': data['volunteer_id'],
            'interaction_type': data['interaction_type'],
            'interaction_date': datetime.utcnow(),
            'outcome': data.get('outcome', 'pending'),
            'notes': data.get('notes', '')
        }
        
        await self.database.store_interaction(interaction)
        return interaction

    async def _process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visitor feedback"""
        feedback = Feedback(
            visitor_id=feedback_data['visitor_id'],
            rating=feedback_data['rating'],
            comments=feedback_data.get('comments', ''),
            categories=feedback_data.get('categories', []),
            timestamp=datetime.utcnow()
        )
        
        await self.database.store_feedback(feedback)
        return feedback.to_dict()

    async def _update_visitor_profile(
        self,
        visitor_id: str,
        feedback_data: Dict[str, Any]
    ):
        """Update visitor profile based on feedback"""
        visitor = await self.database.get_visitor(visitor_id, self.tenant_id)
        
        # Update engagement metrics
        visitor['engagement_score'] = self._calculate_engagement_score(
            visitor,
            feedback_data
        )
        
        # Update interests and preferences
        visitor['interests'] = self._update_interests(
            visitor.get('interests', []),
            feedback_data
        )
        
        await self.database.update_visitor(visitor)

    def _calculate_engagement_score(
        self,
        visitor: Dict[str, Any],
        feedback_data: Dict[str, Any]
    ) -> float:
        """Calculate visitor engagement score"""
        # Implementation for engagement score calculation
        pass

    def _update_interests(
        self,
        current_interests: List[str],
        feedback_data: Dict[str, Any]
    ) -> List[str]:
        """Update visitor interests based on feedback"""
        # Implementation for interests update
        pass