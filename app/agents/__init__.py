"""Agent package initialization and factory pattern implementation."""
from typing import Dict, Any, Type
from .base_agent import BaseAgent
from .data_collection_agent import DataCollectionAgent
from .volunteer_coordination_agent import VolunteerCoordinationAgent
from .evaluation_agent import EvaluationAgent
from .feedback_loop_agent import FeedbackLoopAgent
from .followup_summary_agent import FollowupSummaryAgent
from .generative_agent import GenerativeAgent
from .specialist_agent import SpecialistAgent

class AgentFactory:
    """Factory class for creating and managing agent instances."""
    
    _agent_types: Dict[str, Type[BaseAgent]] = {
        'data_collection': DataCollectionAgent,
        'volunteer_coordination': VolunteerCoordinationAgent,
        'evaluation': EvaluationAgent,
        'feedback_loop': FeedbackLoopAgent,
        'followup_summary': FollowupSummaryAgent,
        'generative': GenerativeAgent,
        'specialist': SpecialistAgent
    }
    
    @classmethod
    def create_agent(cls, agent_type: str, config: Dict[str, Any]) -> BaseAgent:
        """Create an agent instance based on type and configuration.
        
        Args:
            agent_type: Type of agent to create
            config: Configuration dictionary for agent initialization
            
        Returns:
            Initialized agent instance
            
        Raises:
            ValueError: If agent_type is not recognized
        """
        if agent_type not in cls._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = cls._agent_types[agent_type]
        return agent_class(**config)