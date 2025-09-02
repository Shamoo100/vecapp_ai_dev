from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
import json
import logging

from app.database.repositories.connection import DatabaseConnection
from app.data.models.ai_service_models import (
    AuditLogEntry, RecommendationLogInput, RecommendationItem
)

logger = logging.getLogger(__name__)

class AIMetadataService:
    """Centralized service for tracking AI performance metadata."""
    
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
    
    async def track_ai_generation_session(
        self,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track complete AI generation session with all metadata."""
        session_id = uuid4()
        results = {
            'session_id': session_id,
            'audit_saved': False,
            'recommendations_saved': False,
            'suppression_events': [],
            'errors': []
        }
        
        try:
            # 1. Save audit log
            if session_data.get('audit_data'):
                audit_result = await self._save_audit_with_retry(
                    session_data['audit_data']
                )
                results['audit_saved'] = audit_result.get('status') == 'saved'
                if not results['audit_saved']:
                    results['errors'].append(f"Audit save failed: {audit_result.get('error')}")
            
            # 2. Save recommendations
            if session_data.get('recommendations'):
                rec_result = await self._save_recommendations_with_retry(
                    session_data['recommendations']
                )
                results['recommendations_saved'] = rec_result.get('status') == 'saved'
                if not results['recommendations_saved']:
                    results['errors'].append(f"Recommendations save failed: {rec_result.get('error')}")
            
            # 3. Track suppression events
            if session_data.get('suppression_events'):
                for event in session_data['suppression_events']:
                    supp_result = await self._save_suppression_event(event)
                    results['suppression_events'].append(supp_result)
            
            # 4. Save performance metrics
            await self._save_performance_metrics(
                session_id, session_data.get('performance_metrics', {})
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in AI metadata tracking session: {str(e)}")
            results['errors'].append(f"Session tracking failed: {str(e)}")
            return results
    
    async def _save_audit_with_retry(
        self, 
        audit_data: Dict[str, Any], 
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Save audit log with retry logic and error handling."""
        for attempt in range(max_retries):
            try:
                # Ensure all datetime fields are timezone-aware
                if 'timestamp' in audit_data:
                    audit_data['timestamp'] = self._ensure_timezone_aware(
                        audit_data['timestamp']
                    )
                
                # Create audit entry
                audit_entry = AuditLogEntry(**audit_data)
                
                # Save using repository
                from app.data.repositories.ai_service_repository import AIServiceRepository
                repo = AIServiceRepository(self.schema_name)
                result = await repo.create_audit_log(audit_entry)
                
                return {'status': 'saved', 'audit_id': result['id']}
                
            except Exception as e:
                logger.warning(f"Audit save attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return {'status': 'failed', 'error': str(e)}
                
                # Wait before retry
                import asyncio
                await asyncio.sleep(0.5 * (attempt + 1))
    
    def _ensure_timezone_aware(self, dt) -> datetime:
        """Ensure datetime is timezone-aware."""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        return datetime.now(timezone.utc)
    
    async def _save_performance_metrics(
        self, 
        session_id: UUID, 
        metrics: Dict[str, Any]
    ) -> None:
        """Save AI performance metrics for analysis."""
        try:
            async with DatabaseConnection.get_connection(self.schema_name) as conn:
                query = """
                INSERT INTO ai_performance_metrics (
                    session_id, generation_time_ms, token_count, 
                    confidence_score, quality_score, model_version, 
                    metrics_data, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                
                await conn.execute(
                    query,
                    session_id,
                    metrics.get('generation_time_ms', 0),
                    metrics.get('token_count', 0),
                    metrics.get('confidence_score', 0.0),
                    metrics.get('quality_score', 0.0),
                    metrics.get('model_version', 'unknown'),
                    json.dumps(metrics),
                    datetime.now(timezone.utc)
                )
                
        except Exception as e:
            logger.error(f"Error saving performance metrics: {str(e)}")