from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.agents.followup_note_agent import FollowupNoteAgent
from app.security.dependencies import get_current_tenant

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/llm-providers")
async def get_llm_provider_status(
    tenant_id: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Get the status of all LLM providers.
    
    Returns:
        Dictionary containing provider status and availability
    """
    # Create a temporary agent to check LLM status
    agent = FollowupNoteAgent("health_check", tenant_id)
    
    return {
        "llm_providers": agent.get_llm_provider_status(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/llm-providers/{provider}/reset")
async def reset_llm_provider(
    provider: str,
    tenant_id: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Reset a specific LLM provider's availability status.
    
    Args:
        provider: The provider name to reset (gemini, openai, etc.)
        
    Returns:
        Success message and updated status
    """
    agent = FollowupNoteAgent("health_check", tenant_id)
    
    try:
        from app.infastructure.ai.llm_provider_factory import LLMProvider
        provider_enum = LLMProvider(provider.lower())
        agent.llm_factory.reset_provider_availability(provider_enum)
        
        return {
            "message": f"Provider {provider} availability reset successfully",
            "status": agent.get_llm_provider_status()
        }
    except ValueError:
        return {
            "error": f"Unknown provider: {provider}",
            "available_providers": [p.value for p in LLMProvider]
        }