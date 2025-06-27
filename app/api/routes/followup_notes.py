from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from typing import Dict, Any
from app.core.api_key_auth import get_current_tenant
from app.agents.followup_summary_agent import FollowupSummaryAgent
from app.models.tenant import Tenant
from app.models import Visitor, FollowUpTask
from app.api.middleware import limiter
import boto3
import json

router = APIRouter(prefix="/api/v1/followup-notes")

# Initialize SQS client
sqs_client = boto3.client('sqs', region_name='your-region')

@router.post("/generate")
@limiter.limit("5/minute")
async def generate_followup_note(
    request: Request,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant)
):
    """Generate AI-generated follow-up note for a new visitor"""
    try:
        # Listen for SQS messages
        response = sqs_client.receive_message(
            QueueUrl='your-sqs-queue-url',
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )

        if 'Messages' not in response:
            return {"status": "no messages"}

        for message in response['Messages']:
            # Process the message
            body = json.loads(message['Body'])
            visitor_id = body.get('visitor_id')

            # Retrieve visitor data
            visitor = await Visitor.get(visitor_id, tenant.id)
            if not visitor:
                raise HTTPException(status_code=404, detail="Visitor not found")

            # Use FollowupSummaryAgent to generate notes
            agent = FollowupSummaryAgent()
            followup_note = agent.generate_followup_note(visitor)

            # Append note to follow-up task
            follow_up_task = await FollowUpTask.create_or_update(visitor_id, followup_note)

            # Delete the message from the queue
            sqs_client.delete_message(
                QueueUrl='your-sqs-queue-url',
                ReceiptHandle=message['ReceiptHandle']
            )

            return {
                "status": "success",
                "message": "Follow-up note generated and appended successfully",
                "task_id": follow_up_task.id
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
