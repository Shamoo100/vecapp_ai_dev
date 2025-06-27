from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, confloat, conlist

class Sentiment(BaseModel):
    label: str
    confidence: confloat(ge=0, le=100) # Confidence percentage between 0-100

class VisitorSummary(BaseModel):
    visitor_name: str
    primary_interests: conlist(str, min_items=1) # At least one interest required
    special_requests: list[str] = []  # Optional field
    sentiment: Sentiment
    recommended_actions: List[str]
    created_at: datetime

class VisitorSummaryResponse(BaseModel):
    data: dict[str, VisitorSummary]
    meta: dict[str, str]
