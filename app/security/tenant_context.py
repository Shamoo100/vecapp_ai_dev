from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate tenant context from requests"""
    
    async def dispatch(self, request: Request, call_next):
        """Extract tenant ID from request and set in context"""
        # Try to get tenant ID from header
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # If not in header, try to get from path
        if not tenant_id and "tenants" in request.url.path:
            path_parts = request.url.path.split("/")
            tenant_index = path_parts.index("tenants") if "tenants" in path_parts else -1
            if tenant_index >= 0 and tenant_index + 1 < len(path_parts):
                tenant_id = path_parts[tenant_index + 1]
        
        # Set tenant ID in request state if found
        if tenant_id:
            request.state.tenant_id = tenant_id
            logger.debug(f"Set tenant context: {tenant_id}")
        
        response = await call_next(request)
        return response 