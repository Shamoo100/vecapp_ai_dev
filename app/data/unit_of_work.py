from typing import Optional, Dict, Any, Type, TypeVar
from contextlib import asynccontextmanager
from uuid import UUID
from app.database.repositories.connection import DatabaseConnection

# Import from the new repositories location
from app.data.repositories.report_repository import ReportRepository
from app.data.repositories.ai_service_repository import AITaskRepository, AINotesRepository
from app.data.repositories.visitor_repository import VisitorRepository
from app.data.repositories.feedback_repository import FeedbackRepository
from app.data.repositories.member_service_repository import MemberRepository
from app.data.repositories.ai_auth_repository import AiAuthRepository
from app.data.repositories.external_auth_repository import ExternalAuthRepository

T = TypeVar('T')


class UnitOfWork:
    """Manages a business transaction and provides access to repositories
    
    This class implements the Unit of Work pattern to ensure that multiple
    database operations can be performed within a single transaction.
    """
    
    def __init__(self, tenant_id: Optional[UUID] = None, schema_name: Optional[str] = None):
        self.tenant_id = tenant_id
        self.schema_name = schema_name or f"tenant_{tenant_id}" if tenant_id else None
        self._repositories: Dict[str, Any] = {}
    
    def __getattr__(self, name: str) -> Any:
        """Dynamically access repositories by name"""
        if name.endswith('_repository'):
            if name not in self._repositories:
                # Create repository instances on demand
                if name == 'report_repository':
                    self._repositories[name] = ReportRepository()
                elif name == 'ai_task_repository':
                    self._repositories[name] = AITaskRepository()
                elif name == 'ai_notes_repository':
                    self._repositories[name] = AINotesRepository()
                elif name == 'visitor_repository':
                    self._repositories[name] = VisitorRepository()
                elif name == 'feedback_repository':
                    self._repositories[name] = FeedbackRepository()
                elif name == 'member_repository':
                    self._repositories[name] = MemberRepository(self.schema_name)
                elif name == 'auth_repository':
                    self._repositories[name] = AiAuthRepository()
                elif name == 'external_auth_repository':
                    self._repositories[name] = ExternalAuthRepository(self.schema_name)
                # Add other repositories as needed
                
            return self._repositories[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
    
    @asynccontextmanager
    async def transaction(self):
        """Execute operations within a database transaction"""
        async with DatabaseConnection.get_connection(self.tenant_id) as conn:
            async with conn.transaction():
                # Set the connection on all repositories
                for repo in self._repositories.values():
                    if hasattr(repo, '_conn'):
                        repo._conn = conn
                
                try:
                    yield self
                finally:
                    # Clear the connection from repositories
                    for repo in self._repositories.values():
                        if hasattr(repo, '_conn'):
                            repo._conn = None