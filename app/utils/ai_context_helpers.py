"""
AI Context Helper Utilities

This module provides utility functions for AI services to seamlessly
handle authentication and database context.
"""
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import asyncpg
from app.database.repositories.tenant_context import TenantContext
from app.api.schemas.auth_user import UserResponse, TenantContextResponse

async def get_ai_database_context(
    ai_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get database context from AI authentication context.
    
    Args:
        ai_context: Context from AIContext dependency
        
    Returns:
        Enhanced context with database information
    """
    if not ai_context.get("tenant_id"):
        return {**ai_context, "database": {"ready": False, "reason": "No tenant"}}
    
    db_context = await TenantContext.get_tenant_database_context(ai_context["tenant_id"])
    
    return {
        **ai_context,
        "database": db_context
    }

@asynccontextmanager
async def get_tenant_db_connection(ai_context: Dict[str, Any]):
    """
    Get tenant-specific database connection from AI context.
    
    Args:
        ai_context: Context from AIContext dependency
        
    Yields:
        Database connection with tenant schema set
    """
    if not ai_context.get("tenant_id"):
        raise ValueError("No tenant ID in AI context")
    
    schema_name = f"tenant_{ai_context['tenant_id'].lower()}"
    
    async with TenantContext.tenant_connection(schema_name) as conn:
        yield conn

def format_ai_prompt_context(ai_context: Dict[str, Any]) -> str:
    """
    Format AI context for use in LangChain prompts.
    
    Args:
        ai_context: Context from AIContext dependency
        
    Returns:
        Formatted context string for prompts
    """
    if not ai_context.get("authenticated"):
        return "Context: Anonymous user"
    
    user_info = f"User: {ai_context.get('user', {}).get('name', 'Unknown')}"
    tenant_info = f"Organization: {ai_context.get('tenant', {}).get('name', 'Unknown')}"
    
    return f"Context: {user_info}, {tenant_info}"