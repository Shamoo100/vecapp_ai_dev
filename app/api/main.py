from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from core.auth import get_current_tenant, verify_api_key
from core.database import Database
from models.tenant import Tenant
from models.visitor import Visitor
from app.api.followup_summary_report import router as report_router

router = APIRouter()
# CORS middleware

# Include routers
router.include_router(report_router)

@router.post("/api/v1/visitors")
async def create_visitor(
    visitor_data: Dict[str, Any],
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key)
):
    """Create new visitor and trigger MAS workflow"""
    try:
        # Initialize Data Collection Agent
        dca = DataCollectionAgent(
            agent_id=f"dca-{tenant.id}",
            tenant_id=tenant.id,
            database=Database()
        )
        
        # Process visitor data
        result = await dca.process(visitor_data)
        
        return {
            "status": "success",
            "visitor_id": result['visitor_id'],
            "message": "Visitor processing initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/visitors/{visitor_id}")
async def get_visitor(
    visitor_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key)
):
    """Get visitor details and engagement status"""
    try:
        db = Database()
        visitor = await db.get_visitor(visitor_id, tenant.id)
        if not visitor:
            raise HTTPException(status_code=404, detail="Visitor not found")
        return visitor
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/volunteers/assignments")
async def create_volunteer_assignment(
    assignment_data: Dict[str, Any],
    tenant: Tenant = Depends(get_current_tenant),
    api_key: str = Depends(verify_api_key)
):
    """Create volunteer assignment"""
    try:
        vca = VolunteerCoordinationAgent(
            agent_id=f"vca-{tenant.id}",
            tenant_id=tenant.id,
            message_queue=MessageQueue(),
            notification_service=NotificationService()
        )
        
        result = await vca.process(assignment_data)
        return {
            "status": "success",
            "assignment_id": result['assignment_id']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 