from typing import Optional, Dict, Any, Type, TypeVar
from contextlib import asynccontextmanager
from uuid import UUID
from app.database.connection_manager import ConnectionManager
from app.data.report_repository import ReportRepository
# Import other repositories as needed

T = TypeVar('T')

class UnitOfWork:
    """Manages a business transaction and provides access to repositories
    
    This class implements the Unit of Work pattern to ensure that multiple
    database operations can be performed within a single transaction.
    """
    
    def __init__(self, tenant_id: Optional[UUID] = None):
        self.tenant_id = tenant_id
        self._repositories: Dict[str, Any] = {}
    
    def __getattr__(self, name: str) -> Any:
        """Dynamically access repositories by name"""
        if name.endswith('_repository'):
            if name not in self._repositories:
                # Create repository instances on demand
                if name == 'report_repository':
                    self._repositories[name] = ReportRepository()
                # Add other repositories as needed
                
            return self._repositories[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
    
    @asynccontextmanager
    async def transaction(self):
        """Execute operations within a database transaction"""
        async with ConnectionManager.get_connection(self.tenant_id) as conn:
            async with conn.transaction():
                # Set the connection on all repositories
                for repo in self._repositories.values():
                    repo._conn = conn
                
                try:
                    yield self
                finally:
                    # Clear the connection from repositories
                    for repo in self._repositories.values():
                        repo._conn = None