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
from app.services.member_service import MemberService
from app.database.repositories.connection import DatabaseConnection
from app.data.repositories.ai_service_repository import AIServiceRepository
from app.database.models.tenant.ai_notes import AINotes
from app.api.schemas.event_schemas import VisitorEventData, AIGeneratedNoteStructure, VisitorContextData
from app.api.schemas.feedback import SubmitFeedbackRequest, FeedbackHelpfulness, FeedbackResponse
from app.data.models.ai_service_models import (
    AuditLogEntry,
    DecisionAuditEntry,
    TaskNoteInput,
    RecommendationItem,
    RecommendationLogInput,
    FeedbackInput,
    SuppressionLogInput,
)

from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class FollowupService:
    """
    Simplified service for generating AI-powered visitor follow-up notes
    using the new streamlined context builder.
    """
    
    def __init__(self, schema_name: Optional[str] = None):
        """Initialize the followup service with explicit schema name for tenant isolation"""
        self.schema_name = schema_name
    
    async def generate_followup_summary_note(
        self, 
        event_data: VisitorEventData,
        visitor_context: VisitorContextData,
        receipt_handle: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate followup AI summary note using visitor context.
        
        Args:
            event_data: Visitor event data from SQS
            visitor_context: Built visitor context from context builder
            receipt_handle: Optional SQS receipt handle
            
        Returns:
            Generated note with metadata and audit information
        """
        try:
            logger.info(f"Starting followup note generation for visitor {event_data.person_id}")
            
            # Use schema_name from constructor or derive from event_data
            schema_name = self.schema_name or event_data.tenant
            
            # Validate schema consistency
            if self.schema_name and self.schema_name != event_data.tenant:
                logger.warning(f"Schema mismatch: service initialized with {self.schema_name}, event has {event_data.tenant}")
            
            logger.info(f"Using schema: {schema_name} for tenant: {event_data.tenant}")
            
            # Initialize AI agent
            agent = FollowupNoteAgent(
                agent_id="followup_note_agent",
                schema=schema_name
            )
            
            # Generate comprehensive AI note
            logger.info(f"Generating AI note for visitor {event_data.person_id}")
            ai_note_data = await agent.generate_comprehensive_note(visitor_context)
            ai_note = AIGeneratedNoteStructure(**ai_note_data)
            
            # Save note to member service with proper initialization
            member_service = MemberService(schema_name=schema_name)
            await member_service.initialize()
            
            try:
                logger.info(f"Saving note to member service for visitor {event_data.person_id}")
                note_data = self._prepare_member_service_note(ai_note, event_data)
                saved_note = await member_service.create_note(note_data)
            finally:
                await member_service.close()

            if saved_note is None:
                logger.error(f"Failed to save note to member service for visitor {event_data.person_id}")
                raise RuntimeError(f"Failed to save note to member service for visitor {event_data.person_id}")
            
            logger.info(f"Successfully saved note to member service: note_id={saved_note.get('id')}")
            
            # Save to AI audit databases
            logger.info(f"Saving audit log for visitor {event_data.person_id}")
            audit_result = await self._save_to_ai_audit_system(
                event_data, visitor_context, ai_note, saved_note, schema_name
            )

            if audit_result is None or audit_result.get('status') == 'failed':
                logger.error(f"Failed to save audit log to AI audit system for visitor {event_data.person_id}")
                # Don't raise error, continue with other saves

            # Save to AI Notes table
            logger.info(f"Saving AI note record for visitor {event_data.person_id}")
            ai_note_result = await self._save_to_ai_notes_table(
                event_data, visitor_context, ai_note, saved_note, schema_name
            )

            if ai_note_result is None or ai_note_result.get('status') == 'failed':
                logger.error(f"Failed to save note to AI notes table for visitor {event_data.person_id}")
                # Don't raise error, continue with other saves

            # Save recommendation log
            logger.info(f"Saving recommendations for visitor {event_data.person_id}")
            recommendation_result = await self._save_recommendations(
                ai_note.recommended_next_steps,
                event_data.person_id,
                saved_note.get('id'),
                ai_note_result.get('ai_note_id') if ai_note_result else None,
                schema_name
            )
            
            # Save suppression log if applicable
            logger.info(f"Checking for suppression events for visitor {event_data.person_id}")
            suppression_result = await self._save_suppression_log(
                event_data,
                ai_note,
                saved_note.get('id'),
                schema_name
            )
            
            # Prepare response
            result = {
                'note_id': saved_note.get('id'),
                'ai_note': ai_note.model_dump(),
                'member_service_note': saved_note,
                'audit_records': audit_result,
                'ai_note_records': ai_note_result,
                'recommendation_records': recommendation_result,
                'suppression_records': suppression_result,
                'generation_metadata': {
                    'schema': schema_name,
                    'tenant': event_data.tenant,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'confidence_score': ai_note.confidence_score,
                    'data_sources': ai_note.data_sources_used,
                    'scenario': visitor_context.scenario_info.scenario_type  
                }
            }
            
            logger.info(f"Followup note generation completed successfully for visitor {ai_note.email}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating followup note for visitor {event_data.person_id}: {str(e)}")
            await self._log_generation_error(event_data, str(e))
            raise
    
    #submit feedback to ai feedback table
    async def submit_feedback(
        self,
        note_id: str,
        feedback: SubmitFeedbackRequest,
        tenant: str
    ) -> dict:
        """
        Submit admin feedback on AI-generated notes for continuous improvement.
        """
        try:
            logger.info(f"Submitting feedback for note {note_id} in tenant {tenant}")
            
            # Initialize repository with tenant
            repo = AIServiceRepository(tenant)
            
            # Create FeedbackInput with proper field mapping
            feedback_input = FeedbackInput(
                entity_type="note",
                person_id=feedback.visitor_id,
                note_id=int(note_id),
                task_id=int(feedback.task_id) if feedback.task_id else None,
                helpfulness=feedback.helpfulness.value,
                user_comment=feedback.comment,
                admin_id=feedback.admin_id,
                ai_model_version="gemini-2.5-flash",
                ai_confidence_score=None
            )
            
            # Submit feedback using correct method name
            result = await repo.submit_feedback_to_ai_feedback(feedback_input)
            
            logger.info(f"Successfully submitted feedback for note {note_id}")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid feedback data for note {note_id}: {str(e)}")
            raise ValueError(f"Invalid feedback data: {str(e)}")
        except Exception as e:
            logger.error(f"Error submitting feedback for note {note_id}: {str(e)}")
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
            logger.info(f"Retrieving note {note_id} with feedback for tenant {tenant}")
            schema_name = tenant
            
            async with DatabaseConnection.get_session(schema_name) as session:
                note_repo = AIServiceRepository(AINotes, session)
                
                # Get note with feedback
                note_with_feedback = await note_repo.get_feedback_for_note(note_id)
                
                logger.info(f"Successfully retrieved note {note_id} with feedback")
                return note_with_feedback
                
        except Exception as e:
            logger.error(f"Error retrieving note {note_id} with feedback: {str(e)}")
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
            'ai_generated_note': ai_note_dict,
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
                'processing_mode': 'followup_note_agent',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Create structured notes_body (text field for human readability)
        notes_body_content = self._create_structured_notes_body(ai_note)
        
        # Prepare note data with all required database fields
        note_data = {
            # Required fields
            'title': f"Visitor Summary",
            'task_id': self._get_or_create_task_id(event_data),
            'person_id': event_data.person_id,
            'notes_body': notes_body_content,
            'recipient_id': event_data.person_id,
            'recipient_fam_id': event_data.fam_id,
            'type': 'ai_visitor_followup',
            'meta': comprehensive_meta,
            
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
        """Serialize AI note with comprehensive datetime handling."""
        import json
        from datetime import datetime
        
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                # Ensure timezone-aware datetime
                if obj.tzinfo is None:
                    obj = obj.replace(tzinfo=timezone.utc)
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Convert to dict first
        ai_note_dict = ai_note.model_dump()
        
        # Handle generation_timestamp specifically
        if 'generation_timestamp' in ai_note_dict:
            timestamp = ai_note_dict['generation_timestamp']
            if isinstance(timestamp, datetime):
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                ai_note_dict['generation_timestamp'] = timestamp.isoformat()
        
        # Serialize and deserialize to ensure all datetime objects are converted
        json_str = json.dumps(ai_note_dict, default=datetime_handler)
        return json.loads(json_str)
    
    def _create_structured_notes_body(self, ai_note: AIGeneratedNoteStructure) -> str:
        """Create structured text content for the notes_body field."""
        content_parts = [
            f"=== Visitor Summary ===",
            f" ",
        ]
        
        if hasattr(ai_note, 'natural_summary') and ai_note.natural_summary:
            content_parts.extend([
                ai_note.natural_summary,
                f"",
            ])
        
        content_parts.extend([
            f"Visitor Name: {ai_note.visitor_full_name}",
            f" ",
            f"Email: {ai_note.email}",
            f" ",
            f"Phone Number: {ai_note.phone}",
            f" ",
            f"Most Convenient Time to Contact Them: {getattr(ai_note, 'best_time_to_contact', ai_note.best_contact_time) if hasattr(ai_note, 'best_contact_time') else 'Afternoon'}",
            f" ",
            f"Channel To Contact Them: {ai_note.channel_to_contact if ai_note.channel_to_contact else 'Email'}",
            f" ",
            f"First Visit: {ai_note.first_visit}",
            f" ",
            f"Primary Interest:",
            f"{', '.join(ai_note.key_interests) if ai_note.key_interests else 'None identified'}",
            f" ",
            f"Special Request:",
            f"{ai_note.personal_needs_response.get('summary', 'None identified')}",
            f" ",
            f"Family Context:",
            f"{ai_note.family_context}",
            f" ",
            f"Sentiment:",
            f"Overall: {ai_note.sentiment_analysis.get('overall_sentiment', 'N/A')}",
            f"Confidence: {ai_note.sentiment_analysis.get('confidence', 0)*100:.0f}%",
            f" ",
            f"Recommended Actions:",
        ])
        
        if hasattr(ai_note, 'recommended_next_steps') and ai_note.recommended_next_steps:
            for category, recommendations in ai_note.recommended_next_steps.items():
                if not recommendations:
                    continue
                content_parts.append(f"{category.replace('_', ' ').title()}:")

                rec_list = []
                if isinstance(recommendations, list):
                    rec_list = recommendations
                elif isinstance(recommendations, str):
                    if ',' in recommendations:
                        rec_list = [item.strip() for item in str(recommendations).split(',') if item.strip()]
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
        return None
    
    async def _save_to_ai_audit_system(
        self,
        event_data: VisitorEventData,
        visitor_context: VisitorContextData,
        ai_note: AIGeneratedNoteStructure,
        saved_note: Dict[str, Any],
        schema_name: str
    ) -> Dict[str, Any]:
        """Save audit information to AI audit system."""
        try:
            logger.info(f"Saving audit log for person {event_data.person_id}")
            audit_repo = AIServiceRepository(schema_name)
            
            # Serialize the note data properly with datetime handling
            note_data = self._serialize_ai_note_with_datetime_handling(ai_note)
            
            # Generate a proper UUID for system user
            import uuid
            system_user_id = str(uuid.uuid4())
            
            audit_entry = AuditLogEntry(
                user_id=system_user_id,
                user_email="system@vecapp.ai",
                tenant_id=schema_name,
                action="ai_note_generation",
                resource_type="ai_note",
                resource_id=str(saved_note.get('id', 'unknown')),
                endpoint="/ai/generate_note",
                http_method="POST",
                ip_address="127.0.0.1",
                user_agent="VecApp-AI-Agent",
                details=note_data,
                success="true",
                error_message=None,
                timestamp=datetime.now(timezone.utc),
                duration_ms="0"
            )
            
            result = await audit_repo.create_audit_log(audit_entry)
            
            logger.info(f"Successfully saved audit log for person {event_data.person_id}, audit_id: {result['id']}")
            return {
                'audit_id': result['id'],
                'status': 'saved'
            }
            
        except Exception as e:
            logger.error(f"Error saving to AI audit system for person {event_data.person_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    #save to recommendation log
    async def _save_recommendations(
        self,
        recommendations: Dict[str, Any],
        person_id: UUID,
        note_id: Optional[int],
        ai_note_id: Optional[int],
        schema_name: str
    ) -> Dict[str, Any]:
        """Save AI-generated recommendations to the recommendation log."""
        try:
            logger.info(f"Starting recommendation save for person {person_id}, note {note_id}")
            
            if not recommendations:
                logger.info(f"No recommendations to save for person {person_id}")
                return {'status': 'skipped', 'reason': 'no_recommendations'}
            
            repo = AIServiceRepository(schema_name)
            
            # Convert recommendations to RecommendationItem list
            items = []
            for section, recs in recommendations.items():
                if isinstance(recs, list):
                    for rec in recs:
                        if rec:  # Skip empty recommendations
                            items.append(RecommendationItem(
                                text=str(rec),
                                section=section,
                                priority='normal',
                                confidence=0.8,
                                suggested_by='ai'
                            ))
            
            if not items:
                logger.warning(f"No valid recommendations found for person {person_id}")
                return {'status': 'skipped', 'reason': 'no_valid_recommendations'}
            
            payload = RecommendationLogInput(
                person_id=person_id,
                note_id=note_id,
                task_id=None,
                scenario_type='followup_note',
                ai_model_version='gemini-2.5-flash',
                confidence_score=0.8,
                recommendations=items,
                generated_at=datetime.now(timezone.utc),
                module_name='followup_service'  # Add module_name
            )
            
            result = await repo.create_recommendation_logs(payload)
            
            logger.info(f"Successfully saved {len(items)} recommendations for person {person_id}")
            return {
                'recommendation_ids': result.ids,
                'items_saved': len(items),
                'status': 'saved'
            }
            
        except Exception as e:
            logger.error(f"Error saving recommendations for person {person_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _save_suppression_log(
        self,
        event_data: VisitorEventData,
        ai_note: AIGeneratedNoteStructure,
        note_id: Optional[int],
        schema_name: str
    ) -> Dict[str, Any]:
        """Save suppression log entries for AI-generated content."""
        try:
            logger.info(f"Checking suppression events for person {event_data.person_id}")
            
            # Check if any content was suppressed or filtered
            suppression_events = []
            
            # Check for low confidence scores (potential suppression)
            if ai_note.confidence_score < 0.5:
                suppression_events.append({
                    'reason': 'low_confidence',
                    'details': f'Confidence score {ai_note.confidence_score} below threshold 0.5',
                    'content_type': 'ai_note'
                })
            
            # Check for missing or filtered content
            if not ai_note.key_interests or len(ai_note.key_interests) == 0:
                suppression_events.append({
                    'reason': 'no_interests_identified',
                    'details': 'No key interests could be identified from visitor data',
                    'content_type': 'interests'
                })
            
            # Check for empty recommendations
            if not ai_note.recommended_next_steps or all(not recs for recs in ai_note.recommended_next_steps.values()):
                suppression_events.append({
                    'reason': 'no_recommendations_generated',
                    'details': 'No actionable recommendations could be generated',
                    'content_type': 'recommendations'
                })
            
            if not suppression_events:
                logger.info(f"No suppression events found for person {event_data.person_id}")
                return {'status': 'skipped', 'reason': 'no_suppression_events'}
            
            repo = AIServiceRepository(schema_name)
            saved_suppressions = []
            
            for event in suppression_events:
                suppression_input = SuppressionLogInput(
                    person_id=event_data.person_id,
                    note_id=note_id,
                    task_id=None,
                    suppression_reason=event['reason'],
                    content_type=event['content_type'],
                    original_content=event['details'],
                    suppressed_content=None,
                    ai_model_version='gemini-2.5-flash',
                    confidence_threshold=0.5,
                    suppressed_at=datetime.now(timezone.utc),
                    # Add missing required fields:
                    suppressed_entity_type=event.get('content_type', 'note'),  # Required field
                    suppressed_entity_id=note_id,  # Required field
                    meta=ai_note.raw_content,  # Required field
                    reason=event['reason']  # Required field (different from suppression_reason)
                )
                
                result = await repo.create_suppression_log(suppression_input)
                saved_suppressions.append(result)
            
            logger.info(f"Successfully saved {len(saved_suppressions)} suppression events for person {event_data.person_id}")
            return {
                'suppression_events': len(saved_suppressions),
                'status': 'saved',
                'events': saved_suppressions
            }
            
        except Exception as e:
            logger.error(f"Error saving suppression log for person {event_data.person_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _save_to_ai_notes_table(
        self,
        event_data: VisitorEventData,
        visitor_context: VisitorContextData,
        ai_note: AIGeneratedNoteStructure,
        saved_note: dict,
        schema_name: str
    ) -> dict:
        """Save AI note to the ai_notes table."""
        try:
            note_repo = AIServiceRepository(schema_name)
            
            # Serialize the AI note properly with datetime handling
            ai_note_dict = self._serialize_ai_note_with_datetime_handling(ai_note)
            
            # # Validate family_id exists before using it
            # recipient_family_id = None
            # if hasattr(event_data, 'fam_id') and event_data.fam_id:
            #     # Check if family exists in ai_fam table
            #     family_exists = await self._check_family_exists(event_data.fam_id, schema_name)
            #     if family_exists:
            #         recipient_family_id = event_data.fam_id
            #     else:
            #         # Create family record if it doesn't exist
            #         recipient_family_id = await self._create_family_record(event_data, schema_name)
            
            note_data = {
                'title': saved_note.get('title'),
                'notes_body': ai_note_dict,
                'person_id': event_data.person_id,
                'recipient_id': event_data.person_id,
                'recipient_family_id': event_data.fam_id, 
                'ai_model_used': 'gemini-2.5-flash',
                'ai_generation_prompt': getattr(ai_note, 'generation_prompt', None),
                'ai_review_status': 'pending',
                'ai_generated': True,
                'scenario_type': 'visitor_followup',
                'generation_source': 'followup_note_agent',
                'quality_score': getattr(ai_note, 'confidence_score', 0.8),
                'meta': {
                    'confidence_score': ai_note.confidence_score,
                    'recommended_actions': [
                        action for actions in ai_note.recommended_next_steps.values() 
                        for action in actions
                    ],
                    'scenario': getattr(ai_note, 'scenario', None),
                    'generation_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Use the repository method to save
            ai_note_record = await note_repo.create_note(
                note_data=note_data,
                ai_metadata=note_data['meta']
            )
            
            return {
                'ai_note_id': ai_note_record['id'],
                'status': 'saved'
            }
            
        except ValueError as e:
            logger.error(f"Invalid note data: {str(e)}")
            await self._log_generation_error(event_data, f"Note saved with ID: {ai_note_record['id']}")
        except Exception as e:
            logger.error(f"Error saving to ai_notes table: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    # # check if family exist
    # async def _check_family_exists(self, fam_id: Optional[UUID], schema_name: str) -> bool:
    #     """Check if family exists in the database."""
    #     if not fam_id:
    #         return False
        
    #     try:
    #         # Implementation to check family existence
    #         # This would typically query the member service
    #         return True  # Placeholder
    #     except Exception as e:
    #         logger.warning(f"Error checking family existence for {fam_id}: {e}")
    #         return False
    
    # # create family record
    # async def _create_family_record(self, event_data: VisitorEventData, schema_name: str) -> UUID:
    #     """Create a new family record in the database."""
    #     try:
    #         # Implementation to create family record
    #         # This would typically insert into the member service
    #         return event_data.fam_id  # Placeholder
    #     except Exception as e:
    #         logger.error(f"Error creating family record for {event_data.fam_id}: {e}")
    #         raise
    
    async def _log_generation_error(
        self,
        event_data: VisitorEventData,
        error_message: str
    ) -> None:
        """Log generation errors for monitoring and debugging."""
        try:
            logger.error(f"AI note generation failed for person {event_data.person_id}: {error_message}")
            
            # Could also save to error tracking system here
            # For now, just log the error
            
        except Exception as e:
            logger.error(f"Error logging generation error: {str(e)}")