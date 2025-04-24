from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import FileResponse, JSONResponse
import logging
import tempfile
import os

from core.auth import get_current_user, User
from app.database.tenant_management import get_tenant_by_id
from core.report_management import ReportManagement
from agents.base_agent import BaseAgent
from utils.pdf_generator import PDFGenerator
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from app.models.report import ReportCreate, ReportResponse, ReportStatus
from app.security.tenant import get_current_tenant
from app.orchestration.report_generator import ReportGenerator
from app.data.report_repository import ReportRepository

router = APIRouter(prefix="/api/followup-summary_report", tags=["followup-summary-report"])
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_current_tenant),
):
    """Generate a new follow-up summary report"""
    # Create a new report record
    report_id = uuid4()
    report_repository = ReportRepository()
    
    try:
        # Create report record
        await report_repository.create_report(
            id=report_id,
            tenant_id=tenant["id"],
            report_type=report_data.report_type,
            date_range_start=report_data.date_range_start,
            date_range_end=report_data.date_range_end,
            requested_by_user_id=current_user["id"],
            status=ReportStatus.PENDING
        )
        
        # Start background processing
        report_generator = ReportGenerator()
        background_tasks.add_task(
            report_generator.generate_report,
            report_id=report_id,
            tenant_id=tenant["id"],
            start_date=report_data.date_range_start,
            end_date=report_data.date_range_end,
            report_type=report_data.report_type
        )
        
        return {
            "id": report_id,
            "status": ReportStatus.PENDING,
            "message": "Report generation started"
        }
    except Exception as e:
        # Log the error and return appropriate response
        print(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID = Path(..., description="The ID of the report to retrieve"),
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_current_tenant),
):
    """Get the status or result of a report"""
    try:
        report_repository = ReportRepository()
        report = await report_repository.get_report(report_id, tenant["id"])
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "id": report["id"],
            "status": report["status"],
            "created_at": report["created_at"],
            "updated_at": report["updated_at"],
            "report_url": report.get("pdf_storage_key"),
            "report_data": report.get("report_summary_data")
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return appropriate response
        print(f"Error retrieving report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")

@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID = Path(..., description="The ID of the report to download"),
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_current_tenant),
):
    """Download a report as PDF"""
    try:
        report_repository = ReportRepository()
        report = await report_repository.get_report(report_id, tenant["id"])
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
            
        if report["status"] != ReportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Report is not ready for download")
            
        # Get the PDF file from S3
        from app.data.storage import S3Storage
        s3_storage = S3Storage()
        pdf_data = await s3_storage.get_file(report["pdf_storage_key"])
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_data)
            temp_path = temp_file.name
            
        return FileResponse(
            path=temp_path,
            filename=f"followup_summary_{report_id}.pdf",
            media_type="application/pdf",
            background=lambda: os.unlink(temp_path)  # Delete after sending
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return appropriate response
        print(f"Error downloading report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")

@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    start_date: Optional[datetime] = Query(None, description="Filter reports created after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter reports created before this date"),
    status: Optional[ReportStatus] = Query(None, description="Filter reports by status"),
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_current_tenant),
):
    """List all reports for the current tenant"""
    try:
        report_repository = ReportRepository()
        reports = await report_repository.list_reports(
            tenant_id=tenant["id"],
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        return reports
    except Exception as e:
        # Log the error and return appropriate response
        print(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")

@router.delete("/reports/{report_id}")
async def delete_followup_report(
    report_id: str = Path(..., description="The ID of the report to delete"),
    tenant_id: str = Query(..., description="The ID of the tenant the report belongs to"),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific follow-up summary report by ID.
    """
    # Validate tenant access
    tenant = await get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check user permissions
    if not current_user.has_permission("delete_reports", tenant_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete reports for this tenant")
    
    # Delete the report
    try:
        success = await ReportManagement.delete_report(report_id, tenant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found or could not be deleted")
        
        return {
            "status": "success",
            "message": "Report deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting follow-up report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting report: {str(e)}") 