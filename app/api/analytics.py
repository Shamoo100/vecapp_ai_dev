from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
from core.auth import get_current_tenant
from core.analytics import AnalyticsService
from app.database.tenant_management import Tenant

router = APIRouter(prefix="/api/v1/analytics")

@router.get("/dashboard")
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

@router.get("/visitor-trends")
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

@router.get("/volunteer-performance")
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