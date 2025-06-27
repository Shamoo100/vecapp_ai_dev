"""API routes for analytics and reporting."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timedelta
from app.core.api_key_auth import get_current_tenant
from app.core.analytics import AnalyticsService
from app.models.tenant import Tenant
from app.api.schemas import DashboardMetrics, VisitorTrends, VolunteerPerformance

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    tenant: Tenant = Depends(get_current_tenant),
    period: str = "30d"
):
    """Get main dashboard metrics.
    
    Args:
        tenant: Current tenant context
        period: Time period for metrics (e.g., '30d', '7d')
        
    Returns:
        Dashboard metrics
    """
    try:
        analytics = AnalyticsService(tenant.id)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - _parse_period(period)
        
        metrics = await analytics.get_dashboard_metrics(start_date, end_date)
        return DashboardMetrics(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visitor-trends", response_model=VisitorTrends)
async def get_visitor_trends(
    start_date: datetime,
    end_date: datetime,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get visitor engagement trends.
    
    Args:
        start_date: Start date for trend analysis
        end_date: End date for trend analysis
        tenant: Current tenant context
        
    Returns:
        Visitor trend metrics
    """
    try:
        analytics = AnalyticsService(tenant.id)
        trends = await analytics.get_visitor_trends(start_date, end_date)
        return VisitorTrends(**trends)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/volunteer-performance", response_model=List[VolunteerPerformance])
async def get_volunteer_performance(
    tenant: Tenant = Depends(get_current_tenant),
    period: str = "30d"
):
    """Get volunteer performance metrics.
    
    Args:
        tenant: Current tenant context
        period: Time period for metrics
        
    Returns:
        List of volunteer performance metrics
    """
    try:
        analytics = AnalyticsService(tenant.id)
        end_date = datetime.utcnow()
        start_date = end_date - _parse_period(period)
        
        performance = await analytics.get_volunteer_performance(
            start_date,
            end_date
        )
        return [VolunteerPerformance(**p) for p in performance]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _parse_period(period: str) -> timedelta:
    """Parse period string into timedelta.
    
    Args:
        period: Period string (e.g., '30d', '7d')
        
    Returns:
        Corresponding timedelta
        
    Raises:
        ValueError: If period format is invalid
    """
    try:
        value = int(period[:-1])
        unit = period[-1]
        
        if unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        elif unit == 'm':
            return timedelta(days=value * 30)
        else:
            raise ValueError(f"Invalid period unit: {unit}")
    except (IndexError, ValueError):
        raise ValueError(f"Invalid period format: {period}")