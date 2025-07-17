from app.infastructure.aws.sqs_client import SQSClient
import json
from app.services.followup_service import FollowupService  # Assuming this is created as per plan

class VisitorEventListener:
    def __init__(self):
        self.sqs_client = SQSClient()
    
    async def listen_for_events(self):
        # Function to continuously listen for SQS messages related to new visitor forms
        messages = await self.sqs_client.receive_messages(
            queue_name='ai_notes',
            max_messages=10
        )
        for msg in messages:
            try:
                data = json.loads(msg['Body'])
                schema_name = data.get('schema_name')
                person_id = data.get('person_id')
                task_id = data.get('task_id')
                if not all([schema_name, person_id, task_id]):
                    raise ValueError("Missing required fields in message")
                
                # Trigger AI note generation
                await FollowupService.generate_summary_note(schema_name, person_id, task_id)
                
                # Delete the message after processing
                await self.sqs_client.delete_message(
                    queue_name='ai_notes',
                    receipt_handle=msg['ReceiptHandle']
                )
            except Exception as e:
                # Log error (integrate with monitoring later)
                print(f"Error processing message: {e}")
        # To make it continuous, call this method in a loop or background task
