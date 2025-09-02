from __future__ import annotations
from typing import Dict, Any, Optional, List, Protocol
from uuid import UUID
from app.data.models.ai_service_models import (
    AuditLogEntry,
    DecisionAuditEntry,
    TaskNoteInput,
    TaskNoteResult,
    FeedbackInput,
    RecommendationLogInput,
    RecommendationLogResult,
)

class IAIServiceRepository(Protocol):
    """Simplified AI service repository interface using direct SQL."""
    
    # Core audit logging
    async def create_audit_log(self, audit: AuditLogEntry) -> Dict[str, Any]:
        """Create audit log entry - returns dict instead of ORM object."""
        ...
    
    # Decision audit
    async def save_decision_audit(self, decision: DecisionAuditEntry) -> Dict[str, Any]:
        """Save decision audit - returns dict instead of ORM object."""
        ...
    
    # Task and note operations
    async def save_ai_note_to_ai_task(self, task_note: TaskNoteInput) -> TaskNoteResult:
        """Save AI note to task - returns Pydantic model."""
        ...
    
    # Feedback operations
    async def submit_feedback_to_ai_feedback(self, feedback: FeedbackInput) -> Dict[str, Any]:
        """Submit feedback - returns dict instead of ORM object."""
        ...
    
    # Recommendation logs
    async def create_recommendation_logs(self, payload: RecommendationLogInput) -> RecommendationLogResult:
        """Create recommendation logs - returns Pydantic result."""
        ...
    
    # Query operations
    async def get_notes_by_task(self, task_id: int) -> List[Dict[str, Any]]:
        """Get notes by task - returns list of dicts."""
        ...
    
    async def get_feedback_for_note(self, note_id: int) -> List[Dict[str, Any]]:
        """Get feedback for note - returns list of dicts."""
        ...


    #Service Interface Protocol for AI
class IAIService(Protocol):
    """
    Interface for AI service operations including audit logging, notes, tasks, and feedback.
    
    This service handles AI-related data operations within the tenant schema,
    following the same pattern as other service interfaces in the codebase.
    """
    
    async def initialize(self) -> None:
        """Initialize the service and database connections."""
        ...
    
    async def close(self) -> None:
        """Close the service and database connections."""
        ...
    
    # ===== AI Audit Logging =====
    
    async def save_ai_note_to_audit_log(self, audit_log_data: Dict[str, Any]) -> AIAuditLog:
        """Save AI note generation to audit log."""
        ...
    
    async def log_ai_note_generation(
        self, 
        user_id: UUID, 
        user_email: str, 
        tenant_id: str, 
        note_id: str, 
        ai_note_data: Dict[str, Any], 
        confidence_score: float, 
        scenario_type: str, 
        endpoint: str = "visitor_event_listener", 
        success: bool = True, 
        error_message: Optional[str] = None, 
        duration_ms: Optional[str] = None
    ) -> AIAuditLog:
        """Log AI note generation process to audit log."""
        ...
    
    async def log_feedback_submission(
        self, 
        user_id: UUID, 
        user_email: str, 
        tenant_id: str, 
        note_id: str, 
        feedback_data: Dict[str, Any], 
        endpoint: str, 
        success: bool = True, 
        error_message: Optional[str] = None
    ) -> AIAuditLog:
        """Log feedback submission to audit log."""
        ...
    
    # ===== Recommendation Log =====
    async def create_recommendation_logs(
        self, payload: RecommendationLogInput
    ) -> RecommendationLogResult:
        """
        Orchestrates logging recommendations (fan-out items to rows).
        Returns ids + count (thin wrapper around repository).
        """
        ...
    
    # ===== Suppression Log =====
    async def create_suppression_log(
        self, suppression: SuppressionLogInput
    ) -> SuppressionLogResult:
        """
        Create suppression log entry for tracking AI service performance and decision suppression events.
        """
        ...

    # ===== AI Notes and Tasks =====
    
    async def save_ai_note_to_ai_task(self, task_data: Dict[str, Any]) -> AITask:
        """Save AI note to AI task table."""
        ...
    
    async def create_ai_note(
        self, 
        title: str, 
        notes_body: str, 
        person_id: UUID, 
        recipient_id: UUID, 
        recipient_family_id: Optional[UUID] = None, 
        task_id: Optional[int] = None, 
        ai_model_used: str = "gemini-2.5-flash", 
        ai_generation_prompt: Optional[str] = None, 
        ai_confidence_score: Optional[str] = None, 
        meta: Optional[Dict[str, Any]] = None
    ) -> AINotes:
        """Create an AI-generated note."""
        ...
    
    async def get_note_by_id(self, note_id: int) -> Optional[AINotes]:
        """Get AI note by ID."""
        ...
    
    async def get_task_by_id(self, task_id: int) -> Optional[AITask]:
        """Get AI task by ID."""
        ...
    
    # ===== Feedback Management =====
    
    async def submit_feedback_to_ai_feedback(self, feedback_data: Dict[str, Any]) -> AIFeedback:
        """Submit feedback to AI feedback table."""
        ...
    
    async def submit_note_feedback(
        self, 
        note_id: int, 
        person_id: UUID, 
        admin_id: UUID, 
        helpfulness: str, 
        user_comment: Optional[str] = None, 
        ai_model_version: Optional[str] = None, 
        ai_confidence_score: Optional[float] = None
    ) -> AIFeedback:
        """Submit feedback for an AI-generated note."""
        ...
    
    async def get_feedback_for_note(self, note_id: int) -> List[AIFeedback]:
        """Get all feedback for a specific note."""
        ...
    
    async def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback statistics for analytics."""
        ...
    
    async def check_note_exists(self, note_id: int) -> bool:
        """Check if a note exists and is AI-generated."""
        ...
