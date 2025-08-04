#\"""Centralized prompt templates for LLM interactions."""
from typing import Dict
from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.prompts.chat import ChatPromptTemplate

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
        3. Sentiment based on feedback on visitor form
        4. Recommended follow-up actions
        """
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
    
    # Report Generator Prompts
    REPORT_VISITOR_SUMMARY = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
            You are an AI assistant that analyzes church visitor data and creates a summary report.
            For the Visitor Summary section, analyze the data to extract:
            1. Total visitors followed up within the given date range
            2. Count of single-family vs. multi-family engagements
            3. Total number of family members engaged
            
            Your output should be structured as a detailed section with key metrics and brief analysis.
        """),
        HumanMessage(content="""
            Please create the Visitor Summary section based on the following data:
            
            Date Range: {start_date} to {end_date}
            Followup Data: {followup_data}
            
            Format the output as a JSON object with these fields:
            - total_visitors: number
            - single_family: number
            - multi_family: number
            - total_family_members: number
            - summary_text: string (2-3 sentences of analysis)
        """)
    ])
    
    REPORT_ENGAGEMENT_BREAKDOWN = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
            You are an AI assistant that analyzes church visitor data and creates a summary report.
            For the Visitor Engagement Breakdown section, analyze the data to extract:
            1. Interests Distribution (e.g., percentage interested in Worship, Bible Study, etc.)
            2. Common Concerns expressed by visitors
            3. Identified Needs from visitors
            4. Feedback Sentiment analysis (positive vs. negative)
            5. Top Requests made by visitors
            
            Your output should identify patterns and trends in visitor engagement.
        """),
        HumanMessage(content="""
            Please create the Visitor Engagement Breakdown section based on the following data:
            
            Followup Data: {followup_data}
            Analytics Data: {analytics_data}
            
            Format the output as a JSON object with these fields:
            - interests: object (mapping interest categories to percentages)
            - concerns: array of objects (each with text and frequency)
            - needs: array of objects (each with text and frequency)
            - feedback_sentiment: object (positive percentage, negative percentage, neutral percentage)
            - top_requests: array of objects (each with text and frequency)
            - summary_text: string (3-4 sentences of analysis)
        """)
    ])
    
    REPORT_OUTCOME_TRENDS = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
            You are an AI assistant that analyzes church visitor data and creates a summary report.
            For the Follow-Up Outcomes & Decision Trends section, analyze the data to extract:
            1. Visitor Decisions (joined, undecided, not interested)
            2. Reasons for Decisions
            3. Next Steps Taken with visitors
            
            Your output should identify patterns and correlations between decisions and visitor characteristics.
        """),
        HumanMessage(content="""
            Please create the Follow-Up Outcomes & Decision Trends section based on the following data:
            
            Followup Data: {followup_data}
            Analytics Data: {analytics_data}
            
            Format the output as a JSON object with these fields:
            - decisions: object (mapping decision categories to percentages)
            - reasons: array of objects (each with decision, reason, and frequency)
            - next_steps: object (mapping next steps to percentages)
            - correlations: array of string (identified correlations between visitor traits and decisions)
            - summary_text: string (3-4 sentences of analysis)
        """)
    ])
    
    REPORT_INDIVIDUAL_SUMMARIES = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
            You are an AI assistant that analyzes church visitor data and creates a summary report.
            For the Individual/Family Notes Summary section, create concise summaries for each visitor/family.
            Each summary should include:
            1. Key follow-up details
            2. Notes taken by volunteers
            3. Any unresolved concerns requiring additional action
            
            Limit each individual summary to 2-3 sentences focusing on the most important information.
        """),
        HumanMessage(content="""
            Please create the Individual/Family Notes Summary section based on the following data:
            
            Followup Data: {followup_data}
            
            Format the output as an array of objects, each with these fields:
            - visitor_id: string
            - family_id: string (if applicable)
            - name: string
            - summary: string (2-3 sentences)
            - status: string (e.g., "Completed", "Pending Follow-up", "Requires Attention")
            - key_points: array of string (bullet points of important information)
        """)
    ])
    
    REPORT_RECOMMENDATIONS = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
            You are an AI assistant that analyzes church visitor data and creates a summary report.
            For the Recommendations section, generate actionable insights based on all previous analysis.
            Your recommendations should be:
            1. Specific and actionable
            2. Based on patterns and trends identified in the data
            3. Aimed at improving visitor engagement and conversion
            4. Prioritized by potential impact
            
            Provide 3-5 high-quality recommendations.
        """),
        HumanMessage(content="""
            Please create the Recommendations section based on the previous analysis:
            
            Visitor Summary: {visitor_summary}
            Engagement Breakdown: {engagement_breakdown}
            Outcome Trends: {outcome_trends}
            Individual Summaries: {individual_summaries}
            
            Format the output as an array of objects, each with these fields:
            - recommendation: string (the specific recommendation)
            - rationale: string (why this is recommended)
            - impact: string (expected outcome if implemented)
            - priority: number (1-5, with 1 being highest priority)
        """)
    ])
    
    REPORT_ASSEMBLER = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
            You are an AI assistant that assembles a comprehensive church visitor follow-up report.
            Combine all the section data into a cohesive report structure that includes:
            1. Visitor Summary
            2. Engagement Breakdown
            3. Outcome Trends
            4. Individual/Family Summaries
            5. Recommendations
            
            Ensure the report has a consistent style and narrative flow between sections.
        """),
        HumanMessage(content="""
            Please assemble the final report using the following section data:
            
            Visitor Summary: {visitor_summary}
            Engagement Breakdown: {engagement_breakdown}
            Outcome Trends: {outcome_trends}
            Individual Summaries: {individual_summaries}
            Recommendations: {recommendations}
            
            Date Range: {start_date} to {end_date}
            
            Format the output as a single JSON object with these sections as top-level keys,
            and add a 'metadata' section with report generation details.
        """)
    ])
    
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
            'followup_summary': cls.FOLLOWUP_SUMMARY,
            'report_visitor_summary': cls.REPORT_VISITOR_SUMMARY,
            'report_engagement_breakdown': cls.REPORT_ENGAGEMENT_BREAKDOWN,
            'report_outcome_trends': cls.REPORT_OUTCOME_TRENDS,
            'report_individual_summaries': cls.REPORT_INDIVIDUAL_SUMMARIES,
            'report_recommendations': cls.REPORT_RECOMMENDATIONS,
            'report_assembler': cls.REPORT_ASSEMBLER
        }