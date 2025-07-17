import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DataFetcher:
    """Service for fetching data from external services"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.followup_service_url = settings.FOLLOWUP_SERVICE_URL
        self.analytics_service_url = settings.ANALYTICS_SERVICE_URL
    
    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_followup_data(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
        auth_token: str
    ) -> Dict[str, Any]:
        """Fetch follow-up data from the Follow-up service"""
        logger.info(f"Fetching follow-up data for tenant {tenant_id} from {start_date} to {end_date}")
        
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "X-Tenant-ID": str(tenant_id)
            }
            
            response = await self.http_client.get(
                f"{self.followup_service_url}/internal/api/v1/tenants/{tenant_id}/followup-data-for-ai",
                headers=headers,
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "include_archived": "true"
                }
            )
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when fetching follow-up data: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching follow-up data: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_analytics_data(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
        auth_token: str
    ) -> Dict[str, Any]:
        """Fetch analytics data from the Analytics service"""
        logger.info(f"Fetching analytics data for tenant {tenant_id} from {start_date} to {end_date}")
        
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "X-Tenant-ID": str(tenant_id)
            }
            
            response = await self.http_client.get(
                f"{self.analytics_service_url}/internal/api/v1/tenants/{tenant_id}/analytics-data-for-ai",
                headers=headers,
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when fetching analytics data: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching analytics data: {str(e)}")
            raise 