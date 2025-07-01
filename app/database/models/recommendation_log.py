from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.database.models.base import Base
from app.database.models.common import TimestampMixin

class AIRecommendationLog(Base, TimestampMixin):
    __tablename__ = "ai_recommendation_log"
    __table_args__ = {"schema": "demo"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    person_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    fam_id = Column(PostgresUUID(as_uuid=True))
    module_name = Column(String(50))
    recommended_entity_type = Column(String(50))
    recommended_entity_id = Column(String(50))
    recommendation_score = Column(Integer)
    recommendation_tier = Column(String(25))
    rationale = Column(String)
