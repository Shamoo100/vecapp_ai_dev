from fastapi import FastAPI, Depends, HTTPException, APIRouter
#from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from datetime import datetime, timedelta
#from app.core.api_key_auth import get_current_tenant, verify_api_key
#from app.core.database import Database
from app.services.analytics_service import AnalyticsService
from app.database.models.tenant import Tenant
from app.database.models.visitor import Visitor
from app.agents.data_collection_agent import DataCollectionAgent
from app.agents.volunteer_coordination_agent import VolunteerCoordinationAgent
from app.core.messaging import MessageQueue
from app.core.notifications import NotificationService
from app.api.routes import (
    auth_routes,
    visitor,
    volunteer,
    analytics,
    followup,
    followup_notes,
    followup_summary_report,
    tenants,
    batch_tenants
)

# Initialize main API router
router = APIRouter(prefix="/api/v1")

# Include all route modules
router.include_router(visitor.router)
router.include_router(volunteer.router)
router.include_router(analytics.router)
router.include_router(followup.router)
router.include_router(followup_notes.router)
router.include_router(followup_summary_report.router)
router.include_router(auth_routes.router)
router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
router.include_router(batch_tenants.router, prefix="/batch-tenants", tags=["batch-tenants"])

# Volunteer Management Endpoints
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

# Analytics Endpoints
@router.get("/api/v1/analytics/dashboard")
async def get_dashboard_metrics(
    tenant: Tenant = Depends(get_current_tenant),
    period: str = "30d"
):
    """Get main dashboard metrics"""
    try:
        analytics = AnalyticsService(tenant.id)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - _parse_period(period)
        
        metrics = await analytics.get_dashboard_metrics(start_date, end_date)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/analytics/visitor-trends")
async def get_visitor_trends(
    start_date: datetime,
    end_date: datetime,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get visitor engagement trends"""
    try:
        analytics = AnalyticsService(tenant.id)
        trends = await analytics.get_visitor_trends(start_date, end_date)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/analytics/volunteer-performance")
async def get_volunteer_performance(
    tenant: Tenant = Depends(get_current_tenant),
    period: str = "30d"
):
    """Get volunteer performance metrics"""
    try:
        analytics = AnalyticsService(tenant.id)
        end_date = datetime.utcnow()
        start_date = end_date - _parse_period(period)
        
        performance = await analytics.get_volunteer_performance(
            start_date,
            end_date
        )
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def _parse_period(period: str) -> timedelta:
    """Convert period string to timedelta"""
    value = int(period[:-1])
    unit = period[-1]
    if unit == 'd':
        return timedelta(days=value)
    elif unit == 'w':
        return timedelta(weeks=value)
    elif unit == 'm':
        return timedelta(days=value * 30)
    else:
        raise ValueError(f"Invalid period format: {period}")