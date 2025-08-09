import boto3
import json
import uuid
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class SQSClient:
    """
    AWS SQS Client for handling queue operations.
    Supports both standard and FIFO queues with comprehensive message handling.
    Always loads credentials directly from .env file for consistency.
    """
    
    def __init__(self, default_queue_url: Optional[str] = None):
        """
        Initialize SQS client with AWS credentials from .env file.
        
        Args:
            default_queue_url: Optional default queue URL to use for operations
        """
        self.settings = get_settings()
        
        # Load credentials directly from .env file
        self._load_env_credentials()
        
        # Initialize boto3 SQS client with explicit credentials
        self.sqs = boto3.client(
            'sqs',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
        
        # Set default queue URL if provided
        self.default_queue_url = default_queue_url or self.settings.NEW_VISITOR_SIGNUP_QUEUE_URL
        
        logger.info(f"✅ SQS Client initialized")
        if self.default_queue_url:
            logger.info(f"📍 Default Queue URL: {self.default_queue_url}")
        logger.info(f"🌍 Region: {self.aws_region}")
    
    def _load_env_credentials(self):
        """
        Load AWS credentials directly from .env file.
        This ensures we always use the latest credentials from .env,
        bypassing any cached environment variables or AWS credential files.
        """
        # Load .env file explicitly
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(env_path, override=True)
        
        # Get credentials from environment (now loaded from .env)
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Validate credentials
        if not self.aws_access_key_id:
            raise ValueError("AWS_ACCESS_KEY_ID not found in .env file")
        if not self.aws_secret_access_key:
            raise ValueError("AWS_SECRET_ACCESS_KEY not found in .env file")
        
        # Clean credentials (strip whitespace)
        self.aws_access_key_id = str(self.aws_access_key_id).strip()
        self.aws_secret_access_key = str(self.aws_secret_access_key).strip()
        self.aws_region = str(self.aws_region).strip()
        
        logger.info(f"🔑 Loaded AWS credentials from .env file")
        logger.info(f"   Access Key: {self.aws_access_key_id}")
        logger.info(f"   Region: {self.aws_region}")
    
    def _get_queue_url(self, queue_url: Optional[str] = None) -> str:
        """
        Get the queue URL to use for operations.
        
        Args:
            queue_url: Specific queue URL, falls back to default if not provided
            
        Returns:
            Queue URL to use
            
        Raises:
            ValueError: If no queue URL is available
        """
        url = queue_url or self.default_queue_url
        if not url:
            raise ValueError("No queue URL provided and no default queue URL configured")
        return url
    
    async def send_message(
        self, 
        message_body: Dict[str, Any],
        queue_url: Optional[str] = None,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the specified SQS queue.
        
        Args:
            message_body: Dictionary containing the message data
            queue_url: Queue URL (uses default if not provided)
            message_group_id: Group ID for FIFO queues
            message_deduplication_id: Deduplication ID for FIFO queues
            
        Returns:
            Dictionary with message_id and correlation_id
        """
        try:
            target_queue_url = self._get_queue_url(queue_url)
            
            # Generate correlation ID for tracking
            correlation_id = str(uuid.uuid4())
            
            # Add metadata to message
            enhanced_message = {
                **message_body,
                'metadata': {
                    'correlation_id': correlation_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'ai-service'
                }
            }
            
            # Prepare SQS parameters
            params = {
                'QueueUrl': target_queue_url,
                'MessageBody': json.dumps(enhanced_message, default=str)
            }
            
            # Add FIFO-specific parameters if queue is FIFO
            if target_queue_url.endswith('.fifo'):
                params['MessageGroupId'] = message_group_id or 'default_group'
                params['MessageDeduplicationId'] = message_deduplication_id or correlation_id
            
            # Send message
            response = self.sqs.send_message(**params)
            
            result = {
                'message_id': response['MessageId'],
                'correlation_id': correlation_id,
                'queue_url': target_queue_url
            }
            
            logger.info(f"✅ Message sent successfully: {response['MessageId']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send message: {str(e)}")
            raise
    
    async def receive_messages(
        self, 
        queue_url: Optional[str] = None,
        max_messages: int = 10,
        wait_time_seconds: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from the specified SQS queue.
        
        Args:
            queue_url: Queue URL (uses default if not provided)
            max_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Long polling wait time (0-20 seconds)
            
        Returns:
            List of parsed messages with receipt handles
        """
        try:
            target_queue_url = self._get_queue_url(queue_url)
            
            response = self.sqs.receive_message(
                QueueUrl=target_queue_url,
                MaxNumberOfMessages=min(max_messages, 10),  # AWS limit is 10
                WaitTimeSeconds=min(wait_time_seconds, 20),  # AWS limit is 20
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            logger.info(f"📥 Received {len(messages)} messages from queue")
            
            parsed_messages = []
            for message in messages:
                try:
                    body = json.loads(message['Body'])
                    parsed_messages.append({
                        'message_id': message['MessageId'],
                        'receipt_handle': message['ReceiptHandle'],
                        'body': body,
                        'attributes': message.get('Attributes', {}),
                        'message_attributes': message.get('MessageAttributes', {})
                    })
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse message body: {e}")
                    # Still include the raw message for debugging
                    parsed_messages.append({
                        'message_id': message['MessageId'],
                        'receipt_handle': message['ReceiptHandle'],
                        'body': message['Body'],  # Raw body
                        'parse_error': str(e)
                    })
            
            return parsed_messages
            
        except Exception as e:
            logger.error(f"❌ Failed to receive messages: {str(e)}")
            raise
    
    async def delete_message(
        self, 
        receipt_handle: str, 
        queue_url: Optional[str] = None
    ) -> bool:
        """
        Delete a processed message from the queue.
        
        Args:
            receipt_handle: Receipt handle from received message
            queue_url: Queue URL (uses default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            target_queue_url = self._get_queue_url(queue_url)
            
            self.sqs.delete_message(
                QueueUrl=target_queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.info(f"🗑️ Message deleted successfully: {receipt_handle[:20]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete message: {str(e)}")
            return False
    
    def get_queue_attributes(self, queue_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get queue attributes for monitoring and debugging.
        
        Args:
            queue_url: Queue URL (uses default if not provided)
            
        Returns:
            Dictionary with queue attributes
        """
        try:
            target_queue_url = self._get_queue_url(queue_url)
            
            response = self.sqs.get_queue_attributes(
                QueueUrl=target_queue_url,
                AttributeNames=['All']
            )
            
            attributes = response.get('Attributes', {})
            logger.info(f"📊 Queue attributes retrieved for: {target_queue_url}")
            return attributes
            
        except Exception as e:
            logger.error(f"❌ Failed to get queue attributes: {str(e)}")
            raise
    
    def test_connection(self, queue_url: Optional[str] = None) -> bool:
        """
        Test the SQS connection by getting queue attributes.
        
        Args:
            queue_url: Queue URL (uses default if not provided)
            
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            target_queue_url = self._get_queue_url(queue_url)
            
            self.sqs.get_queue_attributes(
                QueueUrl=target_queue_url,
                AttributeNames=['QueueArn']
            )
            
            logger.info(f"✅ SQS connection test successful for: {target_queue_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SQS connection test failed: {str(e)}")
            return False


# Backward compatibility - keep the new visitor specific methods available
class NewVisitorSQSClient(SQSClient):
    """
    Specialized SQS client for new visitor signup queue.
    Inherits from the general SQSClient with visitor-specific convenience methods.
    """
    
    def __init__(self):
        """Initialize with new visitor signup queue as default"""
        settings = get_settings()
        super().__init__(default_queue_url=settings.NEW_VISITOR_SIGNUP_QUEUE_URL)
    
    async def send_visitor_signup_message(
        self, 
        visitor_data: Dict[str, Any],
        message_group_id: str = "new_visitor_signup"
    ) -> Dict[str, Any]:
        """
        Send a new visitor signup message to the queue.
        
        Args:
            visitor_data: Dictionary containing visitor information
            message_group_id: Group ID for FIFO queue
            
        Returns:
            Dictionary with message_id and correlation_id
        """
        message = {
            'event_type': 'new_visitor_signup',
            'visitor_data': visitor_data
        }
        
        return await self.send_message(
            message_body=message,
            message_group_id=message_group_id
        )
    
    async def receive_visitor_signup_messages(
        self, 
        max_messages: int = 10,
        wait_time_seconds: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Receive new visitor signup messages from the queue.
        
        Args:
            max_messages: Maximum number of messages to receive
            wait_time_seconds: Long polling wait time
            
        Returns:
            List of parsed messages with receipt handles
        """
        return await self.receive_messages(
            max_messages=max_messages,
            wait_time_seconds=wait_time_seconds
        )