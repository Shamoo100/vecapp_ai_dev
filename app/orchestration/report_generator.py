from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.retrievers import TenantAwareRetriever
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
import langsmith
from langchain.smith import RunEvaluator

from app.data.data_fetcher import DataFetcher
from app.data.report_repository import ReportRepository
from app.data.storage import S3Storage
from app.models.report import ReportStatus
from app.utils.pdf_generator import PDFGenerator
from app.security.token_service import TokenService
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ReportGenerator:
    """Service for generating AI reports using LangChain and LangGraph"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0, api_key=settings.OPENAI_API_KEY)
        self.data_fetcher = DataFetcher()
        self.report_repository = ReportRepository()
        self.s3_storage = S3Storage()
        self.pdf_generator = PDFGenerator()
        self.token_service = TokenService()
    
    async def generate_report(
        self,
        report_id: UUID,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
        report_type: str
    ):
        """Generate a follow-up summary report"""
        try:
            # Update report status to processing
            await self.report_repository.update_report(
                report_id=report_id,
                tenant_id=tenant_id,
                status=ReportStatus.PROCESSING
            )
            
            # Get system token for inter-service communication
            system_token = self.token_service.generate_system_token(tenant_id)
            
            # Fetch data from required services
            followup_data = await self.data_fetcher.fetch_followup_data(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                auth_token=system_token
            )
            
            analytics_data = await self.data_fetcher.fetch_analytics_data(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                auth_token=system_token
            )
            
            # Process the data using LangChain and LangGraph
            report_data = await self._process_report_data(
                tenant_id=tenant_id,
                followup_data=followup_data,
                analytics_data=analytics_data,
                start_date=start_date,
                end_date=end_date,
                report_type=report_type
            )
            
            # Generate PDF
            pdf_data = self.pdf_generator.generate_pdf(report_data)
            
            # Upload PDF to S3
            pdf_key = f"reports/{tenant_id}/{report_id}.pdf"
            await self.s3_storage.upload_file(pdf_key, pdf_data)
            
            # Update report record with results
            await self.report_repository.update_report(
                report_id=report_id,
                tenant_id=tenant_id,
                status=ReportStatus.COMPLETED,
                pdf_storage_key=pdf_key,
                report_summary_data=report_data
            )
            
            logger.info(f"Successfully generated report {report_id} for tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Error generating report {report_id} for tenant {tenant_id}: {str(e)}")
            # Update report status to failed
            await self.report_repository.update_report(
                report_id=report_id,
                tenant_id=tenant_id,
                status=ReportStatus.FAILED,
                error_message=str(e)
            )
    
    async def _process_report_data(
        self,
        tenant_id: UUID,
        followup_data: Dict[str, Any],
        analytics_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        report_type: str
    ) -> Dict[str, Any]:
        """Process the data and generate the report structure"""
        # Create LangGraph for report generation
        report_graph = self._create_report_graph()
        
        # Prepare input data
        input_data = {
            "tenant_id": str(tenant_id),
            "followup_data": followup_data,
            "analytics_data": analytics_data,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "report_type": report_type
        }
        
        # Execute the graph
        with langsmith.trace(
            project_name=settings.LANGSMITH_PROJECT,
            name=f"FollowupSummaryReport-{tenant_id}"
        ) as tracer:
            result = report_graph.invoke(input_data)
        
        return result["output"]
    
    def _create_report_graph(self):
        """Create a LangGraph for report generation"""
        # Create graph nodes for different sections of the report
        visitor_summary_node = self._create_visitor_summary_node()
        engagement_breakdown_node = self._create_engagement_breakdown_node()
        outcome_trends_node = self._create_outcome_trends_node()
        individual_summaries_node = self._create_individual_summaries_node()
        recommendations_node = self._create_recommendations_node()
        report_assembler_node = self._create_report_assembler_node()
        
        # Create graph
        graph = Graph()
        graph.add_node("visitor_summary", visitor_summary_node)
        graph.add_node("engagement_breakdown", engagement_breakdown_node)
        graph.add_node("outcome_trends", outcome_trends_node)
        graph.add_node("individual_summaries", individual_summaries_node)
        graph.add_node("recommendations", recommendations_node)
        graph.add_node("report_assembler", report_assembler_node)
        
        # Define graph edges
        graph.add_edge("visitor_summary", "engagement_breakdown")
        graph.add_edge("engagement_breakdown", "outcome_trends")
        graph.add_edge("outcome_trends", "individual_summaries")
        graph.add_edge("individual_summaries", "recommendations")
        graph.add_edge(["visitor_summary", "engagement_breakdown", "outcome_trends", 
                        "individual_summaries", "recommendations"], "report_assembler")
        
        return graph.compile()
    
    def _create_visitor_summary_node(self):
        """Create a node for generating the visitor summary section"""
        prompt = ChatPromptTemplate.from_messages([
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
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain
    
    def _create_engagement_breakdown_node(self):
        """Create a node for generating the engagement breakdown section"""
        prompt = ChatPromptTemplate.from_messages([
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
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain
    
    def _create_outcome_trends_node(self):
        """Create a node for generating the outcome trends section"""
        prompt = ChatPromptTemplate.from_messages([
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
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain
    
    def _create_individual_summaries_node(self):
        """Create a node for generating individual/family summaries"""
        prompt = ChatPromptTemplate.from_messages([
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
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain
    
    def _create_recommendations_node(self):
        """Create a node for generating recommendations section"""
        prompt = ChatPromptTemplate.from_messages([
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
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain
    
    def _create_report_assembler_node(self):
        """Create a node for assembling the final report"""
        prompt = ChatPromptTemplate.from_messages([
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
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain