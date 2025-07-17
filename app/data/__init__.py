"""Data access layer for the application."""

from app.data.interfaces.visitor_repository import VisitorRepository
from app.data.interfaces.report_repository import ReportRepository
from app.data.interfaces.feedback_repository import FeedbackRepository
from app.data.interfaces.ai_task_repository import AITaskRepository

__all__ = [
    'VisitorRepository',
    'ReportRepository',
    'FeedbackRepository',
    'AITaskRepository',
]
