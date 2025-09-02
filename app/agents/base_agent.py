from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional
from app.infastructure.ai.llm_provider_factory import LLMProviderFactory

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_id: str, schema: str):
        """
        Initialize the agent with LLM provider support.
        
        Args:
            agent_id: The unique identifier for the agent
            schema: The schema name of the tenant
        """
        self.agent_id = agent_id
        self.schema = schema
        self.llm_factory = LLMProviderFactory()
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

    async def generate_llm_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using available LLM providers with automatic fallback.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional parameters for the LLM
            
        Returns:
            Generated content string
        """
        try:
            return await self.llm_factory.generate_content_with_fallback(prompt, **kwargs)
        except Exception as e:
            logger.error(f"LLM content generation failed for agent {self.agent_id}: {e}")
            raise

    def get_llm_provider_status(self) -> Dict[str, Any]:
        """
        Get the status of all LLM providers.
        
        Returns:
            Dictionary containing provider status information
        """
        return self.llm_factory.get_provider_status()

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
        getattr(logger, level, logger.info)(f"[{self.agent_id}] {message}")

    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get comprehensive agent status including LLM providers.
        
        Returns:
            Dictionary containing agent status
        """
        return {
            "agent_id": self.agent_id,
            "schema": self.schema,
            "llm_providers": self.get_llm_provider_status(),
            "status": "active"
        }