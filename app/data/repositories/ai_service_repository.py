from __future__ import annotations
from typing import Any, Dict, List, Optional
from uuid import UUID
import logging
import json
from datetime import datetime, timezone

from app.database.repositories.connection import DatabaseConnection
from app.data.models.ai_service_models import (
    AuditLogEntry,
    DecisionAuditEntry,
    TaskNoteInput,
    TaskNoteResult,
    FeedbackInput,
    RecommendationLogInput,
    RecommendationLogResult,
    SuppressionLogInput,
    SuppressionLogResult
)

logger = logging.getLogger(__name__)

class AIServiceRepository:
    """Direct SQL implementation of AI service repository."""
    
    def __init__(self, tenant: str):
        self.tenant = tenant
    
    def _ensure_timezone_aware(self, dt: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    def _serialize_json_field(self, data: Any) -> Optional[str]:
        """Safely serialize data to JSON string."""
        if data is None:
            return None
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return data
    
    async def create_audit_log(self, audit: AuditLogEntry) -> Dict[str, Any]:
        """Create audit log entry using direct SQL."""
        query = """
        INSERT INTO ai_audit_log (
            user_id, user_email, tenant_id, action, resource_type, resource_id,
            endpoint, http_method, ip_address, user_agent, details, success,
            error_message, timestamp, duration_ms, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
        RETURNING id, created_at
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            # Serialize details if it's a dict
            details = self._serialize_json_field(audit.details)
            
            now = datetime.now(timezone.utc)
            # Ensure audit timestamp is timezone-aware
            audit_timestamp = self._ensure_timezone_aware(audit.timestamp)
            
            result = await conn.fetchrow(
                query,
                audit.user_id,
                audit.user_email,
                audit.tenant_id,
                audit.action,
                audit.resource_type,
                audit.resource_id,
                audit.endpoint,
                audit.http_method,
                audit.ip_address,
                audit.user_agent,
                details,
                audit.success,
                audit.error_message,
                audit_timestamp,  # Now timezone-aware
                audit.duration_ms,
                now,  # created_at
                now   # updated_at
            )
            
            return {
                'id': result['id'],
                'created_at': result['created_at']
            }
    
    async def save_decision_audit(self, decision: DecisionAuditEntry) -> Dict[str, Any]:
        """Save decision audit using direct SQL."""
        query = """
        INSERT INTO ai_decision_audit (
            person_id, rule_id, rule_description, input_data, output_data, triggered
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, created_at
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            result = await conn.fetchrow(
                query,
                decision.person_id,
                decision.rule_id,
                decision.rule_description,
                decision.input_data,
                decision.output_data,
                decision.triggered
            )
            
            return {
                'id': result['id'],
                'created_at': result['created_at'],
                'status': 'created'
            }
    
    async def save_ai_note_to_ai_task(self, task_note: TaskNoteInput) -> TaskNoteResult:
        """Save AI note to task using direct SQL with transaction."""
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            async with conn.transaction():
                # Check for existing task
                task_query = """
                SELECT id FROM ai_task 
                WHERE recipient_person_id = $1 AND recipient_id = $2 
                AND recipient_family_id = $3 AND task_type = $4
                """
                
                task_result = await conn.fetchrow(
                    task_query,
                    task_note.person_id,
                    task_note.recipient_id,
                    task_note.recipient_family_id,
                    task_note.type
                )
                
                if task_result:
                    task_id = task_result['id']
                else:
                    # Create new task
                    create_task_query = """
                    INSERT INTO ai_task (
                        recipient_person_id, recipient_id, recipient_family_id,
                        task_type, task_title, task_description, task_status,
                        task_priority, ai_agent_type
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """
                    
                    new_task = await conn.fetchrow(
                        create_task_query,
                        task_note.person_id,
                        task_note.recipient_id,
                        task_note.recipient_family_id,
                        task_note.type,
                        task_note.task_title,
                        task_note.task_description,
                        task_note.task_status,
                        task_note.task_priority,
                        task_note.ai_agent_type
                    )
                    task_id = new_task['id']
                
                # Create note with required fields
                note_query = """
                INSERT INTO ai_notes (
                    task_id, person_id, title, notes_body, recipient_id,
                    recipient_family_id, meta, is_edited, is_archived, is_deleted
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """
                
                # Serialize meta field
                meta_serialized = self._serialize_json_field(task_note.note_meta or {})
                
                note_result = await conn.fetchrow(
                    note_query,
                    task_id,
                    task_note.person_id,
                    task_note.note_title,
                    task_note.note_body,
                    task_note.recipient_id,
                    task_note.recipient_family_id,
                    meta_serialized,
                    False,  # is_edited
                    False,  # is_archived
                    False   # is_deleted
                )
                
                return TaskNoteResult(
                    task_id=task_id,
                    note_id=note_result['id']
                )
    
    async def submit_feedback_to_ai_feedback(self, feedback: FeedbackInput) -> Dict[str, Any]:
        """Submit feedback using direct SQL."""
        logger.info(f"Using schema: {self.tenant}") 
        query = """
        INSERT INTO ai_feedback (
            entity_type, person_id, note_id, task_id, helpfulness,
            user_comment, admin_id, ai_model_version, ai_confidence_score
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id, created_at
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            result = await conn.fetchrow(
                query,
                feedback.entity_type,
                feedback.person_id,
                feedback.note_id,
                feedback.task_id,
                feedback.helpfulness,
                feedback.user_comment,
                feedback.admin_id,
                feedback.ai_model_version,
                feedback.ai_confidence_score
            )
            
            return {
                'id': result['id'],
                'created_at': result['created_at'],
                'status': 'submitted'
            }
    
    async def create_recommendation_logs(self, payload: RecommendationLogInput) -> RecommendationLogResult:
        """Create recommendation logs using direct SQL batch insert."""
        if not payload.items:
            return RecommendationLogResult(ids=[], count=0)
        
        query = """
        INSERT INTO ai_recommendation_log (
            id, person_id, note_id, task_id, scenario_type, source, model_version,
            text, section, priority, confidence, tags, suggested_by,
            suppressed, suppress_reason, module_name, meta, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
        RETURNING id
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            async with conn.transaction():
                ids = []
                meta_serialized = self._serialize_json_field(payload.meta)
                now = datetime.now(timezone.utc)
                
                for item in payload.items:
                    # Generate explicit UUID for each recommendation
                    from uuid import uuid4
                    rec_id = uuid4()
                    
                    # Serialize tags properly
                    tags_serialized = item.tags if isinstance(item.tags, list) else None
                    
                    # Set module_name based on source
                    module_name = payload.source or "followup_note_agent"
                    
                    result = await conn.fetchrow(
                        query,
                        rec_id,  # Explicit UUID
                        payload.person_id,
                        payload.note_id,
                        payload.task_id,
                        payload.scenario_type,
                        payload.source,
                        payload.model_version,
                        item.text,
                        item.section,
                        item.priority,
                        item.confidence,
                        tags_serialized,
                        item.suggested_by,
                        item.suppressed,
                        item.suppress_reason,
                        module_name,  # Add module_name field
                        meta_serialized,
                        now,  # created_at
                        now   # updated_at
                    )
                    # Convert UUID to string for consistency
                    ids.append(str(result['id']))
                
                return RecommendationLogResult(
                    ids=ids,
                    count=len(ids)
                )
    
    async def get_notes_by_task(self, task_id: int) -> List[Dict[str, Any]]:
        """Get notes by task using direct SQL."""
        query = """
        SELECT id, task_id, person_id, title, notes_body, recipient_id,
               recipient_family_id, meta, created_at, updated_at
        FROM ai_notes WHERE task_id = $1
        ORDER BY created_at DESC
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            results = await conn.fetch(query, task_id)
            return [dict(row) for row in results]
    
    async def get_feedback_for_note(self, note_id: int) -> List[Dict[str, Any]]:
        """Get feedback for note using direct SQL."""
        query = """
        SELECT id, entity_type, person_id, note_id, task_id, helpfulness,
               user_comment, admin_id, ai_model_version, ai_confidence_score,
               created_at, updated_at
        FROM ai_feedback WHERE note_id = $1
        ORDER BY created_at DESC
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            results = await conn.fetch(query, note_id)
            return [dict(row) for row in results]
    
    async def create_note(
        self,
        task_id: Optional[int] = None,
        tenant: Optional[str] = None,
        note_data: Optional[Dict[str, Any]] = None,
        ai_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create AI note using direct SQL."""
        query = """
        INSERT INTO ai_notes (
            title, notes_body, person_id, recipient_id, recipient_family_id,
            ai_model_used, ai_generation_prompt, ai_review_status, ai_generated, 
            meta, is_edited, is_archived, is_deleted
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING id, created_at
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            # Serialize complex objects to JSON strings
            notes_body = self._serialize_json_field(note_data.get('notes_body'))
            meta = self._serialize_json_field(note_data.get('meta'))
            
            result = await conn.fetchrow(
                query,
                note_data.get('title'),
                notes_body,  # Now properly serialized
                note_data.get('person_id'),
                note_data.get('recipient_id'),
                note_data.get('recipient_family_id'),
                note_data.get('ai_model_used'),
                note_data.get('ai_generation_prompt'),
                note_data.get('ai_review_status', 'pending'),
                note_data.get('ai_generated', True),
                meta,  # Now properly serialized
                note_data.get('is_edited', False),  # Added required field
                note_data.get('is_archived', False),  # Added required field
                note_data.get('is_deleted', False)   # Added required field
            )
            
            return {
                'id': result['id'],
                'created_at': result['created_at']
            }
    
    async def create_suppression_log(self, suppression: SuppressionLogInput) -> SuppressionLogResult:
        """Create suppression log entry using direct SQL."""
        query = """
        INSERT INTO ai_suppression_log (
            id, person_id, suppressed_entity_type, suppressed_entity_id,
            reason, suppression_type, module_name, suppressed_by_user_id,
            auto_suppression_rule, meta, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id
        """
        
        async with DatabaseConnection.get_connection(self.tenant) as conn:
            from uuid import uuid4
            
            suppression_id = uuid4()
            now = datetime.now(timezone.utc)
            
            # Serialize meta field
            meta_serialized = self._serialize_json_field(suppression.meta)
            
            result = await conn.fetchrow(
                query,
                suppression_id,
                suppression.person_id,
                suppression.suppressed_entity_type,
                suppression.suppressed_entity_id,
                suppression.reason,
                suppression.suppression_type,
                suppression.module_name,
                suppression.suppressed_by_user_id,
                suppression.auto_suppression_rule,
                meta_serialized,
                now,  # created_at
                now   # updated_at
            )
            
            return SuppressionLogResult(
                id=result['id'],
                status='saved'
            )