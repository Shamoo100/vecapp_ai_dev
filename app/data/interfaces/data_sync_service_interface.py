"""
Interface for Data Sync Service operations.

This interface defines the contract for orchestrating hybrid data syncing
between provisioning-time sync and on-demand data pulling.
"""

from typing import Dict, Any, Optional, List, Protocol
from uuid import UUID
from datetime import datetime
from enum import Enum


class SyncStatus(Enum):
    """Enumeration for sync operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncType(Enum):
    """Enumeration for sync operation types."""
    PROVISIONING = "provisioning"
    ON_DEMAND = "on_demand"
    INCREMENTAL = "incremental"
    FULL_REFRESH = "full_refresh"


class IDataSyncService(Protocol):
    """
    Interface for data synchronization service operations.
    
    This service orchestrates the hybrid data syncing approach, managing
    both provisioning-time sync and on-demand data pulling across all
    external services (Auth, Member, Calendar, Connect).
    """
    
    async def initialize(self) -> None:
        """Initialize the data sync service."""
        ...
    
    async def close(self) -> None:
        """Close the data sync service."""
        ...
    
    # ========================================
    # PROVISIONING-TIME SYNC ORCHESTRATION
    # ========================================
    
    async def sync_tenant_provisioning_data(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Orchestrate complete provisioning-time data sync for a new tenant.
        
        This includes:
        - Auth service: User authentication, roles, permissions
        - Member service: Person, family, user types, user status, tasks, notes
        
        Args:
            tenant_id: The tenant's unique identifier
            
        Returns:
            Sync operation summary with status and metrics
        """
        ...
    
    async def sync_auth_provisioning_data(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Sync auth service data during tenant provisioning.
        
        Args:
            tenant_id: The tenant's unique identifier
            
        Returns:
            Auth sync operation summary
        """
        ...
    
    async def sync_member_provisioning_data(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Sync member service data during tenant provisioning.
        
        Args:
            tenant_id: The tenant's unique identifier
            
        Returns:
            Member sync operation summary
        """
        ...
    
    # ========================================
    # ON-DEMAND DATA PULLING ORCHESTRATION
    # ========================================
    
    async def pull_calendar_data(self, tenant_id: UUID, **kwargs) -> Dict[str, Any]:
        """
        Pull calendar data on-demand.
        
        Args:
            tenant_id: The tenant's unique identifier
            **kwargs: Additional parameters for calendar data pulling
            
        Returns:
            Calendar data and operation summary
        """
        ...
    
    async def pull_connect_data(self, tenant_id: UUID, **kwargs) -> Dict[str, Any]:
        """
        Pull connect service data on-demand.
        
        Args:
            tenant_id: The tenant's unique identifier
            **kwargs: Additional parameters for connect data pulling
            
        Returns:
            Connect data and operation summary
        """
        ...
    
    async def pull_member_updates(self, tenant_id: UUID, since: datetime = None) -> Dict[str, Any]:
        """
        Pull updated member service data on-demand.
        
        Args:
            tenant_id: The tenant's unique identifier
            since: Optional timestamp to pull updates since
            
        Returns:
            Updated member data and operation summary
        """
        ...
    
    # ========================================
    # SYNC STATUS AND MONITORING
    # ========================================
    
    async def get_sync_status(self, tenant_id: UUID, sync_type: SyncType = None) -> Dict[str, Any]:
        """
        Get sync status for a tenant.
        
        Args:
            tenant_id: The tenant's unique identifier
            sync_type: Optional filter by sync type
            
        Returns:
            Sync status information
        """
        ...
    
    async def get_sync_history(self, tenant_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get sync operation history for a tenant.
        
        Args:
            tenant_id: The tenant's unique identifier
            limit: Maximum number of history records to return
            
        Returns:
            List of sync operation history records
        """
        ...
    
    async def retry_failed_sync(self, tenant_id: UUID, sync_operation_id: UUID) -> Dict[str, Any]:
        """
        Retry a failed sync operation.
        
        Args:
            tenant_id: The tenant's unique identifier
            sync_operation_id: The failed sync operation identifier
            
        Returns:
            Retry operation summary
        """
        ...
    
    # ========================================
    # INCREMENTAL AND REFRESH OPERATIONS
    # ========================================
    
    async def incremental_sync(self, tenant_id: UUID, service_name: str) -> Dict[str, Any]:
        """
        Perform incremental sync for a specific service.
        
        Args:
            tenant_id: The tenant's unique identifier
            service_name: Name of the service to sync (auth, member, calendar, connect)
            
        Returns:
            Incremental sync operation summary
        """
        ...
    
    async def full_refresh_sync(self, tenant_id: UUID, service_name: str) -> Dict[str, Any]:
        """
        Perform full refresh sync for a specific service.
        
        Args:
            tenant_id: The tenant's unique identifier
            service_name: Name of the service to refresh
            
        Returns:
            Full refresh operation summary
        """
        ...
    
    async def schedule_sync_operation(
        self, 
        tenant_id: UUID, 
        sync_type: SyncType, 
        service_name: str,
        scheduled_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Schedule a sync operation for later execution.
        
        Args:
            tenant_id: The tenant's unique identifier
            sync_type: Type of sync operation
            service_name: Name of the service to sync
            scheduled_time: Optional scheduled execution time
            
        Returns:
            Scheduled operation summary
        """
        ...