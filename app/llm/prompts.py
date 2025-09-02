"""Centralized prompt templates for LLM interactions."""
from typing import Dict,Any, List
import json
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage


class PromptLibrary:
    """Manages and provides access to all prompt templates."""
    
    # Visitor Analysis Prompts
    VISITOR_ANALYSIS = PromptTemplate(
        input_variables=["visitor_data", "context"],
        template="""
        Analyze the following visitor data and context and provide key insights:
        Visitor Data: {visitor_data}
        Context: {context}

        Your response **must** be a JSON object with the following structure and no extra text:
        {{
        "interests": ["list of key interests"],
        "needs": ["list of identified needs"],
        "engagement_opportunities": ["list of opportunities"],
        "sentiment": "positive/neutral/negative",
        "follow_up_actions": ["list of recommended actions"],
        "confidence": 0.85
        }}

        Return only valid JSON with these fields and do not include any explanatory prose.
        """
            )

    # Recommendation Prompts
    RECOMMENDATIONS = PromptTemplate(
        input_variables=[
            "visitor_data",
            "welcome_form_data",
            "team_names",
            "group_names",
            "event_names",
            "available_opportunities",
        ],
        template="""
        Using the visitor data and available opportunities, craft personalized recommendations.  Provide concrete suggestions for:
        • Community integration
        • Event engagement
        • Addressing personal needs
        • Followup actions

        Inputs:
        Visitor Data: {visitor_data}
        Welcome Form Data: {welcome_form_data}
        Available Opportunities: {available_opportunities}
        Team Names: {team_names}
        Group Names: {group_names}
        Event Names: {event_names}

        Return the recommendations strictly as a JSON object with exactly these top‑level keys:
        {{
        "community_integration": [ {{"title": "", "description": ""}}, ... ],
        "event_engagement": [ {{"title": "", "description": ""}}, ... ],
        "personal_needs": {{"identified_needs": [""], "action_recommendations": [""], "escalation_required": false}},
        "feedback_insights": {{"key_takeaways": [""], "actions": [""]}}
        }}

        Do not add any narrative explanation—respond with valid JSON only.
        """
            )

    # Sentiment Analysis Prompts
    SENTIMENT_ANALYSIS = PromptTemplate(
        input_variables=["feedback_data", "context"],
        template="""
        Analyze the sentiment of the provided feedback data and context.
        Feedback Data: {feedback_data}
        Context: {context}

        Your output must be a JSON object with the following fields:
        {{
        "overall_sentiment": "positive/neutral/negative",
        "themes": ["list of key themes or topics"],
        "strengths": ["list of strengths"],
        "weaknesses": ["list of weaknesses"],
        "areas_for_improvement": ["list of improvement areas"],
        "confidence": 0.75
        }}

        Return only valid JSON—no additional commentary or markdown.
        """
            )
            
            
    # Feedback Analysis Prompts
    FEEDBACK_ANALYSIS = PromptTemplate(
        input_variables=["feedback_data", "historical_context"],
        template="""
        Analyze the provided feedback and its historical context.
        Feedback: {feedback_data}
        Historical Context: {historical_context}

        Your analysis should be returned as a JSON object with these fields:
        {{
        "sentiment_and_key_themes": ["list of sentiments and themes"],
        "areas_for_improvement": ["list of improvement areas"],
        "success_patterns": ["list of success patterns"],
        "recommended_adjustments": ["list of adjustments"]
        }}

        Respond with valid JSON only—omit any additional prose or formatting.
        """
            )
            
   
    
    # Report Generator Prompts
    #TODO: Clean up..currently not in use (Summary Report)
    REPORT_VISITOR_SUMMARY = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
        You are an AI assistant that analyzes church visitor data and creates a summary report.
        For the Visitor Summary section, extract metrics such as:
        1. Total visitors followed up within the given date range
        2. Count of single‑family vs. multi‑family engagements
        3. Total number of family members engaged

        Provide your response in a concise, data‑driven format.
        """),
                HumanMessage(content="""
        Please create the Visitor Summary section using the following data:

        Date Range: {start_date} to {end_date}
        Followup Data: {followup_data}

        Return a JSON object with exactly these keys and no extra text:
        {
        "total_visitors": 0,
        "single_family": 0,
        "multi_family": 0,
        "total_family_members": 0,
        "summary_text": "2-3 sentences summarizing the findings"
        }
        """)
            ])

    # Follow-up Summary Prompts
    #TODO: Clean up..currently not in use (Summary Report)
    FOLLOWUP_SUMMARY = PromptTemplate(
        input_variables=["interaction_history", "outcomes"],
        template="""
        Summarize the given interaction history and outcomes.
        Interaction History: {interaction_history}
        Outcomes: {outcomes}

        Return the summary strictly as a JSON object with these keys:
        {{
        "discussion_points": ["list of key discussion points"],
        "decisions_made": ["list of decisions"],
        "action_items": ["list of action items"],
        "next_steps": ["list of next steps"],
        "summary_text": "2-3 sentence overall summary"
        }}

        Do not include any narrative text outside of this JSON structure.
        """
            )
     #TODO: Clean up..currently not in use (Summary Report)       
    REPORT_ENGAGEMENT_BREAKDOWN = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
        You are an AI assistant that analyzes church visitor data and creates a summary report. For the Visitor Engagement Breakdown section, identify patterns and trends in visitor engagement, including:
        1. Interests distribution (percentages across categories such as Worship, Bible Study, etc.)
        2. Common concerns expressed by visitors
        3. Identified needs from visitors
        4. Feedback sentiment (positive, negative, neutral)
        5. Top requests made by visitors
        """),
                HumanMessage(content="""
        Please create the Visitor Engagement Breakdown section based on the following:

        Followup Data: {followup_data}
        Analytics Data: {analytics_data}

        Return your findings as a JSON object with these keys:
        {
        "interests": {"category": 0.0},
        "concerns": [ {"text": "", "frequency": 0}, ... ],
        "needs": [ {"text": "", "frequency": 0}, ... ],
        "feedback_sentiment": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
        "top_requests": [ {"text": "", "frequency": 0}, ... ],
        "summary_text": "3-4 sentences summarizing the engagement patterns"
        }

        Do not include any explanatory text outside of this JSON object.
        """)
            ])
    #TODO: Clean up..currently not in use (Visitor Journey)
    REPORT_OUTCOME_TRENDS = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
        You are an AI assistant that analyzes church visitor data and creates a summary report. For the Follow‑Up Outcomes & Decision Trends section, highlight patterns and correlations between visitor characteristics and their decisions. Focus on:
        1. Visitor decisions (joined, undecided, not interested)
        2. Reasons for those decisions
        3. Next steps taken with visitors
        """),
                HumanMessage(content="""
        Using the provided data, produce the Follow‑Up Outcomes & Decision Trends section.

        Followup Data: {followup_data}
        Analytics Data: {analytics_data}

        Return a JSON object with these fields and no extra commentary:
        {
        "decisions": {"joined": 0.0, "undecided": 0.0, "not_interested": 0.0},
        "reasons": [ {"decision": "", "reason": "", "frequency": 0}, ... ],
        "next_steps": {"step": 0.0},
        "correlations": ["description of correlation", ... ],
        "summary_text": "3-4 sentences summarizing the trends"
        }
        """)
            ])
    #TODO: Clean up..currently not in use (snapshot)
    REPORT_INDIVIDUAL_SUMMARIES = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
        You are an AI assistant that analyzes church visitor data and creates a summary report.  For the Individual/Family Notes Summary section, generate concise summaries for each visitor or family, highlighting:
        • Key follow‑up details
        • Volunteer notes
        • Any unresolved concerns requiring additional action

        Limit each summary to the most critical information.
        """),
                HumanMessage(content="""
        Create the Individual/Family Notes Summary using this data:

        Followup Data: {followup_data}

        Return an array of objects in JSON with the following fields:
        [
        {
            "visitor_id": "",
            "family_id": "" (omit or empty if not applicable),
            "name": "",
            "summary": "2-3 sentences summarizing the visit",
            "status": "Completed/Pending Follow-up/Requires Attention",
            "key_points": ["bullet point of important information", ...]
        },
        ...
        ]

        Only output valid JSON—no additional narrative or markdown.
        """)
            ])
     #TODO: Clean up..currently not in use        
    REPORT_RECOMMENDATIONS = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
        You are an AI assistant that analyzes church visitor data and creates a summary report. For the Recommendations section, provide 3 specific, actionable insights that are grounded in the patterns and trends identified in the previous analyses.  Rank them by potential impact.
        """),
                HumanMessage(content="""
        Generate the Recommendations section using the previous analysis:

        Visitor Summary: {visitor_summary}
        Engagement Breakdown: {engagement_breakdown}
        Outcome Trends: {outcome_trends}
        Individual Summaries: {individual_summaries}

        Return an array of JSON objects in this format:
        [
        {
            "recommendation": "specific recommendation",
            "rationale": "brief rationale",
            "impact": "expected outcome if implemented",
            "priority": 1
        },
        ...
        ]

        Do not include any text outside of the JSON array.
        """)
            ])
   #TODO: Clean up..currently not in use 
    REPORT_ASSEMBLER = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
        You are an AI assistant that assembles a comprehensive church visitor follow‑up report.  Combine the provided sections into a cohesive report containing:
        1. Visitor Summary
        2. Engagement Breakdown
        3. Outcome Trends
        4. Individual/Family Summaries
        5. Recommendations

        Ensure consistent style and narrative flow across sections.
        """),
                HumanMessage(content="""
        Assemble the final report from the following sections:

        Visitor Summary: {visitor_summary}
        Engagement Breakdown: {engagement_breakdown}
        Outcome Trends: {outcome_trends}
        Individual Summaries: {individual_summaries}
        Recommendations: {recommendations}

        Date Range: {start_date} to {end_date}

        Return a single JSON object with these top‑level keys:
        {
        "visitor_summary": {...},
        "engagement_breakdown": {...},
        "outcome_trends": {...},
        "individual_summaries": [...],
        "recommendations": [...],
        "metadata": {
            "start_date": "{start_date}",
            "end_date": "{end_date}",
            "generated_at": "ISO 8601 timestamp"
        }
        }

        Do not include any explanatory prose—return valid JSON only.
        """)
            ])

    # Volunteer Matching Prompts
    #TODO: Clean up..currently not in use (Volunteer Matching/Workforce)
    VOLUNTEER_MATCHING = PromptTemplate(
        input_variables=["visitor_needs", "volunteer_profiles"],
        template="""
        Given a list of visitor needs and available volunteer profiles, determine the best matches.
        Visitor Needs: {visitor_needs}
        Volunteer Profiles: {volunteer_profiles}

        Evaluate each match using:
        • Skill alignment
        • Availability
        • Past performance
        • Communication style

        Return a JSON object with a single key `matches` whose value is an array of ranked match objects.  Each match object should contain:
        {{
        "volunteer_id": "identifier",
        "score": 0.0,
        "reasons": ["brief justification"]
        }}

        Only output valid JSON—no extra text or explanation.
        """
            )
    
    @classmethod
    def get_prompts(cls) -> Dict[str, PromptTemplate]:
        """Get all available prompt templates.
        
        Returns:
            Dictionary mapping prompt names to templates
        """
        return {
            'visitor_analysis': cls.VISITOR_ANALYSIS,
            'recommendations': cls.RECOMMENDATIONS,
            'sentiment_analysis': cls.SENTIMENT_ANALYSIS,
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

    @classmethod
    def get_visitor_profile_analysis_prompt(cls, visitor_data: Dict[str, Any], context: str) -> str:
        return cls.VISITOR_ANALYSIS.format(
            visitor_data=visitor_data,
            context=context
        )
    
    @classmethod
    def get_sentiment_analysis_prompt(cls, feedback_data: Dict[str, Any], historical_context: str) -> str:
        """Create a sentiment analysis prompt that produces structured JSON output.

        This uses the SENTIMENT_ANALYSIS template, which instructs the LLM to
        return a JSON object describing overall sentiment, key themes, strengths,
        weaknesses, areas for improvement, and a confidence score.

        Args:
            feedback_data: The raw feedback data to analyse.
            historical_context: Additional context that may influence sentiment.

        Returns:
            A formatted prompt string.
        """
        return cls.SENTIMENT_ANALYSIS.format(
            feedback_data=feedback_data,
            context=historical_context,
        )
    
    @classmethod
    def get_recommendations_prompt(cls, visitor_data: Dict[str, Any], 
                                 welcome_form_data: Dict[str, Any], 
                                 team_names: List[str], 
                                 group_names: List[str], 
                                 event_names: List[str]) -> str:
        # Combine opportunities for the template
        available_opportunities = {
            "teams": team_names,
            "groups": group_names, 
            "events": event_names
        }
        
        return cls.RECOMMENDATIONS.format(
            visitor_data=visitor_data,
            available_opportunities=available_opportunities,
            welcome_form_data=welcome_form_data,
            team_names=team_names,
            group_names=group_names,
            event_names=event_names
        )

    # @classmethod
    def get_journey_analysis_prompt(self, visitor_profile: Dict, follow_up_tasks: List, notes: List, interactions: List) -> str:

        """Generate prompt for journey analysis"""
        return f"""
    Analyze this visitor's follow-up journey and provide structured insights:
    
    VISITOR PROFILE:
    {json.dumps(visitor_profile, indent=2)}
    
    FOLLOW-UP TASKS:
    {json.dumps(follow_up_tasks, indent=2)}
    
    NOTES & INTERACTIONS:
    {json.dumps(notes + interactions, indent=2)}
    
    Provide analysis in this JSON format:
    {{
        "visitor_decision": "joined|undecided|not_interested",
        "decision_rationale": "Brief explanation of decision factors",
        "unresolved_needs": ["list", "of", "unmet", "needs"],
        "ai_recommendations": ["specific", "next", "steps"],
        "sentiment_analysis": "positive|neutral|negative",
        "engagement_level": "high|medium|low"
    }}
    """










# """Centralized prompt templates for LLM interactions."""
# from typing import Dict,Any, List
# from langchain.prompts import PromptTemplate
# from langchain_core.messages import SystemMessage, HumanMessage
# from langchain.prompts.chat import ChatPromptTemplate
# # from langchain.prompts import PromptTemplate
# # from langchain.prompts.chat import ChatPromptTemplate
# # from langchain_core.messages import SystemMessage, HumanMessage
# # from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
# # from langchain_core.messages import SystemMessage, HumanMessage


# class PromptLibrary:
#     """Manages and provides access to all prompt templates."""
    
#     # Visitor Analysis Prompts
#     VISITOR_ANALYSIS = PromptTemplate(
#         input_variables=["visitor_data", "context"],
#         template="""Analyze the following visitor data and context:
#         Visitor Data: {visitor_data}
#         Context: {context}
        
#         Provide insights on:
#         1. Key interests and needs
#         2. Potential engagement opportunities
#         3. Sentiment based on feedback on visitor form
#         4. Recommended follow-up actions
        
#         Format your response as a JSON object with these exact fields:
#         {{
#             "interests": ["list of key interests"],
#             "needs": ["list of identified needs"],
#             "engagement_opportunities": ["list of opportunities"],
#             "sentiment": "positive/neutral/negative",
#             "follow_up_actions": ["list of recommended actions"],
#             "confidence": 0.85
#         }}
        
#         Return only valid JSON, no additional text."""
#     )

#     # Recommendation Prompts
#     RECOMMENDATIONS = PromptTemplate(
#         input_variables=["visitor_data", "welcome_form_data", "team_names", "group_names", "event_names", "available_opportunities"],
#         template="""Based on the visitor data and available opportunities, generate personalized recommendations:
        
#         Visitor Data: {visitor_data}
#         Available Opportunities: {available_opportunities}
        
#         Welcome Form Data: {welcome_form_data}
#         Team Names: {team_names}
#         Group Names: {group_names}
#         Event Names: {event_names}
#         Provide specific recommendations for:
#         1. Community integration opportunities
#         2. Event engagement suggestions
#         3. Personal needs addressing
#         4. Follow-up actions
        
#         Format as JSON with categories: community_integration, event_engagement, personal_needs, feedback_insights"""
#     )

#     # Sentiment Analysis Prompts
#     # SENTIMENT_ANALYSIS = PromptTemplate(
#     #     input_variables=["feedback_data", "context"],
#     #     template="""Analyze the sentiment of the following feedback data:
#     #     Feedback Data: {feedback_data}
#     #     Context: {context}
        
#     #     Provide a sentiment score and analysis on:
#     #     1. Overall sentiment
#     #     2. Key themes or topics
#     #     3. Strengths and weaknesses
#     #     4. Potential areas for improvement
#     #     """
#     # )
#     SENTIMENT_ANALYSIS = PromptTemplate(
#     input_variables=["feedback_data", "context"],
#     template=(
#         "Analyze the sentiment of the following feedback data and context:\n"
#         "Feedback Data: {feedback_data}\nContext: {context}\n\n"
#         "Provide a JSON response with these fields:\n"
#         "overall_sentiment: string\n"
#         "confidence: number\n"
#         "key_themes: array of strings\n"
#         "strengths: array of strings\n"
#         "areas_for_improvement: array of strings\n"
#     ),
# )

    
#     # Volunteer Matching Prompts
#     VOLUNTEER_MATCHING = PromptTemplate(
#         input_variables=["visitor_needs", "volunteer_profiles"],
#         template="""Match the following visitor needs with available volunteers:
#         Visitor Needs: {visitor_needs}
#         Volunteer Profiles: {volunteer_profiles}
        
#         Evaluate and rank matches based on:
#         1. Skill alignment
#         2. Availability
#         3. Past performance
#         4. Communication style"""
#     )
    
#     # Feedback Analysis Prompts
#     FEEDBACK_ANALYSIS = PromptTemplate(
#         input_variables=["feedback_data", "historical_context"],
#         template="""Analyze the following feedback and historical context:
#         Feedback: {feedback_data}
#         Historical Context: {historical_context}
        
#         Provide analysis on:
#         1. Sentiment and key themes
#         2. Areas for improvement
#         3. Success patterns
#         4. Recommended adjustments"""
#     )
    
#     # Follow-up Summary Prompts
#     FOLLOWUP_SUMMARY = PromptTemplate(
#         input_variables=["interaction_history", "outcomes"],
#         template="""Summarize the following interaction and outcomes:
#         Interaction History: {interaction_history}
#         Outcomes: {outcomes}
        
#         Generate a comprehensive summary including:
#         1. Key discussion points
#         2. Decisions made
#         3. Action items
#         4. Next steps"""
#     )
    
#     # Report Generator Prompts
#     REPORT_VISITOR_SUMMARY = ChatPromptTemplate.from_messages([
#         SystemMessage(content="""
#             You are an AI assistant that analyzes church visitor data and creates a summary report.
#             For the Visitor Summary section, analyze the data to extract:
#             1. Total visitors followed up within the given date range
#             2. Count of single-family vs. multi-family engagements
#             3. Total number of family members engaged
            
#             Your output should be structured as a detailed section with key metrics and brief analysis.
#         """),
#         HumanMessage(content="""
#             Please create the Visitor Summary section based on the following data:
            
#             Date Range: {start_date} to {end_date}
#             Followup Data: {followup_data}
            
#             Format the output as a JSON object with these fields:
#             - total_visitors: number
#             - single_family: number
#             - multi_family: number
#             - total_family_members: number
#             - summary_text: string (2-3 sentences of analysis)
#         """)
#     ])
    
#     REPORT_ENGAGEMENT_BREAKDOWN = ChatPromptTemplate.from_messages([
#         SystemMessage(content="""
#             You are an AI assistant that analyzes church visitor data and creates a summary report.
#             For the Visitor Engagement Breakdown section, analyze the data to extract:
#             1. Interests Distribution (e.g., percentage interested in Worship, Bible Study, etc.)
#             2. Common Concerns expressed by visitors
#             3. Identified Needs from visitors
#             4. Feedback Sentiment analysis (positive vs. negative)
#             5. Top Requests made by visitors
            
#             Your output should identify patterns and trends in visitor engagement.
#         """),
#         HumanMessage(content="""
#             Please create the Visitor Engagement Breakdown section based on the following data:
            
#             Followup Data: {followup_data}
#             Analytics Data: {analytics_data}
            
#             Format the output as a JSON object with these fields:
#             - interests: object (mapping interest categories to percentages)
#             - concerns: array of objects (each with text and frequency)
#             - needs: array of objects (each with text and frequency)
#             - feedback_sentiment: object (positive percentage, negative percentage, neutral percentage)
#             - top_requests: array of objects (each with text and frequency)
#             - summary_text: string (3-4 sentences of analysis)
#         """)
#     ])
    
#     REPORT_OUTCOME_TRENDS = ChatPromptTemplate.from_messages([
#         SystemMessage(content="""
#             You are an AI assistant that analyzes church visitor data and creates a summary report.
#             For the Follow-Up Outcomes & Decision Trends section, analyze the data to extract:
#             1. Visitor Decisions (joined, undecided, not interested)
#             2. Reasons for Decisions
#             3. Next Steps Taken with visitors
            
#             Your output should identify patterns and correlations between decisions and visitor characteristics.
#         """),
#         HumanMessage(content="""
#             Please create the Follow-Up Outcomes & Decision Trends section based on the following data:
            
#             Followup Data: {followup_data}
#             Analytics Data: {analytics_data}
            
#             Format the output as a JSON object with these fields:
#             - decisions: object (mapping decision categories to percentages)
#             - reasons: array of objects (each with decision, reason, and frequency)
#             - next_steps: object (mapping next steps to percentages)
#             - correlations: array of string (identified correlations between visitor traits and decisions)
#             - summary_text: string (3-4 sentences of analysis)
#         """)
#     ])
    
#     REPORT_INDIVIDUAL_SUMMARIES = ChatPromptTemplate.from_messages([
#         SystemMessage(content="""
#             You are an AI assistant that analyzes church visitor data and creates a summary report.
#             For the Individual/Family Notes Summary section, create concise summaries for each visitor/family.
#             Each summary should include:
#             1. Key follow-up details
#             2. Notes taken by volunteers
#             3. Any unresolved concerns requiring additional action
            
#             Limit each individual summary to 2-3 sentences focusing on the most important information.
#         """),
#         HumanMessage(content="""
#             Please create the Individual/Family Notes Summary section based on the following data:
            
#             Followup Data: {followup_data}
            
#             Format the output as an array of objects, each with these fields:
#             - visitor_id: string
#             - family_id: string (if applicable)
#             - name: string
#             - summary: string (2-3 sentences)
#             - status: string (e.g., "Completed", "Pending Follow-up", "Requires Attention")
#             - key_points: array of string (bullet points of important information)
#         """)
#     ])
    
#     REPORT_RECOMMENDATIONS = ChatPromptTemplate.from_messages([
#         SystemMessage(content="""
#             You are an AI assistant that analyzes church visitor data and creates a summary report.
#             For the Recommendations section, generate actionable insights based on all previous analysis.
#             Your recommendations should be:
#             1. Specific and actionable
#             2. Based on patterns and trends identified in the data
#             3. Aimed at improving visitor engagement and conversion
#             4. Prioritized by potential impact
            
#             Provide 3-5 high-quality recommendations.
#         """),
#         HumanMessage(content="""
#             Please create the Recommendations section based on the previous analysis:
            
#             Visitor Summary: {visitor_summary}
#             Engagement Breakdown: {engagement_breakdown}
#             Outcome Trends: {outcome_trends}
#             Individual Summaries: {individual_summaries}
            
#             Format the output as an array of objects, each with these fields:
#             - recommendation: string (the specific recommendation)
#             - rationale: string (why this is recommended)
#             - impact: string (expected outcome if implemented)
#             - priority: number (1-5, with 1 being highest priority)
#         """)
#     ])
    
#     REPORT_ASSEMBLER = ChatPromptTemplate.from_messages([
#         SystemMessage(content="""
#             You are an AI assistant that assembles a comprehensive church visitor follow-up report.
#             Combine all the section data into a cohesive report structure that includes:
#             1. Visitor Summary
#             2. Engagement Breakdown
#             3. Outcome Trends
#             4. Individual/Family Summaries
#             5. Recommendations
            
#             Ensure the report has a consistent style and narrative flow between sections.
#         """),
#         HumanMessage(content="""
#             Please assemble the final report using the following section data:
            
#             Visitor Summary: {visitor_summary}
#             Engagement Breakdown: {engagement_breakdown}
#             Outcome Trends: {outcome_trends}
#             Individual Summaries: {individual_summaries}
#             Recommendations: {recommendations}
            
#             Date Range: {start_date} to {end_date}
            
#             Format the output as a single JSON object with these sections as top-level keys,
#             and add a 'metadata' section with report generation details.
#         """)
#     ])
    
#     @classmethod
#     def get_prompts(cls) -> Dict[str, PromptTemplate]:
#         """Get all available prompt templates.
        
#         Returns:
#             Dictionary mapping prompt names to templates
#         """
#         return {
#             'visitor_analysis': cls.VISITOR_ANALYSIS,
#             'recommendations': cls.RECOMMENDATIONS,
#             'sentiment_analysis': cls.SENTIMENT_ANALYSIS,
#             'volunteer_matching': cls.VOLUNTEER_MATCHING,
#             'feedback_analysis': cls.FEEDBACK_ANALYSIS,
#             'followup_summary': cls.FOLLOWUP_SUMMARY,
#             'report_visitor_summary': cls.REPORT_VISITOR_SUMMARY,
#             'report_engagement_breakdown': cls.REPORT_ENGAGEMENT_BREAKDOWN,
#             'report_outcome_trends': cls.REPORT_OUTCOME_TRENDS,
#             'report_individual_summaries': cls.REPORT_INDIVIDUAL_SUMMARIES,
#             'report_recommendations': cls.REPORT_RECOMMENDATIONS,
#             'report_assembler': cls.REPORT_ASSEMBLER
#         }

#     @classmethod
#     def get_visitor_profile_analysis_prompt(cls, visitor_data: Dict[str, Any], context: str) -> str:
#         return cls.VISITOR_ANALYSIS.format(
#             visitor_data=visitor_data,
#             context=context
#         )
    
#     @classmethod
#     def get_sentiment_analysis_prompt(cls, feedback_data: Dict[str, Any], historical_context: str) -> str:
#         return cls.FEEDBACK_ANALYSIS.format(
#             feedback_data=feedback_data,
#             historical_context=historical_context
#         )
    
#     @classmethod
#     def get_recommendations_prompt(cls, visitor_data: Dict[str, Any], 
#                                  welcome_form_data: Dict[str, Any], 
#                                  team_names: List[str], 
#                                  group_names: List[str], 
#                                  event_names: List[str]) -> str:
#         # Combine opportunities for the template
#         available_opportunities = {
#             "teams": team_names,
#             "groups": group_names, 
#             "events": event_names
#         }
        
#         return cls.RECOMMENDATIONS.format(
#             visitor_data=visitor_data,
#             available_opportunities=available_opportunities,
#             welcome_form_data=welcome_form_data,
#             team_names=team_names,
#             group_names=group_names,
#             event_names=event_names
#         )
