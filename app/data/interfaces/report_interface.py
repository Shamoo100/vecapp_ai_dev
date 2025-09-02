"""
Report Repository Interface
Defines the contract for report data access operations.
"""
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime
from uuid import UUID

from app.api.schemas.report import ReportStatus
from app.data.interfaces.repository import IRepository


class IReportRepository(IRepository, Protocol):
    """Interface for report repository operations"""
    
    async def create_report(
        self,
        id: UUID,
        tenant_id: UUID,
        report_type: str,
        date_range_start: datetime,
        date_range_end: datetime,
        requested_by_user_id: UUID,
        status: ReportStatus = ReportStatus.PENDING
    ) -> Dict[str, Any]:
        """Create a new report record"""
        ...
    
    async def update_report(
        self,
        report_id: UUID,
        tenant_id: UUID,
        status: Optional[ReportStatus] = None,
        pdf_storage_key: Optional[str] = None,
        report_summary_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing report record"""
        ...
    
    async def list_reports(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[ReportStatus] = None
    ) -> List[Dict[str, Any]]:
        """List reports with optional filtering"""
        ...
    
    async def get_report(self, report_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a report by ID"""
        ...