from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
import langsmith
#from langchain.smith import RunEvaluator
from langgraph.graph import Graph

from app.data.data_fetcher import DataFetcher
from app.data.report_repository2 import ReportRepository
from app.data.storage import S3Storage
from app.api.schemas.report import ReportStatus
from app.utils.pdf_generator import PDFGenerator
from app.security.token_service import TokenService
from app.config.settings import get_settings
from app.llm.prompts import PromptLibrary

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
        self.prompts = PromptLibrary.get_prompts()
    
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
        chain = LLMChain(llm=self.llm, prompt=self.prompts['report_visitor_summary'])
        return chain
    
    def _create_engagement_breakdown_node(self):
        """Create a node for generating the engagement breakdown section"""
        chain = LLMChain(llm=self.llm, prompt=self.prompts['report_engagement_breakdown'])
        return chain
    
    def _create_outcome_trends_node(self):
        """Create a node for generating the outcome trends section"""
        chain = LLMChain(llm=self.llm, prompt=self.prompts['report_outcome_trends'])
        return chain
    
    def _create_individual_summaries_node(self):
        """Create a node for generating individual/family summaries"""
        chain = LLMChain(llm=self.llm, prompt=self.prompts['report_individual_summaries'])
        return chain
    
    def _create_recommendations_node(self):
        """Create a node for generating recommendations section"""
        chain = LLMChain(llm=self.llm, prompt=self.prompts['report_recommendations'])
        return chain
    
    def _create_report_assembler_node(self):
        """Create a node for assembling the final report"""
        chain = LLMChain(llm=self.llm, prompt=self.prompts['report_assembler'])
        return chain