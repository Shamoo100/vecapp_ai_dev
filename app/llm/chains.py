"""Chain definitions for various LLM-powered functionalities."""
from typing import Dict, Any
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from .prompts import PromptLibrary

class ChainFactory:
    """Factory for creating and configuring LLM chains."""
    
    def __init__(self, llm_manager):
        """Initialize chain factory with LLM manager.
        
        Args:
            llm_manager: Instance of LLMManager for chain creation
        """
        self.llm_manager = llm_manager
        self.prompts = PromptLibrary.get_prompts()
        
    def create_visitor_analysis_chain(self) -> LLMChain:
        """Create chain for visitor data analysis.
        
        Returns:
            Configured LLMChain for visitor analysis
        """
        return LLMChain(
            llm=self.llm_manager.llm,
            prompt=self.prompts['visitor_analysis']
        )
    
    def create_volunteer_matching_chain(self) -> LLMChain:
        """Create chain for volunteer matching.
        
        Returns:
            Configured LLMChain for volunteer matching
        """
        return LLMChain(
            llm=self.llm_manager.llm,
            prompt=self.prompts['volunteer_matching']
        )
    
    def create_feedback_analysis_chain(self, with_memory: bool = True) -> LLMChain:
        """Create chain for feedback analysis with optional memory.
        
        Args:
            with_memory: Whether to include conversation memory
            
        Returns:
            Configured LLMChain for feedback analysis
        """
        memory = ConversationBufferMemory() if with_memory else None
        return LLMChain(
            llm=self.llm_manager.llm,
            prompt=self.prompts['feedback_analysis'],
            memory=memory
        )
    
    def create_followup_summary_chain(self) -> LLMChain:
        """Create chain for generating follow-up summaries.
        
        Returns:
            Configured LLMChain for follow-up summaries
        """
        return LLMChain(
            llm=self.llm_manager.llm,
            prompt=self.prompts['followup_summary']
        )
    
    def get_chain_config(self, chain_type: str) -> Dict[str, Any]:
        """Get configuration for a specific chain type.
        
        Args:
            chain_type: Type of chain to configure
            
        Returns:
            Chain configuration dictionary
            
        Raises:
            ValueError: If chain_type is not recognized
        """
        configs = {
            'visitor_analysis': {
                'temperature': 0.7,
                'max_tokens': 500
            },
            'volunteer_matching': {
                'temperature': 0.5,
                'max_tokens': 300
            },
            'feedback_analysis': {
                'temperature': 0.6,
                'max_tokens': 400
            },
            'followup_summary': {
                'temperature': 0.4,
                'max_tokens': 600
            }
        }
        
        if chain_type not in configs:
            raise ValueError(f"Unknown chain type: {chain_type}")
            
        return configs[chain_type]