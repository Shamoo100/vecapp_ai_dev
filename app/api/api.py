from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.core.auth import get_current_tenant, verify_api_key
from app.core.database import Database
from app.core.analytics import AnalyticsService
from app.models.tenant import Tenant
from app.models.visitor import Visitor
from app.agents.data_collection_agent import DataCollectionAgent
from app.agents.volunteer_coordination_agent import VolunteerCoordinationAgent
from app.core.messaging import MessageQueue
from app.core.notifications import NotificationService

# Initialize main router
router = APIRouter()

# Visitor Management Endpoints
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