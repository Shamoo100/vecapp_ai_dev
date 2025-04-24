from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import asyncpg
from app.config.settings import get_settings
from app.models.report import ReportStatus

settings = get_settings()

class ReportRepository:
    """Repository for report data operations"""
    
    async def _get_connection(self, tenant_id: UUID = None):
        """Get a database connection with tenant schema set if provided"""
        conn = await asyncpg.connect(settings.DATABASE_URL)
        if tenant_id:
            await conn.execute(f"SET search_path TO tenant_{tenant_id}, public")
        return conn
    
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
        conn = await self._get_connection(tenant_id)
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO generated_reports (
                    id, tenant_id, report_type, status,
                    date_range_start, date_range_end,
                    requested_by_user_id, requested_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
                """,
                id, tenant_id, report_type, status.value,
                date_range_start, date_range_end,
                requested_by_user_id, datetime.utcnow()
            )
            return dict(row)
        finally:
            await conn.close()
    
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
        conn = await self._get_connection(tenant_id)
        try:
            # Build update query dynamically based on provided fields
            update_parts = []
            params = [report_id, tenant_id]
            param_idx = 3
            
            if status is not None:
                update_parts.append(f"status = ${param_idx}")
                params.append(status.value)
                param_idx += 1
                
                # Update timestamps based on status
                if status == ReportStatus.PROCESSING:
                    update_parts.append(f"generation_started_at = ${param_idx}")
                    params.append(datetime.utcnow())
                    param_idx += 1
                elif status in [ReportStatus.COMPLETED, ReportStatus.FAILED]:
                    update_parts.append(f"generation_completed_at = ${param_idx}")
                    params.append(datetime.utcnow())
                    param_idx += 1
            
            if pdf_storage_key is not None:
                update_parts.append(f"pdf_storage_key = ${param_idx}")
                params.append(pdf_storage_key)
                param_idx += 1
            
            if report_summary_data is not None:
                update_parts.append(f"report_summary_data = ${param_idx}")
                params.append(json.dumps(report_summary_data))
                param_idx += 1
            
            if error_message is not None:
                update_parts.append(f"error_message = ${param_idx}")
                params.append(error_message)
                param_idx += 1
            
            # Always update updated_at
            update_parts.append(f"updated_at = ${param_idx}")
            params.append(datetime.utcnow())
            
            # Execute update query
            if update_parts:
                query = f"""
                UPDATE generated_reports
                SET {", ".join(update_parts)}
                WHERE id = $1 AND tenant_id = $2
                RETURNING *
                """
                row = await conn.fetchrow(query, *params)
                return dict(row)
            return None
        finally:
            await conn.close()
    
    async def get_report(self, report_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a report by ID"""
        conn = await self._get_connection(tenant_id)
        try:
            row = await conn.fetchrow(
                """
                SELECT * FROM generated_reports
                WHERE id = $1 AND tenant_id = $2
                """,
                report_id, tenant_id
            )
            if row:
                return dict(row)
            return None
        finally:
            await conn.close()
    
    async def list_reports(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[ReportStatus] = None
    ) -> List[Dict[str, Any]]:
        """List reports with optional filtering"""
        conn = await self._get_connection(tenant_id)
        try:
            # Build query with optional filters
            query = "SELECT * FROM generated_reports WHERE tenant_id = $1"
            params = [tenant_id]
            param_idx = 2
            
            if start_date:
                query += f" AND requested_at >= ${param_idx}"
                params.append(start_date)
                param_idx += 1
            
            if end_date:
                query += f" AND requested_at <= ${param_idx}"
                params.append(end_date)
                param_idx += 1
            
            if status:
                query += f" AND status = ${param_idx}"
                params.append(status.value)
                param_idx += 1
            
            query += " ORDER BY requested_at DESC"
            
            # Execute query
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
        finally:
            await conn.close() 