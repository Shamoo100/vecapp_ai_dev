from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

class EngagementMetrics(BaseModel):
    visitor_count: int
    engagement_rate: float
    feedback_scores: Dict[str, float]
    volunteer_performance: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime

class VisitorMetrics(BaseModel):
    total_visitors: int
    return_rate: float
    avg_engagement_score: float
    visit_frequency: Dict[str, int]

class VolunteerMetrics(BaseModel):
    total_volunteers: int
    active_volunteers: int
    avg_response_time: float
    satisfaction_score: float
    assignments_completed: int 