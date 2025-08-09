"""Agent package initialization and factory pattern implementation."""
from typing import Dict, Any, Type
from .base_agent import BaseAgent
from .data_collection_agent import DataCollectionAgent
from .followup_summary_agent import FollowupSummaryAgent
from .followup_note_agent import FollowupNoteAgent

class AgentFactory:
    """Factory class for creating and managing agent instances."""
    
    _agent_types: Dict[str, Type[BaseAgent]] = {
        'data_collection': DataCollectionAgent,
        'followup_summary': FollowupSummaryAgent,
        'followup_note': FollowupNoteAgent,
    }
    
    @classmethod
    def create_agent(cls, agent_type: str, agent_id: str, schema: str, config: Dict[str, Any]) -> BaseAgent:
        """Create an agent instance based on type and configuration.
        
        Args:
            agent_type: Type of agent to create
            agent_id: Unique identifier for the agent
            schema: Schema name for the tenant
            config: Configuration dictionary for agent initialization
            
        Returns:
            Initialized agent instance
            
        Raises:
            ValueError: If agent_type is not recognized
        """
        if agent_type not in cls._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = cls._agent_types[agent_type]
        
        # Add required parameters to config
        agent_config = {
            "agent_id": agent_id,
            "schema": schema,
            **config
        }
        
        return agent_class(**agent_config)