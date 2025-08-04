"""
Production-ready SQS message handler with robust error handling and message lifecycle management.
"""
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import asyncio

logger = logging.getLogger(__name__)


class SQSMessageHandler:
    """
    Production-ready SQS message handler with comprehensive error handling,
    retry logic, and proper message lifecycle management.
    """
    
    def __init__(self, queue_url: str, region_name: str = 'us-east-1'):
        """
        Initialize SQS message handler.
        
        Args:
            queue_url: SQS queue URL
            region_name: AWS region name
        """
        self.queue_url = queue_url
        self.region_name = region_name
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        
    async def process_messages(
        self,
        processor_func: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        max_messages: int = 10,
        timeout_seconds: int = 300,
        wait_time_seconds: int = 5
    ) -> Dict[str, Any]:
        """
        Process messages from SQS queue with proper lifecycle management.
        
        Args:
            processor_func: Async function to process each message
            max_messages: Maximum number of messages to process
            timeout_seconds: Maximum time to wait for messages
            wait_time_seconds: Long polling wait time
            
        Returns:
            Processing summary with statistics
        """
        start_time = datetime.now()
        processed_count = 0
        successful_count = 0
        failed_count = 0
        errors = []
        
        logger.info(f"🚀 Starting SQS message processing...")
        logger.info(f"📊 Max messages: {max_messages}, Timeout: {timeout_seconds}s")
        
        try:
            while processed_count < max_messages:
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    logger.info(f"⏰ Timeout reached ({timeout_seconds}s)")
                    break
                
                try:
                    # Receive messages from queue
                    response = self.sqs_client.receive_message(
                        QueueUrl=self.queue_url,
                        MaxNumberOfMessages=1,
                        WaitTimeSeconds=wait_time_seconds,
                        MessageAttributeNames=['All']
                    )
                    
                    messages = response.get('Messages', [])
                    
                    if not messages:
                        logger.debug("📭 No messages available, continuing...")
                        continue
                    
                    # Process each message
                    for message in messages:
                        message_result = await self._process_single_message(
                            message, processor_func
                        )
                        
                        processed_count += 1
                        
                        if message_result['success']:
                            successful_count += 1
                        else:
                            failed_count += 1
                            errors.append(message_result['error'])
                
                except ClientError as e:
                    error_msg = f"SQS client error: {e}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    await asyncio.sleep(5)  # Wait before retrying
                
                except Exception as e:
                    error_msg = f"Unexpected error in message processing loop: {e}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    await asyncio.sleep(5)  # Wait before retrying
            
            # Calculate final statistics
            total_duration = (datetime.now() - start_time).total_seconds()
            
            summary = {
                'total_processed': processed_count,
                'successful': successful_count,
                'failed': failed_count,
                'duration_seconds': total_duration,
                'errors': errors,
                'success_rate': successful_count / processed_count if processed_count > 0 else 0
            }
            
            logger.info(f"🏁 SQS processing completed: {successful_count}/{processed_count} successful")
            return summary
            
        except Exception as e:
            logger.error(f"💥 Fatal error in SQS message processing: {e}")
            raise
    
    async def _process_single_message(
        self,
        message: Dict[str, Any],
        processor_func: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Process a single SQS message with proper error handling and deletion.
        
        Args:
            message: SQS message object
            processor_func: Function to process the message data
            
        Returns:
            Processing result with success status
        """
        message_id = message.get('MessageId', 'unknown')
        receipt_handle = message['ReceiptHandle']
        
        try:
            # Parse message body
            try:
                event_data = json.loads(message['Body'])
                logger.info(f"📨 Processing message {message_id}: {event_data.get('person_id', 'unknown')}")
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON in message {message_id}: {e}"
                logger.error(f"❌ {error_msg}")
                # Don't delete malformed messages - they need manual review
                return {
                    'success': False,
                    'error': error_msg,
                    'message_deleted': False
                }
            
            # Process the event data
            try:
                processing_result = await processor_func(event_data)
                
                # Check if processing was successful
                if processing_result.get('status') == 'completed':
                    # Delete message from queue on successful processing
                    try:
                        self.sqs_client.delete_message(
                            QueueUrl=self.queue_url,
                            ReceiptHandle=receipt_handle
                        )
                        logger.info(f"🗑️ Message {message_id} successfully deleted from queue")
                        
                        return {
                            'success': True,
                            'message_deleted': True,
                            'processing_result': processing_result
                        }
                        
                    except Exception as delete_error:
                        error_msg = f"Failed to delete message {message_id}: {delete_error}"
                        logger.error(f"❌ {error_msg}")
                        # Processing succeeded but deletion failed - this is concerning
                        return {
                            'success': True,  # Processing was successful
                            'message_deleted': False,
                            'error': error_msg,
                            'processing_result': processing_result
                        }
                else:
                    # Processing failed - leave message in queue for retry
                    error_msg = f"Processing failed for message {message_id}: {processing_result.get('final_error', 'Unknown error')}"
                    logger.warning(f"⚠️ {error_msg}")
                    
                    return {
                        'success': False,
                        'error': error_msg,
                        'message_deleted': False,
                        'processing_result': processing_result
                    }
                    
            except Exception as processing_error:
                error_msg = f"Processing exception for message {message_id}: {processing_error}"
                logger.error(f"❌ {error_msg}")
                # Don't delete messages that failed due to processing errors
                return {
                    'success': False,
                    'error': error_msg,
                    'message_deleted': False
                }
        
        except Exception as e:
            error_msg = f"Unexpected error processing message {message_id}: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message_deleted': False
            }
    
    async def send_message(self, message_data: Dict[str, Any], message_group_id: str = None) -> bool:
        """
        Send a message to the SQS queue.
        
        Args:
            message_data: Data to send
            message_group_id: Message group ID for FIFO queues
            
        Returns:
            True if message was sent successfully
        """
        try:
            send_params = {
                'QueueUrl': self.queue_url,
                'MessageBody': json.dumps(message_data)
            }
            
            # Add FIFO queue parameters if needed
            if message_group_id:
                send_params['MessageGroupId'] = message_group_id
                send_params['MessageDeduplicationId'] = f"{message_group_id}-{datetime.now().timestamp()}"
            
            response = self.sqs_client.send_message(**send_params)
            
            logger.info(f"📤 Message sent successfully - MessageId: {response.get('MessageId')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
    
    def get_queue_attributes(self) -> Dict[str, Any]:
        """
        Get queue attributes for monitoring.
        
        Returns:
            Queue attributes including message counts
        """
        try:
            response = self.sqs_client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['All']
            )
            return response.get('Attributes', {})
        except Exception as e:
            logger.error(f"❌ Failed to get queue attributes: {e}")
            return {}