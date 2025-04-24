from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_type: str):
        """
        Initialize the agent.
        
        Args:
            agent_type: The type of the agent
        """
        self.agent_type = agent_type
        logger.info(f"Initialized {agent_type} agent")

    @abstractmethod
    async def process(self, data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Process data with the agent.
        
        Args:
            data: The data to process
            tenant_id: The ID of the tenant the data belongs to
            
        Returns:
            The processed data
        """
        logger.info(f"Processing data with {self.agent_type} agent for tenant {tenant_id}")
        return {}

    async def validate_tenant_access(self) -> bool:
        """Validate agent has access to tenant data"""
        # Implementation for tenant validation
        return True

    def log_activity(self, message: str, level: str = "info"):
        """Log agent activity"""
        log_methods = {
            "info": logger.info,
            "error": logger.error,
            "warning": logger.warning,
            "debug": logger.debug
        }
        log_methods.get(level, logger.info)(
            f"[Tenant: {self.tenant_id}] {message}"
        )

    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get the status of the agent.
        
        Returns:
            The agent status
        """
        return {
            "agent_type": self.agent_type,
            "status": "active"
        }

    @staticmethod
    def create_agent(agent_type: str) -> 'BaseAgent':
        """
        Factory method to create an agent of the specified type.
        
        Args:
            agent_type: The type of agent to create
            
        Returns:
            An instance of the specified agent type
        """
        from agents.volunteer_coordination_agent import VolunteerCoordinationAgent
        from agents.specialist_agent import SpecialistAgent
        from agents.generative_agent import GenerativeAgent
        from agents.feedback_loop_agent import FeedbackLoopAgent
        from agents.evaluation_agent import EvaluationAgent
        from agents.data_collection_agent import DataCollectionAgent
        from agents.followup_summary_agent import FollowupSummaryAgent
        
        agent_classes = {
            "volunteer_coordination": VolunteerCoordinationAgent,
            "specialist": SpecialistAgent,
            "generative": GenerativeAgent,
            "feedback_loop": FeedbackLoopAgent,
            "evaluation": EvaluationAgent,
            "data_collection": DataCollectionAgent,
            "followup_summary": FollowupSummaryAgent
        }
        
        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return agent_classes[agent_type]() 