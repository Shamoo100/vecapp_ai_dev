#\"""Centralized prompt templates for LLM interactions."""
from typing import Dict
from langchain.prompts import PromptTemplate

class PromptLibrary:
    """Manages and provides access to all prompt templates."""
    
    # Visitor Analysis Prompts
    VISITOR_ANALYSIS = PromptTemplate(
        input_variables=["visitor_data", "context"],
        template="""Analyze the following visitor data and context:
        Visitor Data: {visitor_data}
        Context: {context}
        
        Provide insights on:
        1. Key interests and needs
        2. Potential engagement opportunities
        3. Recommended follow-up actions"""
    )
    
    # Volunteer Matching Prompts
    VOLUNTEER_MATCHING = PromptTemplate(
        input_variables=["visitor_needs", "volunteer_profiles"],
        template="""Match the following visitor needs with available volunteers:
        Visitor Needs: {visitor_needs}
        Volunteer Profiles: {volunteer_profiles}
        
        Evaluate and rank matches based on:
        1. Skill alignment
        2. Availability
        3. Past performance
        4. Communication style"""
    )
    
    # Feedback Analysis Prompts
    FEEDBACK_ANALYSIS = PromptTemplate(
        input_variables=["feedback_data", "historical_context"],
        template="""Analyze the following feedback and historical context:
        Feedback: {feedback_data}
        Historical Context: {historical_context}
        
        Provide analysis on:
        1. Sentiment and key themes
        2. Areas for improvement
        3. Success patterns
        4. Recommended adjustments"""
    )
    
    # Follow-up Summary Prompts
    FOLLOWUP_SUMMARY = PromptTemplate(
        input_variables=["interaction_history", "outcomes"],
        template="""Summarize the following interaction and outcomes:
        Interaction History: {interaction_history}
        Outcomes: {outcomes}
        
        Generate a comprehensive summary including:
        1. Key discussion points
        2. Decisions made
        3. Action items
        4. Next steps"""
    )
    
    @classmethod
    def get_prompts(cls) -> Dict[str, PromptTemplate]:
        """Get all available prompt templates.
        
        Returns:
            Dictionary mapping prompt names to templates
        """
        return {
'visitor_analysis': cls.VISITOR_ANALYSIS,
            'volunteer_matching': cls.VOLUNTEER_MATCHING,
            'feedback_analysis': cls.FEEDBACK_ANALYSIS,
            'followup_summary': cls.FOLLOWUP_SUMMARY
        }