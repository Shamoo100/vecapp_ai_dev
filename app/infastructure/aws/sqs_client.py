import boto3
import json
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class SQSClient:
    """Unified client for interacting with AWS SQS and SNS"""
    
    def __init__(self, default_queue_url: Optional[str] = None):
        self.sqs = boto3.client(
            'sqs',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.sns = boto3.client(
            'sns',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        # Support multiple queue URLs
        self.default_queue_url = default_queue_url or settings.SQS_QUEUE_URL
        self.queue_urls = {
            'followup_tasks': getattr(settings, 'FOLLOWUP_TASK_QUEUE_URL', settings.SQS_QUEUE_URL),
            'member_service_response': getattr(settings, 'MEMBER_SERVICE_RESPONSE_QUEUE_URL', settings.SQS_QUEUE_URL),
            'ai_notes': getattr(settings, 'AI_NOTES_QUEUE_URL', settings.SQS_QUEUE_URL),
        }
        
    async def send_message(
        self, 
        message_body: Dict[str, Any], 
        queue_name: Optional[str] = None,
        queue_url: Optional[str] = None,
        message_group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to SQS queue"""
        try:
            # Determine queue URL
            target_queue_url = queue_url or self.queue_urls.get(queue_name, self.default_queue_url)
            
            # Add correlation ID and timestamp
            if 'metadata' not in message_body:
                message_body['metadata'] = {}
                
            message_body['metadata'].update({
                'correlation_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'ai-service',
                'queue_name': queue_name or 'default'
            })
            
            params = {
                'QueueUrl': target_queue_url,
                'MessageBody': json.dumps(message_body)
            }
            
            # Add message group ID for FIFO queues
            if message_group_id and '.fifo' in target_queue_url:
                params['MessageGroupId'] = message_group_id
                params['MessageDeduplicationId'] = f"{message_body['metadata']['correlation_id']}"
            
            response = self.sqs.send_message(**params)
            
            logger.info(f"Sent message to SQS queue {queue_name or 'default'}: {response['MessageId']}")
            return {
                'message_id': response['MessageId'],
                'correlation_id': message_body['metadata']['correlation_id'],
                'queue_name': queue_name
            }
        except Exception as e:
            logger.error(f"Error sending message to SQS queue {queue_name}: {str(e)}")
            raise
    
    async def receive_messages(
        self, 
        queue_name: Optional[str] = None,
        queue_url: Optional[str] = None,
        max_messages: int = 10, 
        wait_time_seconds: int = 20
    ) -> List[Dict[str, Any]]:
        """Receive messages from SQS queue"""
        try:
            target_queue_url = queue_url or self.queue_urls.get(queue_name, self.default_queue_url)
            
            response = self.sqs.receive_message(
                QueueUrl=target_queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} messages from SQS queue {queue_name or 'default'}")
            
            parsed_messages = []
            for message in messages:
                try:
                    body = json.loads(message['Body'])
                    parsed_messages.append({
                        'receipt_handle': message['ReceiptHandle'],
                        'message_id': message['MessageId'],
                        'body': body,
                        'queue_name': queue_name
                    })
                except json.JSONDecodeError:
                    logger.error(f"Error parsing message body: {message['Body']}")
            
            return parsed_messages
        except Exception as e:
            logger.error(f"Error receiving messages from SQS queue {queue_name}: {str(e)}")
            raise
    
    async def delete_message(
        self, 
        receipt_handle: str, 
        queue_name: Optional[str] = None,
        queue_url: Optional[str] = None
    ) -> bool:
        """Delete a message from SQS queue"""
        try:
            target_queue_url = queue_url or self.queue_urls.get(queue_name, self.default_queue_url)
            
            self.sqs.delete_message(
                QueueUrl=target_queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info(f"Deleted message from SQS queue {queue_name or 'default'}: {receipt_handle[:10]}...")
            return True
        except Exception as e:
            logger.error(f"Error deleting message from SQS queue {queue_name}: {str(e)}")
            return False
    
    async def subscribe_to_topic(
        self, 
        topic_arn: str, 
        queue_name: str,
        filter_policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Subscribe a queue to an SNS topic for REQ-0 member service integration"""
        try:
            queue_url = self.queue_urls.get(queue_name, self.default_queue_url)
            
            # Get queue attributes to get the ARN
            queue_attrs = self.sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['QueueArn']
            )
            queue_arn = queue_attrs['Attributes']['QueueArn']
            
            # Subscribe queue to topic
            subscription_params = {
                'TopicArn': topic_arn,
                'Protocol': 'sqs',
                'Endpoint': queue_arn
            }
            
            if filter_policy:
                subscription_params['Attributes'] = {
                    'FilterPolicy': json.dumps(filter_policy)
                }
            
            response = self.sns.subscribe(**subscription_params)
            
            logger.info(f"Subscribed queue {queue_name} to topic {topic_arn}")
            return {
                'subscription_arn': response['SubscriptionArn'],
                'queue_name': queue_name,
                'topic_arn': topic_arn
            }
        except Exception as e:
            logger.error(f"Error subscribing queue {queue_name} to topic {topic_arn}: {str(e)}")
            raise

    async def publish_to_topic(self, topic_arn: str, message: Dict[str, Any], subject: str = None) -> Dict[str, Any]:
        """Publish a message to an SNS topic"""
        try:
            # Add correlation ID and timestamp
            if 'metadata' not in message:
                message['metadata'] = {}
                
            message['metadata'].update({
                'correlation_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'ai-service'
            })
            
            params = {
                'TopicArn': topic_arn,
                'Message': json.dumps(message)
            }
            
            if subject:
                params['Subject'] = subject
            
            response = self.sns.publish(**params)
            
            logger.info(f"Published message to SNS topic: {response['MessageId']}")
            return {
                'message_id': response['MessageId'],
                'correlation_id': message['metadata']['correlation_id']
            }
        except Exception as e:
            logger.error(f"Error publishing message to SNS: {str(e)}")
            raise