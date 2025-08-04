"""
AI Service Repository Implementation
Concrete implementation for AI task and notes data operations.
"""
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
import logging

from app.database.models.tenant.ai_task import AITask
from app.database.models.tenant.ai_notes import AINotes
from app.database.models.tenant.ai_person import AIPerson
from app.database.models.tenant.ai_audit_log import AIAuditLog
from app.database.repositories.base_repository import BaseRepository
from app.database.models.tenant.feedback import AIFeedback,FeedbackHelpfulness
from app.api.schemas.feedback import SubmitFeedbackRequest


logger = logging.getLogger(__name__)


class AITaskRepository(BaseRepository[AITask]):
    """Repository for AI task data operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AITask, session)
    
    async def create_ai_task(
        self, 
        tenant_id: int,
        task_data: Dict[str, Any],
        ai_result: Dict[str, Any]
    ) -> AITask:
        """Create a new AI task with associated AI processing results"""
        try:
            ai_task = AITask(
                task_title=task_data.get('task_title'),
                task_description=task_data.get('task_description'),
                task_type=task_data.get('task_type'),
                task_status=task_data.get('task_status'),
                task_priority=task_data.get('task_priority'),
                task_type_flag=task_data.get('task_type_flag'),
                created_by=task_data.get('created_by'),
                recipient_person_id=task_data.get('recipient_person_id'),
                recipient_id=task_data.get('recipient_id'),
                recipient_family_id=task_data.get('recipient_family_id'),
                task_assignee_id=task_data.get('task_assignee_id'),
                follow_up_user=task_data.get('follow_up_user'),
                assign_usertype=task_data.get('assign_usertype'),
                routed_to=task_data.get('routed_to'),
                follow_up_prev_task=task_data.get('follow_up_prev_task'),
                ai_agent_type=ai_result.get('ai_agent_type'),
                ai_processing_status=ai_result.get('ai_processing_status', 'completed'),
                ai_confidence_score=ai_result.get('confidence_score'),
                ai_model_version=ai_result.get('model_version', 'gpt-4')
            )
            return await self.create(ai_task)
        except Exception as e:
            logger.error(f"Error creating AI task: {str(e)}")
            raise
    
    async def get_by_id(
        self, 
        task_id: int, 
        tenant_id: int
    ) -> Optional[AITask]:
        """Get AI task by ID within tenant context"""
        try:
            stmt = select(AITask).where(
                AITask.id == task_id,
                AITask.tenant_id == tenant_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting AI task by ID {task_id}: {str(e)}")
            raise
    
    async def update_processing_status(
        self, 
        task_id: int, 
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Update AI task processing status with timestamps"""
        try:
            update_data = {
                "ai_processing_status": status,
                "updated_at": datetime.utcnow()
            }
            if status == 'processing':
                update_data["processing_started_at"] = datetime.utcnow()
            elif status == 'completed':
                update_data["processing_completed_at"] = datetime.utcnow()
            elif status == 'failed' and error_message:
                update_data["error_message"] = error_message
            
            stmt = update(AITask).where(
                AITask.id == task_id
            ).values(**update_data)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {str(e)}")
            await self.session.rollback()
            raise


class AINotesRepository(BaseRepository[AINotes]):
    """Repository for AI-generated notes data operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AINotes, session)
    
    async def create_note(
        self,
        task_id: int,
        tenant_id: int,
        note_data: Dict[str, Any],
        ai_metadata: Dict[str, Any]
    ) -> AINotes:
        """Create a new AI-generated note linked to a task"""
        try:
            note = AINotes(
                title=note_data.get('title'),
                notes_body=note_data.get('notes_body'),
                person_id=note_data.get('person_id'),
                task_id=task_id,
                task_assignee_id=note_data.get('task_assignee_id'),
                recipient_id=note_data.get('recipient_id'),
                recipient_family_id=note_data.get('recipient_family_id'),
                note_link=note_data.get('note_link'),
                meta=note_data.get('meta'),
                ai_generated=True,
                ai_model_used=ai_metadata.get('ai_model_used'),
                ai_generation_prompt=ai_metadata.get('ai_generation_prompt'),
                ai_review_status='pending',
                ai_confidence_score=ai_metadata.get('confidence_score')
            )
            return await self.create(note)
        except Exception as e:
            logger.error(f"Error creating AI note: {str(e)}")
            raise
    
    async def get_notes_by_task(
        self, 
        task_id: int, 
        tenant_id: int
    ) -> List[AINotes]:
        """Get all notes associated with a specific task"""
        try:
            stmt = select(AINotes).where(
                AINotes.task_id == task_id,
                AINotes.tenant_id == tenant_id
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting notes for task {task_id}: {str(e)}")
            raise
    
    async def update_review_status(
        self, 
        note_id: int, 
        review_status: str,
        reviewer_id: Optional[int] = None
    ) -> bool:
        """Update the review status of an AI-generated note"""
        try:
            update_data = {
                "ai_review_status": review_status,
                "updated_at": datetime.utcnow()
            }
            if reviewer_id:
                update_data["reviewed_by"] = reviewer_id
                update_data["reviewed_at"] = datetime.utcnow()
            
            stmt = update(AINotes).where(
                AINotes.id == note_id
            ).values(**update_data)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating note review status {note_id}: {str(e)}")
            await self.session.rollback()
            raise


class AIFeedbackRepository(BaseRepository[AIFeedback]):
    """Repository for managing AI note feedback operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def submit_feedback(self, feedback_request: SubmitFeedbackRequest) -> Optional[AIFeedback]:
        """
        Submit feedback for an AI-generated note
        
        Args:
            feedback_request: The feedback submission request
            
        Returns:
            AINoteFeedback: The created feedback record, or None if failed
        """
        try:
            # First, verify the note exists and is AI-generated
            note = self.db.query(AINotes).filter(
                AINotes.id == feedback_request.note_id,
                AINotes.is_ai_generated == True
            ).first()
            
            if not note:
                logger.warning(f"Note {feedback_request.note_id} not found or not AI-generated")
                return None
            
            # Check if feedback already exists from this admin for this note
            existing_feedback = self.db.query(AIFeedback).filter(
                AIFeedback.note_id == feedback_request.note_id,
                AIFeedback.admin_id == feedback_request.admin_id
            ).first()
            
            if existing_feedback:
                logger.warning(f"Feedback already exists from admin {feedback_request.admin_id} for note {feedback_request.note_id}")
                return None
            
            # Create new feedback record
            feedback = AIFeedback(
                note_id=feedback_request.note_id,
                visitor_id=feedback_request.visitor_id,
                admin_id=feedback_request.admin_id,
                tenant_id=feedback_request.tenant_id,
                helpfulness=FeedbackHelpfulness(feedback_request.helpfulness.value),
                comment=feedback_request.comment,
                ai_model_version=note.ai_model_version,
                ai_confidence_score=note.ai_confidence_score
            )
            
            self.db.add(feedback)
            
            # Mark the note as having received feedback
            note.feedback_received = True
            
            self.db.commit()
            self.db.refresh(feedback)
            
            logger.info(f"Feedback submitted successfully for note {feedback_request.note_id} by admin {feedback_request.admin_id}")
            return feedback
            
        except SQLAlchemyError as e:
            logger.error(f"Database error submitting feedback: {str(e)}")
            self.db.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error submitting feedback: {str(e)}")
            self.db.rollback()
            return None
    
    def get_feedback_for_note(self, note_id: int, tenant_id: int) -> List[AIFeedback]:
        """
        Get all feedback for a specific note
        
        Args:
            note_id: The ID of the note
            tenant_id: The tenant ID for security
            
        Returns:
            List[AINoteFeedback]: List of feedback records
        """
        try:
            feedback_list = self.db.query(AIFeedback).filter(
                AIFeedback.note_id == note_id,
                AIFeedback.tenant_id == tenant_id
            ).order_by(AIFeedback.created_at.desc()).all()
            
            return feedback_list
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving feedback for note {note_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving feedback for note {note_id}: {str(e)}")
            return []
    
    def get_feedback_by_admin(self, admin_id: UUID, tenant_id: int, limit: int = 50) -> List[AIFeedback]:
        """
        Get feedback submitted by a specific admin
        
        Args:
            admin_id: The admin's ID
            tenant_id: The tenant ID for security
            limit: Maximum number of records to return
            
        Returns:
            List[AINoteFeedback]: List of feedback records
        """
        try:
            feedback_list = self.db.query(AIFeedback).filter(
                AIFeedback.admin_id == admin_id,
                AIFeedback.tenant_id == tenant_id
            ).order_by(AIFeedback.created_at.desc()).limit(limit).all()
            
            return feedback_list
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving feedback by admin {admin_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving feedback by admin {admin_id}: {str(e)}")
            return []
    
    def get_feedback_stats(self, tenant_id: int, days: int = 30) -> dict:
        """
        Get feedback statistics for analytics
        
        Args:
            tenant_id: The tenant ID
            days: Number of days to look back
            
        Returns:
            dict: Statistics about feedback
        """
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get total feedback count
            total_feedback = self.db.query(func.count(AIFeedback.id)).filter(
                AIFeedback.tenant_id == tenant_id,
                AIFeedback.created_at >= cutoff_date
            ).scalar() or 0
            
            # Get feedback by helpfulness
            helpfulness_stats = self.db.query(
                AIFeedback.helpfulness,
                func.count(AIFeedback.id)
            ).filter(
                AIFeedback.tenant_id == tenant_id,
                AIFeedback.created_at >= cutoff_date
            ).group_by(AIFeedback.helpfulness).all()
            
            # Get notes with feedback vs total AI notes
            notes_with_feedback = self.db.query(func.count(func.distinct(AINotes.id))).filter(
                AINotes.tenant_id == tenant_id,
                AINotes.created_at >= cutoff_date
            ).scalar() or 0
            
            total_ai_notes = self.db.query(func.count(AINotes.id)).filter(
                AINotes.is_ai_generated == True,
                AINotes.created_at >= cutoff_date
            ).scalar() or 0
            
            return {
                "total_feedback": total_feedback,
                "helpfulness_breakdown": {str(h): count for h, count in helpfulness_stats},
                "notes_with_feedback": notes_with_feedback,
                "total_ai_notes": total_ai_notes,
                "feedback_rate": round((notes_with_feedback / total_ai_notes * 100), 2) if total_ai_notes > 0 else 0,
                "period_days": days
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving feedback stats: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error retrieving feedback stats: {str(e)}")
            return {}
    
    def check_note_exists(self, note_id: int, tenant_id: int) -> bool:
        """
        Check if a note exists and is AI-generated
        
        Args:
            note_id: The note ID
            tenant_id: The tenant ID for security
            
        Returns:
            bool: True if note exists and is AI-generated
        """
        try:
            note = self.db.query(AINotes).filter(
                AINotes.id == note_id,
                AINotes.is_ai_generated == True
            ).first()
            
            return note is not None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking note existence: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking note existence: {str(e)}")
            return False


class AIAuditLogRepository(BaseRepository[AIAuditLog]):
    """Repository for managing AI service audit logs"""

    def __init__(self, session: Session):
        super().__init__(AIAuditLog, session)

    def log_user_access(
        self,
        user_id: str,
        user_email: str,
        tenant_id: str,
        endpoint: str,
        http_method: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> AIAuditLog:
        """Log user access to AI service API."""
        try:
            audit_log = AIAuditLog(
                user_id=user_id,
                user_email=user_email,
                tenant_id=tenant_id,
                action="user_access",
                resource_type="api",
                resource_id=None,
                endpoint=endpoint,
                http_method=http_method,
                ip_address=ip_address,
                user_agent=user_agent,
                success="true",
                timestamp=datetime.utcnow()
            )
            self.session.add(audit_log)
            self.session.commit()
            self.session.refresh(audit_log)
            return audit_log
        except Exception as e:
            logger.error(f"Error logging user access: {str(e)}")
            self.session.rollback()
            return None

    def create_audit_log(
        self,
        user_id: str,
        user_email: str,
        tenant_id: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        endpoint: str = None,
        http_method: str = None,
        ip_address: str = None,
        user_agent: str = None,
        success: str = "true",
        error_message: str = None,
        details: dict = None,
        duration_ms: str = None
    ) -> AIAuditLog:
        """Create a general audit log entry."""
        try:
            audit_log = AIAuditLog(
                user_id=user_id,
                user_email=user_email,
                tenant_id=tenant_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                endpoint=endpoint,
                http_method=http_method,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message,
                details=details,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            self.session.add(audit_log)
            self.session.commit()
            self.session.refresh(audit_log)
            return audit_log
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            self.session.rollback()
            return None