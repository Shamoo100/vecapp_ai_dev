"""
Simplified AI Service Example

Demonstrates 3 essential patterns for AI services:
1. Public AI (no auth)
2. Enhanced AI (optional auth) 
3. Tenant AI (required auth + tenant)
"""
from typing import Dict, Any, Optional, Tuple
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.security.dependencies import (
    CurrentUserOptional,
    AuthContextDep,
    UserAndTenant
)
from app.api.schemas.auth_user import (
    UserResponse,
    TenantContextResponse,
    AuthContextResponse
)

router = APIRouter(prefix="/ai", tags=["AI Service Examples"])

# Request/Response Models
class AIRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 100

class AIResponse(BaseModel):
    response: str
    model: str
    authenticated: bool
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

# Pattern 1: Public AI (No Authentication)
@router.post(
    "/public",
    response_model=AIResponse,
    summary="Public AI Service",
    description="Basic AI available to everyone"
)
async def public_ai(request: AIRequest) -> AIResponse:
    """Public AI service - no authentication required."""
    return AIResponse(
        response=f"Public AI: {request.prompt[:50]}...",
        model="basic-model",
        authenticated=False
    )

# Pattern 2: Enhanced AI (Optional Authentication)
@router.post(
    "/enhanced",
    response_model=AIResponse,
    summary="Enhanced AI Service",
    description="Better AI for authenticated users, basic for everyone"
)
async def enhanced_ai(
    request: AIRequest,
    user: Optional[UserResponse] = CurrentUserOptional,
    context: Optional[AuthContextResponse] = AuthContextDep
) -> AIResponse:
    """Enhanced AI with optional authentication."""
    
    if user and context:
        # Premium features for authenticated users
        response = f"Premium AI for {user.username}: {request.prompt}"
        model = "premium-model"
        user_id = str(user.id)
        tenant_id = context.tenant.id if context.tenant else None
    else:
        # Basic features for anonymous users
        response = f"Basic AI: {request.prompt[:30]}..."
        model = "basic-model"
        user_id = None
        tenant_id = None
    
    return AIResponse(
        response=response,
        model=model,
        authenticated=user is not None,
        user_id=user_id,
        tenant_id=tenant_id
    )

# Pattern 3: Tenant AI (Required Authentication + Tenant Context)
@router.post(
    "/tenant",
    response_model=AIResponse,
    summary="Tenant AI Service", 
    description="AI with tenant-specific data (auth required)"
)
async def tenant_ai(
    request: AIRequest,
    auth: Tuple[UserResponse, TenantContextResponse] = Depends(UserAndTenant)
) -> AIResponse:
    """Tenant-aware AI service - authentication required."""
    
    user, tenant = auth
    
    response = f"Tenant AI for {tenant.name}: {request.prompt}"
    
    return AIResponse(
        response=response,
        model="tenant-model",
        authenticated=True,
        user_id=str(user.id),
        tenant_id=str(tenant.id)
    )