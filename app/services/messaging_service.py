import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.infastructure.aws.sqs_client import SQSClient
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class MessagingService:
    """High-level messaging service for follow-up task processing"""
    
    def __init__(self, region_name: Optional[str] = None):
        self.sqs_client = SQSClient()
        
    async def send_message(
        self, 
        queue_name: str, 
        message: Dict[str, Any],
        message_group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to a specific queue"""
        try:
            # Add service metadata
            enriched_message = {
                **message,
                'metadata': {
                    **message.get('metadata', {}),
                    'service': 'ai-service',
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_name': queue_name
                }
            }
            
            result = await self.sqs_client.send_message(
                message_body=enriched_message,
                queue_name=queue_name,
                message_group_id=message_group_id
            )
            
            logger.info(f"Message sent to {queue_name}: {result['message_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending message to {queue_name}: {str(e)}")
            raise
    
    async def receive_followup_tasks(
        self, 
        max_messages: int = 10, 
        wait_time_seconds: int = 20
    ) -> List[Dict[str, Any]]:
        """Receive follow-up task messages from the queue"""
        try:
            messages = await self.sqs_client.receive_messages(
                queue_name='followup_tasks',
                max_messages=max_messages,
                wait_time_seconds=wait_time_seconds
            )
            
            followup_tasks = []
            for message in messages:
                try:
                    body = message['body']
                    
                    # Validate message structure
                    if self._is_valid_followup_task(body):
                        followup_tasks.append({
                            'receipt_handle': message['receipt_handle'],
                            'message_id': message['message_id'],
                            'task_data': body.get('task_data'),
                            'message_type': body.get('message_type'),
                            'timestamp': body.get('timestamp'),
                            'source_service': body.get('source_service')
                        })
                    else:
                        logger.warning(f"Invalid follow-up task message: {message['message_id']}")
                        # Delete invalid message
                        await self.sqs_client.delete_message(message['receipt_handle'])
                        
                except Exception as e:
                    logger.error(f"Error processing message {message['message_id']}: {str(e)}")
                    continue
            
            logger.info(f"Received {len(followup_tasks)} valid follow-up tasks")
            return followup_tasks
            
        except Exception as e:
            logger.error(f"Error receiving follow-up tasks: {str(e)}")
            raise
    
    async def listen_for_member_service_events(self) -> List[Dict[str, Any]]:
        """Listen for events from member service (REQ-0 implementation)"""
        try:
            messages = await self.sqs_client.receive_messages(
                queue_name='ai_notes',  # Queue subscribed to member service topic
                max_messages=10,
                wait_time_seconds=20
            )
            
            processed_events = []
            for message in messages:
                try:
                    body = message['body']
                    
                    # Validate member service event structure
                    if self._is_valid_member_service_event(body):
                        processed_events.append({
                            'receipt_handle': message['receipt_handle'],
                            'message_id': message['message_id'],
                            'event_type': body.get('event_type'),
                            'event_data': body.get('event_data'),
                            'timestamp': body.get('timestamp'),
                            'source_service': body.get('source_service')
                        })
                    else:
                        logger.warning(f"Invalid member service event: {message['message_id']}")
                        await self.sqs_client.delete_message(
                            message['receipt_handle'], 
                            queue_name='ai_notes'
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing member service event {message['message_id']}: {str(e)}")
                    continue
            
            logger.info(f"Received {len(processed_events)} valid member service events")
            return processed_events
            
        except Exception as e:
            logger.error(f"Error listening for member service events: {str(e)}")
            raise
    
    def _is_valid_member_service_event(self, message_body: Dict[str, Any]) -> bool:
        """Validate if the message is a valid member service event"""
        required_fields = ['event_type', 'event_data', 'source_service']
        
        for field in required_fields:
            if field not in message_body:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Check if it's from member service
        if message_body['source_service'] != 'member-service':
            logger.warning(f"Invalid source service: {message_body['source_service']}")
            return False
        
        return True
    
    async def send_followup_response(
        self, 
        task_id: int,
        person_id: str,
        generated_note: str,
        ai_confidence_score: float,
        status: str = "completed",
        error_message: Optional[str] = None,
        recommended_actions: Optional[List[str]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send follow-up note response back to member service"""
        try:
            response_message = {
                'message_type': 'followup_note_generated' if status == 'completed' else 'followup_note_error',
                'task_id': task_id,
                'person_id': person_id,
                'generated_note': generated_note,
                'ai_confidence_score': ai_confidence_score,
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'source_service': 'ai_service'
            }
            
            # Add optional fields
            if error_message:
                response_message['error'] = error_message
            
            if recommended_actions:
                response_message['recommended_actions'] = recommended_actions
            
            if additional_metadata:
                response_message['metadata'] = additional_metadata
            
            result = await self.send_message(
                queue_name='member-service-response',
                message=response_message,
                message_group_id=f"task_{task_id}"
            )
            
            logger.info(f"Follow-up response sent for task {task_id}: {result['message_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending follow-up response for task {task_id}: {str(e)}")
            raise
    
    async def acknowledge_message(self, receipt_handle: str) -> bool:
        """Acknowledge and delete a processed message"""
        try:
            result = await self.sqs_client.delete_message(receipt_handle)
            logger.info(f"Message acknowledged: {receipt_handle[:10]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error acknowledging message: {str(e)}")
            return False
    
    def _is_valid_followup_task(self, message_body: Dict[str, Any]) -> bool:
        """Validate if the message is a valid follow-up task"""
        required_fields = ['message_type', 'task_data']
        
        # Check required top-level fields
        for field in required_fields:
            if field not in message_body:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Check message type
        if message_body['message_type'] != 'task_created':
            logger.warning(f"Invalid message type: {message_body['message_type']}")
            return False
        
        # Check task data structure
        task_data = message_body['task_data']
        required_task_fields = ['id', 'task_title', 'task_description', 'recipient']
        
        for field in required_task_fields:
            if field not in task_data:
                logger.warning(f"Missing required task field: {field}")
                return False
        
        # Check recipient structure
        recipient = task_data['recipient']
        required_recipient_fields = ['person_id', 'person']
        
        for field in required_recipient_fields:
            if field not in recipient:
                logger.warning(f"Missing required recipient field: {field}")
                return False
        
        # Check person structure
        person = recipient['person']
        required_person_fields = ['first_name', 'last_name']
        
        for field in required_person_fields:
            if field not in person:
                logger.warning(f"Missing required person field: {field}")
                return False
        
        return True
