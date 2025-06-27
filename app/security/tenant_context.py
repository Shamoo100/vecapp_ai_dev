from fastapi import Request, Response, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Optional, Dict, Any, Callable
import logging
from contextvars import ContextVar
from uuid import UUID

logger = logging.getLogger(__name__)

# Create a context variable to store tenant ID throughout the request lifecycle
# This allows any code to access the current tenant ID without passing it explicitly
tenant_context_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)

def get_current_tenant_id() -> Optional[str]:
    """Get the current tenant ID from the context variable
    
    Returns:
        The current tenant ID or None if not set
    """
    return tenant_context_var.get()

class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate tenant context from requests
    
    This middleware extracts the tenant ID from the request and sets it in both
    the request state and a context variable for easy access throughout the request.
    """
    
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
        
        # Set tenant ID in request state and context variable if found
        token = None
        if tenant_id:
            request.state.tenant_id = tenant_id
            # Set the tenant ID in the context variable
            token = tenant_context_var.set(tenant_id)
            logger.debug(f"Set tenant context: {tenant_id}")
        
        try:
            # Process the request with tenant context set
            response = await call_next(request)
            return response
        finally:
            # Reset the context variable when done
            if token:
                tenant_context_var.reset(token)

# Dependency to get tenant ID from request
async def get_tenant_id(request: Request) -> Optional[str]:
    """FastAPI dependency to get tenant ID from request
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The tenant ID or None if not found
    """
    return getattr(request.state, 'tenant_id', None) or get_current_tenant_id()

from typing import Optional
from fastapi import Depends, Header, HTTPException
import logging
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

# Context variable to store the current tenant schema
current_schema_var: ContextVar[Optional[str]] = ContextVar("current_schema", default=None)

def get_current_schema() -> Optional[str]:
    """
    Get the current tenant schema from the request context.
    
    Returns:
        The current tenant schema name or None if not set
    """
    return current_schema_var.get()

def set_current_schema(schema: str) -> None:
    """
    Set the current tenant schema in the request context.
    
    Args:
        schema: The tenant schema name to set
    """
    current_schema_var.set(schema)

async def get_tenant_schema(x_tenant_schema: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency to extract and validate the tenant schema from request headers.
    
    Args:
        x_tenant_schema: The tenant schema from the X-Tenant-Schema header
        
    Returns:
        The validated tenant schema
        
    Raises:
        HTTPException: If the tenant schema is missing or invalid
    """
    if not x_tenant_schema:
        raise HTTPException(status_code=400, detail="X-Tenant-Schema header is required")
    
    # Here you could add validation logic for the schema name
    # For example, check if it exists in a list of valid schemas
    
    return x_tenant_schema

class TenantSchemaMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant schema from request headers and set it in the context.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and set tenant schema in context."""
        # Extract tenant schema from header
        tenant_schema = request.headers.get("X-Tenant-Schema")
        
        if tenant_schema:
            # Set tenant schema in context
            token = set_current_schema(tenant_schema)
            try:
                # Process the request
                response = await call_next(request)
                return response
            finally:
                # Reset context after request is processed
                current_schema_var.reset(token)
        else:
            # No tenant schema provided, continue without setting context
            return await call_next(request)