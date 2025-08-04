"""
Simplified Followup Service for AI-powered visitor follow-up notes.
Works with the new simplified visitor context builder.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
import os
from uuid import UUID

from app.agents.followup_note_agent import FollowupNoteAgent
from app.services.visitor_context_builder import VisitorContextBuilder
from app.infastructure.aws.sqs_client import NewVisitorSQSClient
from app.services.member_service import MemberService
#from app.database.repositories.tenant_context import TenantContextMiddleware
from app.database.repositories.connection import DatabaseConnection
from app.data.repositories.ai_service_repository import AITaskRepository, AINotesRepository, AIFeedbackRepository, AIAuditLogRepository
from app.database.models.tenant.ai_task import AITask  
from app.database.models.tenant.ai_notes import AINotes  
from app.api.schemas.event_schemas import VisitorEventData, AIGeneratedNoteStructure, AINoteFeedback, VisitorContextData
from app.api.schemas.feedback import SubmitFeedbackRequest
from app.config.settings import settings
import logging

# from gemini import gemini_api_key

logger = logging.getLogger(__name__)


class FollowupService:
    """
    Simplified service for generating AI-powered visitor follow-up notes
    using the new streamlined context builder.
    """
    
    def __init__(self):
        """Initialize the followup service"""
        self.context_builder = VisitorContextBuilder()
        self.sqs_client = NewVisitorSQSClient()
    
    async def generate_enhanced_summary_note(
        self, 
        event_data: VisitorEventData,
        visitor_context: VisitorContextData,
        receipt_handle:str = None
    ) -> Dict[str, Any]:
        """
        Generate enhanced AI summary note using visitor context.
        
        Args:
            event_data: Visitor event data from SQS
            visitor_context: Built visitor context from context builder
            
        Returns:
            Generated note with metadata and audit information
        """
        try:
            # Derive schema name from tenant
            schema_name = event_data.tenant
            
            # Initialize AI agent
            agent = FollowupNoteAgent(
                agent_id="enhanced_followup_agent",
                schema=schema_name
                # gemini_api_key=settings.GEMINI_API_KEY
            )
            
            # Generate comprehensive AI note
            ai_note_data = await agent.generate_comprehensive_note(visitor_context)
            ai_note = AIGeneratedNoteStructure(**ai_note_data)
            
            # Save note to member service with proper initialization
            member_service = MemberService(schema_name=schema_name)
            await member_service.initialize()  # Initialize connection pool
            
            try:
                note_data = self._prepare_member_service_note(ai_note, event_data)
                saved_note = await member_service.create_member_note(note_data)
            finally:
                await member_service.close()  # Ensure cleanup
            
            # Save to AI audit databases
            audit_result = await self._save_to_ai_audit_system(
                event_data, visitor_context, ai_note, saved_note, schema_name
            )

            #save to AI Notes table
            ai_note_result = await self._save_to_ai_notes_table(
                event_data, visitor_context, ai_note, saved_note, schema_name
            )


            #delete SQS message after  successful processing
            if receipt_handle:
                try:
                    self.sqs_client.delete_message(receipt_handle)
                    logger.info(f"Deleted SQS message with receipt handle: {receipt_handle}")
                except Exception as e:
                    logger.error(f"Failed to delete SQS message: {str(e)}")

            
            # Prepare response
            result = {
                'note_id': saved_note.get('id'),
                'ai_note': ai_note.model_dump(),
                'member_service_note': saved_note,
                'audit_records': audit_result,
                'ai_note_records': ai_note_result,
                'generation_metadata': {
                    'schema': schema_name,
                    'tenant': event_data.tenant,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'confidence_score': ai_note.confidence_score,
                    'data_sources': ai_note.data_sources_used,
                    'scenario': visitor_context.scenario_info.scenario_type  
                }
            }
            
            logger.info(f"Enhanced note generated for visitor {ai_note.email}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating enhanced summary note: {str(e)}")
            await self._log_generation_error(event_data, str(e))
            raise


    async def submit_feedback(
        self,
        note_id: str,
        feedback: AINoteFeedback,
        tenant: str
    ) -> dict:
        """
        Submit admin feedback on AI-generated notes for continuous improvement.
        """
        try:
            schema_name = tenant
            async with DatabaseConnection.get_session(schema_name) as session:
                repo = AIFeedbackRepository(session)
                feedback_record = repo.submit_feedback(
                    SubmitFeedbackRequest(
                        note_id=note_id,
                        visitor_id=feedback.person_id,
                        admin_id=feedback.reviewer_id,
                        tenant_id=tenant,
                        helpfulness=feedback.was_helpful,
                        comment=feedback.feedback_comments
                    )
                )
                await session.commit()
            return {
                'feedback_id': feedback_record.id,
                'status': 'submitted',
                'note_id': note_id
            }
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            raise

    async def get_note_with_feedback(self, note_id: str, tenant: str) -> Dict[str, Any]:
        """
        Retrieve AI-generated note with any associated feedback.
        
        Args:
            note_id: The ID of the note to retrieve
            tenant: Tenant identifier
            
        Returns:
            Note data with feedback history
        """
        try:
            schema_name = tenant
            
            async with DatabaseConnection.get_session(schema_name) as session:
                note_repo = AINotesRepository(AINotes, session)  # FIXED: Add model class parameter
                
                # Get note with feedback
                note_with_feedback = await note_repo.get_note_with_feedback(note_id)
                
                return note_with_feedback
                
        except Exception as e:
            logger.error(f"Error retrieving note with feedback: {str(e)}")
            raise
    
    def _prepare_member_service_note(
        self, 
        ai_note: AIGeneratedNoteStructure, 
        event_data: VisitorEventData
    ) -> Dict[str, Any]:
        """Prepare note data for member service storage with all required fields."""
        
        # Serialize AI note to dict with datetime handling
        ai_note_dict = self._serialize_ai_note_with_datetime_handling(ai_note)
        
        # Create comprehensive meta field with entire AI note + metadata
        comprehensive_meta = {
            'ai_generated_note': ai_note_dict,  # Entire AI note structure with serialized datetimes
            'generation_metadata': {
                'confidence_score': ai_note.confidence_score,
                'generation_timestamp': ai_note.generation_timestamp.isoformat() if ai_note.generation_timestamp else None,
                'data_sources': ai_note.data_sources_used,
                'tenant': event_data.tenant,
                'generation_source': 'vecapp_followup_agent',
                'model_version': 'gemini-2.5-flash',
                'prompt_version': '1.0'
            },
            'event_context': {
                'person_id': str(event_data.person_id),
                'fam_id': str(event_data.fam_id) if event_data.fam_id else None,
                'timestamp': event_data.timestamp.isoformat() if event_data.timestamp else None,
                'tenant': event_data.tenant
            },
            'processing_info': {
                'created_by_service': 'ai_service',
                'processing_mode': 'enhanced_followup',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Create structured notes_body (text field for human readability)
        notes_body_content = self._create_structured_notes_body(ai_note)
        
        # Prepare note data with all required database fields
        note_data = {
            # Required fields
            'title': f"Visitor Summary",  # As specified
            'task_id': self._get_or_create_task_id(event_data),  # Handle task requirement
            'person_id': event_data.person_id,
            'notes_body': notes_body_content,  # Text field with structured content
            'recipient_id': event_data.person_id,
            'recipient_fam_id': event_data.fam_id,  # Missing field added
            'type': 'ai_visitor_followup',  # Missing critical field added
            'meta': comprehensive_meta,  # JSONB with entire AI note + metadata
            
            # Optional fields with defaults
            'note_link': None,
            'note_photos': None,
            'file_attachment': None,
            'task_assignee_id': None,
            'is_edited': False,
            'is_archived': False
        }
        
        return note_data

    def _serialize_ai_note_with_datetime_handling(self, ai_note: AIGeneratedNoteStructure) -> Dict[str, Any]:
        """
        Serialize AI note to dictionary with proper datetime handling.
        Converts datetime objects to ISO format strings for JSON serialization.
        """
        ai_note_dict = ai_note.model_dump()
        
        # Handle datetime fields that need serialization
        if 'generation_timestamp' in ai_note_dict and ai_note_dict['generation_timestamp']:
            if isinstance(ai_note_dict['generation_timestamp'], datetime):
                ai_note_dict['generation_timestamp'] = ai_note_dict['generation_timestamp'].isoformat()
        
        return ai_note_dict
    
    def _create_structured_notes_body(self, ai_note: AIGeneratedNoteStructure) -> str:
        content_parts = [
            f"=== Visitor Summary ===",
            f"",
        ]
        
        if hasattr(ai_note, 'natural_summary') and ai_note.natural_summary:
            content_parts.extend([
                ai_note.natural_summary,
                f"",
            ])
        
        content_parts.extend([
            f"Visitor Name: {ai_note.visitor_full_name}",
            f"",
            f"Email: {ai_note.email}",
            f"",
            f"Phone Number: {ai_note.phone}",
            f"",
            f"Most Convinient Time to Contact Them: {getattr(ai_note, 'best_time_to_contact', ai_note.best_contact_time) if hasattr(ai_note, 'best_contact_time') else 'Afternoon'}",
            f"",
            f"Channel To Contact Them: {ai_note.channel_to_contact if ai_note.channel_to_contact else 'Email'}",
            f"",
            f"First Visit: {ai_note.first_visit}",
            f"",
            f"Primary Interest:",
            f"{', '.join(ai_note.key_interests) if ai_note.key_interests else 'None identified'}",
            f"",
            f"Special Request:",
            f"{ai_note.personal_needs_response.get('summary', 'None identified')}",
            f"",
            f"Family Context:",
            f"{ai_note.family_context}",
            f"",
            f"Sentiment:",
            f"Overall: {ai_note.sentiment_analysis.get('overall_sentiment', 'N/A')}",
            f"Confidence: {ai_note.sentiment_analysis.get('confidence', 0)*100:.0f}%",
            f"",
            f"Recommended Actions:",
        ])
        #TODO: Revisit when events are fully backup
        if hasattr(ai_note, 'recommended_next_steps') and ai_note.recommended_next_steps:
            for category, recommendations in ai_note.recommended_next_steps.items():
                if not recommendations:
                    continue
                content_parts.append(f"{category.replace('_', ' ').title()}:")

                rec_list = []
                if isinstance(recommendations, list):
                    rec_list = recommendations
                elif isinstance(recommendations, str):
                    # Only split if there are multiple lines, otherwise treat as single recommendation
                    if '\n' in recommendations:
                        rec_list = [line.strip() for line in recommendations.split('\n') if line.strip()]
                    else:
                        rec_list = [recommendations.strip()]
                else:
                    rec_list = [str(recommendations)]

                for rec in rec_list:
                    if rec is None:
                        continue
                    if isinstance(rec, dict):
                        rec_str = rec.get('title') or rec.get('description') or str(rec)
                    else:
                        rec_str = str(rec).strip()
                    if rec_str:
                        content_parts.append(f"  \u2022 {rec_str}")
                content_parts.append("")
        
        content_parts.extend([
            f"",
            f"=== Generation Metadata ===",
            f"Generated: {ai_note.generation_timestamp}",
            f"Confidence Score: {ai_note.confidence_score:.2f}",
            f"Data Sources: {', '.join(ai_note.data_sources_used)}",
            f"",
            f"[This note was automatically generated by AI and may require review]"
        ])
        
        return "\n".join(content_parts)
    
    def _get_or_create_task_id(self, event_data: VisitorEventData) -> int:
        """
        Handle task_id requirement for notes table.
        Since task_id is NOT NULL in the database but AI notes might not have tasks,
        we need to either create a default task or use a system task.
        """
        # Option 1: Use a default system task ID for AI-generated notes
        # This would require creating a system task during tenant setup
        #DEFAULT_AI_TASK_ID = 39  # System task for AI-generated notes
        
        # Option 2: Create a task on-demand (would require additional logic)
        # For now, using default approach
        
        return None #DEFAULT_AI_TASK_ID
    
    async def _save_to_ai_audit_system(
        self,
        event_data: VisitorEventData,
        visitor_context: VisitorContextData,
        ai_note: AIGeneratedNoteStructure,
        saved_note: Dict[str, Any],
        schema_name: str
    ) -> Dict[str, Any]:
        """Save generation audit data to the consolidated AI audit log table."""
        try:
            async with DatabaseConnection.get_session(schema_name) as session:
                audit_log_repo = AIAuditLogRepository(AIAuditLog, session)  # Assuming a repository for audit logs
    
                audit_entry = {
                    'user_id': event_data.person_id,
                    'user_email': event_data.email if hasattr(event_data, 'email') else None,
                    'tenant_id': event_data.tenant,
                    'action': 'generate_followup_note',
                    'resource_type': 'ai_note',
                    'resource_id': saved_note.get('id'),
                    'endpoint': 'visitor_event_listener',
                    'http_method': 'POST',
                    'ip_address': None,  # Add if available
                    'user_agent': None,  # Add if available
                    'details': {
                        'note': ai_note.model_dump(),
                        'confidence_score': ai_note.confidence_score,
                        'recommended_actions': [
                            action for actions in ai_note.recommended_next_steps.values() 
                            for action in actions
                        ],
                        'scenario': visitor_context.scenario_info.scenario_type
                    },
                    'success': 'true',
                    'error_message': None,
                    'duration_ms': None  # Add timing if available
                }
    
                await audit_log_repo.create_log(audit_entry)
                await session.commit()
    
                return {
                    'audit_status': 'completed',
                    'audit_log_id': audit_entry.get('id')
                }
    
        except Exception as e:
            logger.error(f"Error saving to AI audit system: {str(e)}")
            return {
                'audit_status': 'failed',
                'error': str(e)
            }
    
    async def _save_to_ai_notes_table(
        self,
        event_data: VisitorEventData,
        ai_note: AIGeneratedNoteStructure,
        saved_note: dict,
        schema_name: str
    ) -> dict:
        """Save AI generated note data to the ai_notes table."""
        try:
            async with DatabaseConnection.get_session(schema_name) as session:
                note_repo = AINotesRepository(AINotes, session)  # Assuming this repository exists
    
                note_data = {
                    'title': saved_note.get('title'),
                    'notes_body': ai_note.model_dump(),
                    'person_id': event_data.person_id,
                    'recipient_id': event_data.person_id,
                    'recipient_family_id': event_data.fam_id if hasattr(event_data, 'fam_id') else None,
                    'ai_model_used': 'gemini-2.5-flash',
                    'ai_generation_prompt': ai_note.generation_prompt if hasattr(ai_note, 'generation_prompt') else None,
                    'ai_review_status': 'pending',
                    'ai_generated': True,
                    'meta': {
                        'confidence_score': ai_note.confidence_score,
                        'recommended_actions': [
                            action for actions in ai_note.recommended_next_steps.values() 
                            for action in actions
                        ],
                        'scenario': getattr(ai_note, 'scenario', None)
                    }
                }
    
                ai_note_record = await note_repo.create_note(
                    task_id=None,  # If task_id is relevant, pass it here
                    tenant=event_data.tenant,
                    note_data=note_data,
                    ai_metadata=None  # Adjust if metadata is needed
                )
    
                await session.commit()
    
                return {
                    'ai_note_id': ai_note_record.id,
                    'status': 'saved'
                }
    
        except Exception as e:
            logger.error(f"Error saving to ai_notes table: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _log_generation_error(
        self, 
        event_data: VisitorEventData, 
        error_message: str
    ) -> None:
        """Log generation errors for monitoring and debugging."""
        try:
            schema_name = event_data.tenant
            async with DatabaseConnection.get_session(schema_name) as session:
                # Log error to AI audit system
                error_data = {
                    'tenant': event_data.tenant,
                    'person_id': event_data.person_id,
                    'error_message': error_message,
                    'error_timestamp': datetime.now(timezone.utc).isoformat(),
                    'error_type': 'note_generation_failure'
                }
                
                # Save error log (implement based on your error logging schema)
                logger.error(f"Note generation failed: {error_data}")
                
        except Exception as e:
            logger.error(f"Failed to log generation error: {str(e)}")