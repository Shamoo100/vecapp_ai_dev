from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_id: str, schema: str):
        """
        Initialize the agent.
        
        Args:
            agent_id: The unique identifier for the agent
            schema: The schema name of the tenant
        """
        self.agent_id = agent_id
        self.schema = schema
        logger.info(f"Initialized agent {agent_id} with schema {schema}")

    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data with the agent.
        
        Args:
            data: The data to process
            
        Returns:
            The processed data
        """
        logger.info(f"Processing data with agent {self.agent_id} for schema {self.schema}")
        return {}

    async def validate_tenant_access(self) -> bool:
        """
        Validate agent has access to tenant data.
        
        Returns:
            True if access is valid, False otherwise
        """
        # Implementation for tenant validation
        return True

    def log_activity(self, message: str, level: str = "info"):
        """
        Log agent activity.
        
        Args:
            message: The message to log
            level: The log level
        """
        log_methods = {
            "info": logger.info,
            "error": logger.error,
            "warning": logger.warning,
            "debug": logger.debug
        }
        
        schema_context = f"[Schema: {self.schema}] "
        log_methods.get(level, logger.info)(f"{schema_context}{message}")

    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get the status of the agent.
        
        Returns:
            The agent status
        """
        return {
            "agent_id": self.agent_id,
            "schema": self.schema,
            "status": "active"
        }