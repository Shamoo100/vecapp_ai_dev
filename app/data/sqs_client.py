import boto3
import json
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class SQSClient:
    """Client for interacting with AWS SQS"""
    
    def __init__(self):
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
        self.queue_url = settings.SQS_QUEUE_URL
        
    async def send_message(self, message_body: Dict[str, Any], message_group_id: str = None) -> Dict[str, Any]:
        """Send a message to SQS queue"""
        try:
            # Add correlation ID and timestamp
            if 'metadata' not in message_body:
                message_body['metadata'] = {}
                
            message_body['metadata'].update({
                'correlation_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'ai-service'
            })
            
            params = {
                'QueueUrl': self.queue_url,
                'MessageBody': json.dumps(message_body)
            }
            
            # Add message group ID for FIFO queues
            if message_group_id and '.fifo' in self.queue_url:
                params['MessageGroupId'] = message_group_id
                params['MessageDeduplicationId'] = f"{message_body['metadata']['correlation_id']}"
            
            response = self.sqs.send_message(**params)
            
            logger.info(f"Sent message to SQS: {response['MessageId']}")
            return {
                'message_id': response['MessageId'],
                'correlation_id': message_body['metadata']['correlation_id']
            }
        except Exception as e:
            logger.error(f"Error sending message to SQS: {str(e)}")
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
    
    async def receive_messages(self, max_messages: int = 10, wait_time_seconds: int = 20) -> list:
        """Receive messages from SQS queue"""
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} messages from SQS")
            
            parsed_messages = []
            for message in messages:
                try:
                    body = json.loads(message['Body'])
                    parsed_messages.append({
                        'receipt_handle': message['ReceiptHandle'],
                        'message_id': message['MessageId'],
                        'body': body
                    })
                except json.JSONDecodeError:
                    logger.error(f"Error parsing message body: {message['Body']}")
            
            return parsed_messages
        except Exception as e:
            logger.error(f"Error receiving messages from SQS: {str(e)}")
            raise
    
    async def delete_message(self, receipt_handle: str) -> bool:
        """Delete a message from SQS queue"""
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info(f"Deleted message from SQS: {receipt_handle[:10]}...")
            return True
        except Exception as e:
            logger.error(f"Error deleting message from SQS: {str(e)}")
            return False 