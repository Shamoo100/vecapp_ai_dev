from typing import Dict, Any, List
from datetime import datetime, timedelta
from core.database import Database
from models.metrics import AnalyticsMetrics

class AnalyticsService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.database = Database()

    async def get_dashboard_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get main dashboard metrics"""
        return {
            "visitor_metrics": await self._get_visitor_metrics(start_date, end_date),
            "engagement_metrics": await self._get_engagement_metrics(start_date, end_date),
            "volunteer_metrics": await self._get_volunteer_metrics(start_date, end_date),
            "follow_up_metrics": await self._get_follow_up_metrics(start_date, end_date)
        }

    async def get_visitor_trends(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get visitor engagement trends"""
        query = """
        SELECT 
            date_trunc('day', visit_date) as date,
            COUNT(*) as visitor_count,
            AVG(engagement_score) as avg_engagement
        FROM {schema}.visitors
        WHERE visit_date BETWEEN $1 AND $2
        GROUP BY date_trunc('day', visit_date)
        ORDER BY date
        """
        
        results = await self.database.fetch_all(
            query,
            start_date,
            end_date,
            schema=f"tenant_{self.tenant_id}"
        )
        
        return [dict(row) for row in results]

    async def get_volunteer_performance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get volunteer performance metrics"""
        query = """
        SELECT 
            v.volunteer_id,
            v.name,
            COUNT(f.follow_up_id) as total_follow_ups,
            AVG(f.response_time) as avg_response_time,
            AVG(f.satisfaction_score) as avg_satisfaction
        FROM {schema}.volunteers v
        LEFT JOIN {schema}.follow_ups f ON v.volunteer_id = f.volunteer_id
        WHERE f.created_at BETWEEN $1 AND $2
        GROUP BY v.volunteer_id, v.name
        """
        
        results = await self.database.fetch_all(
            query,
            start_date,
            end_date,
            schema=f"tenant_{self.tenant_id}"
        )
        
        return [dict(row) for row in results]

    async def _get_visitor_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get visitor-related metrics"""
        return {
            "total_visitors": await self._count_visitors(start_date, end_date),
            "return_rate": await self._calculate_return_rate(start_date, end_date),
            "avg_engagement_score": await self._calculate_avg_engagement(start_date, end_date)
        }

    async def _get_engagement_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get engagement-related metrics"""
        return {
            "engagement_rate": await self._calculate_engagement_rate(start_date, end_date),
            "response_rate": await self._calculate_response_rate(start_date, end_date),
            "satisfaction_score": await self._calculate_satisfaction_score(start_date, end_date)
        } 