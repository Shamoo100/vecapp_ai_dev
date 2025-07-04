from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.database.repositories.connection import DatabaseConnection
from app.database.models.visitor import Visitor

class DataCollectionAgent(BaseAgent):
    def __init__(self, agent_id: str, schema: str):
        super().__init__(agent_id, schema)
        self.db_connection = DatabaseConnection

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visitor data"""
        try:
            # Validate data
            self._validate_visitor_data(data)
            
            # Create visitor object
            visitor = Visitor(
                schema=self.schema,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone=data.get('phone'),
                visit_date=data['visit_date']
            )

            # Store in database
            visitor_id = await self.database.store_visitor(visitor, self.schema)
            
            # Prepare data for Generative Agent
            processed_data = {
                'visitor_id': visitor_id,
                'visitor_data': visitor.to_dict(),
                'schema': self.schema
            }

            self.log_activity(f"Processed visitor data for {visitor.email}")
            return processed_data

        except Exception as e:
            self.log_activity(f"Error processing visitor data: {str(e)}", "error")
            raise

    def _validate_visitor_data(self, data: Dict[str, Any]) -> bool:
        """Validate required visitor fields"""
        required_fields = ['first_name', 'last_name', 'email', 'visit_date']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return True