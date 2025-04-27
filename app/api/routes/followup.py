"""API routes for follow-up note management."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict
from datetime import datetime

from app.core.auth import get_current_tenant
from app.models.tenant import Tenant
from app.models import Visitor, FollowUpTask
from app.agents.followup_summary_agent import FollowupSummaryAgent
from app.data.sqs_client import SQSClient
from app.api.schemas import FollowupNoteCreate, FollowupNoteResponse

router = APIRouter(prefix="/api/v1/followup-notes", tags=["followup"])

# Initialize SQS client
sqs_client = SQSClient()

@router.post("/generate", response_model=Dict[str, str])
async def generate_followup_note(
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Generate AI-powered follow-up note for a visitor.
    
    Args:
        background_tasks: FastAPI background tasks
        tenant: Current tenant context
        
    Returns:
        Status message
    """
    try:
        # Process SQS messages
        messages = await sqs_client.receive_messages()
        if not messages:
            return {"status": "no messages"}

        for message in messages:
            visitor_id = message.get('visitor_id')
            
            # Retrieve visitor data
            visitor = await Visitor.get(visitor_id, tenant.id)
            if not visitor:
                raise HTTPException(status_code=404, detail="Visitor not found")

            # Generate follow-up note using AI agent
            agent = FollowupSummaryAgent()
            followup_note = await agent.generate_followup_note(visitor)

            # Create follow-up task
            note = FollowupNoteCreate(
                visitor_id=visitor_id,
                content=followup_note,
                note_type="ai_generated",
                priority="medium"
            )
            
            task = await FollowUpTask.create_or_update(note.dict())
            
            # Delete processed message
            await sqs_client.delete_message(message['receipt_handle'])

            return {
                "status": "success",
                "message": "Follow-up note generated successfully",
                "task_id": task.id
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{note_id}", response_model=FollowupNoteResponse)
async def get_followup_note(
    note_id: str,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get follow-up note by ID.
    
    Args:
        note_id: ID of the follow-up note
        tenant: Current tenant context
        
    Returns:
        Follow-up note details
    """
    try:
        note = await FollowUpTask.get(note_id, tenant.id)
        if not note:
            raise HTTPException(status_code=404, detail="Follow-up note not found")
        return FollowupNoteResponse(**note.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))