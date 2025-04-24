from typing import Dict, Any
from .base_agent import BaseAgent
from core.database import Database
from models.visitor import Visitor

class DataCollectionAgent(BaseAgent):
    def __init__(self, agent_id: str, tenant_id: str, database: Database):
        super().__init__(agent_id, tenant_id)
        self.database = database

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visitor data"""
        try:
            # Validate data
            self._validate_visitor_data(data)
            
            # Create visitor object
            visitor = Visitor(
                tenant_id=self.tenant_id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone=data.get('phone'),
                visit_date=data['visit_date']
            )

            # Store in database
            visitor_id = await self.database.store_visitor(visitor)
            
            # Prepare data for Generative Agent
            processed_data = {
                'visitor_id': visitor_id,
                'visitor_data': visitor.to_dict(),
                'tenant_id': self.tenant_id
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