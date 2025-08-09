# app/security/service_auth.py
from typing import Optional
import httpx
from app.config.settings import get_settings

class ServiceAuthClient:
    """Client for VecApp central authentication service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.auth_service_url = self.settings.CENTRAL_AUTH_SERVICE_URL
        self.service_id = self.settings.SERVICE_ID  # "vecapp-ai"
        self.service_secret = self.settings.SERVICE_SECRET
    
    async def get_service_token(self, tenant_id: str) -> str:
        """Get service-to-service token from central auth"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_service_url}/service/token",
                json={
                    "service_id": self.service_id,
                    "service_secret": self.service_secret,
                    "tenant_id": tenant_id,
                    "scopes": ["data_access", "ai_operations"]
                }
            )
            return response.json()["access_token"]
    
    async def validate_service_token(self, token: str) -> dict:
        """Validate incoming service token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_service_url}/service/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.json()