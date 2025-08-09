"""
Enhanced Visitor Event Listener for AI Follow-up Notes.
Processes SQS events with family context awareness and robust error handling.
"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime, timedelta

from app.infastructure.aws.sqs_client import SQSClient
from app.api.schemas.event_schemas import VisitorEventData
from app.services.followup_service import FollowupService
from app.services.visitor_context_builder import VisitorContextBuilder


logger = logging.getLogger(__name__)


class VisitorEventListener:
    """
    Enhanced visitor event listener with family context awareness.
    Processes SQS messages for visitor follow-up note generation.
    """
    
    def __init__(self):
        """Initialize the visitor event listener with required services"""
        self.sqs_client = SQSClient()
        self.followup_service = FollowupService()
        self.context_builder = VisitorContextBuilder()
        self.processing_stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "last_processed": None
        }
    
    async def listen_for_events(self, max_messages: int = 10):
        """
        Continuously listen for SQS messages related to visitor events.
        
        Args:

            max_messages: Maximum number of messages to process per batch
        """

        logger.info(f"Starting visitor event listener for visitor events")
        
        try:
            messages = await self.sqs_client.receive_messages(
                max_messages=max_messages
            )
            
            if not messages:
                logger.debug("No messages received from queue")
                return
            
            logger.info(f"Received {len(messages)} messages from queue")
            
            # Process messages in parallel for better performance
            tasks = [self._process_single_message(msg) for msg in messages]

            #TODO: update when there is need for logging
            #             tasks = []
            # for msg in messages:
            #     if msg.is_valid():
            #         try:
            #             task = self._process_single_message(msg)
            #             tasks.append(task)
            #         except Exception as e:
            #             logger.warning(f"Failed to process {msg.id}: {e}")

            # tasks = []
            # for msg in messages:
            #     task = self._process_single_message(msg)
            #     tasks.append(task)
            
            # Execute all message processing tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            
            self.processing_stats["messages_processed"] += successful
            self.processing_stats["messages_failed"] += failed
            self.processing_stats["last_processed"] = datetime.utcnow()
            
            logger.info(f"Batch processing complete: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Error in event listener: {str(e)}")
            self.processing_stats["messages_failed"] += 1
    
    async def _process_single_message(self, message: Dict[str, Any]) -> bool:
        """
        Process a single SQS message.
        
        Args:
            message: SQS message data
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        receipt_handle = message.get('receipt_handle')  # Use lowercase key as per sqs_client.py
        message_id = message.get('message_id', 'unknown')
        
        try:
            # Parse message body
            message_body_raw = message['body']
            if isinstance(message_body_raw, dict):
                message_body = message_body_raw
            else:
                message_body = json.loads(message_body_raw)

            logger.info(f"Processing message {message_id}")
            
            # Validate and parse event data
            event_data = self._parse_event_data(message_body)
            if not event_data:
                logger.error(f"Invalid event data in message {message_id}")
                await self.sqs_client.delete_message(receipt_handle=receipt_handle, queue_url=self.sqs_client.default_queue_url)
                return False
            
             # Start extending visibility timeout in background
            extend_task = asyncio.create_task(
                self._extend_visibility_timeout(
                    self.sqs_client.sqs,  # boto3 client inside SQSClient
                    self.sqs_client.default_queue_url,
                    receipt_handle
                )
            )
            # Build comprehensive visitor context
            visitor_context = await self.context_builder.build_context(event_data)
            
            # Generate AI follow-up note
            await self.followup_service.generate_enhanced_summary_note(
                event_data, visitor_context
            )

            # Cancel the visibility extension task when done
            extend_task.cancel()
            try:
                await extend_task
            except asyncio.CancelledError:
                pass
            
            # Delete message after successful processing using receipt_handle from raw message
            await self.sqs_client.delete_message(receipt_handle=receipt_handle, queue_url=self.sqs_client.default_queue_url)
            
            logger.info(f"Successfully processed message {message_id} for person {event_data.person_id}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message {message_id}: {str(e)}")
            await self.sqs_client.delete_message(receipt_handle=receipt_handle, queue_url=self.sqs_client.default_queue_url)
            return False
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {str(e)}")
            # Don't delete message on processing error - let it retry
            return False
    
    def _parse_event_data(self, message_body: Dict[str, Any]) -> Optional[VisitorEventData]:
        """
        Parse and validate event data from message body.
        
        Args:
            message_body: Raw message body from SQS
            
        Returns:
            VisitorEventData if valid, None otherwise
        """
        try:
            # Create VisitorEventData directly from message body
            event_data = VisitorEventData(**message_body)
            
            # Validate required fields
            if not all([
                event_data.person_id,
                event_data.tenant,
                event_data.family_context,
                event_data.family_history,
            ]):
                logger.error("Missing required fields in event data")
                return None
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error parsing event data: {str(e)}")
            return None
    

    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.processing_stats.copy()

    async def _extend_visibility_timeout(self, sqs_client, queue_url, receipt_handle, interval=15, duration=600):
        """
        Periodically extend the visibility timeout of a message while processing.
        
        Args:
            sqs_client: boto3 SQS client
            queue_url: SQS queue URL
            receipt_handle: Message receipt handle
            interval: How often to extend visibility (seconds)
            duration: Total time to keep extending (seconds)
        """
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                sqs_client.change_message_visibility(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle,
                    VisibilityTimeout=60  # Extend by 60 seconds each time
                )
                logger.debug(f"♻️ Extended visibility timeout for message")
            except Exception as e:
                logger.error(f"❌ Failed to extend visibility timeout: {e}")
                break
            await asyncio.sleep(interval)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the event listener"""
        try:
            # Test SQS connectivity
            await self.sqs_client.receive_messages(
                queue_name='ai_notes',
                max_messages=1
            )
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow(),
                "stats": self.get_processing_stats()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow(),
                "stats": self.get_processing_stats()
            }

