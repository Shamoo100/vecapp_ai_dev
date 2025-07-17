from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from uuid import UUID
import logging

from app.database.models.tenant.ai_notes import AINotes
from app.database.models.tenant.feedback import AIFeedback,FeedbackHelpfulness
from app.api.schemas.feedback import SubmitFeedbackRequest

logger = logging.getLogger(__name__)

class FeedbackRepository:
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