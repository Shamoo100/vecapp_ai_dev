"""
Production-ready error handling utilities for VecApp AI.
Handles network failures, credential issues, and service outages.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
import json

logger = logging.getLogger(__name__)

class ProductionErrorHandler:
    """
    Comprehensive error handling for production environments.
    """
    
    @staticmethod
    def categorize_aws_error(error: Exception) -> Dict[str, Any]:
        """
        Categorize AWS-related errors and provide actionable insights.
        """
        error_str = str(error).lower()
        
        if isinstance(error, NoCredentialsError):
            return {
                "category": "credentials",
                "severity": "high",
                "message": "AWS credentials not found or invalid",
                "actions": [
                    "Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY",
                    "Verify IAM role permissions",
                    "Check AWS CLI configuration",
                    "Validate environment variables"
                ],
                "retry_recommended": False,
                "escalation_required": True
            }
        
        elif isinstance(error, EndpointConnectionError):
            return {
                "category": "network",
                "severity": "medium",
                "message": "Cannot connect to AWS service endpoint",
                "actions": [
                    "Check internet connectivity",
                    "Verify AWS region configuration",
                    "Check firewall/proxy settings",
                    "Validate VPC/security group rules"
                ],
                "retry_recommended": True,
                "escalation_required": False
            }
        
        elif "could not connect to the endpoint url" in error_str:
            return {
                "category": "endpoint",
                "severity": "medium", 
                "message": "AWS endpoint unreachable",
                "actions": [
                    "Check AWS service status",
                    "Verify region configuration",
                    "Check DNS resolution",
                    "Validate endpoint URL format"
                ],
                "retry_recommended": True,
                "escalation_required": False
            }
        
        elif "timeout" in error_str:
            return {
                "category": "timeout",
                "severity": "low",
                "message": "Request timeout to AWS service",
                "actions": [
                    "Increase timeout values",
                    "Check network latency",
                    "Implement circuit breaker",
                    "Consider regional failover"
                ],
                "retry_recommended": True,
                "escalation_required": False
            }
        
        elif isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', 'Unknown')
            return {
                "category": "client_error",
                "severity": "medium",
                "message": f"AWS client error: {error_code}",
                "error_code": error_code,
                "actions": [
                    "Check API permissions",
                    "Validate request parameters",
                    "Review AWS service limits",
                    "Check resource existence"
                ],
                "retry_recommended": error_code in ['Throttling', 'ServiceUnavailable'],
                "escalation_required": error_code in ['AccessDenied', 'InvalidUserID.NotFound']
            }
        
        else:
            return {
                "category": "unknown",
                "severity": "medium",
                "message": f"Unknown AWS error: {error}",
                "actions": ["Check AWS CloudTrail logs", "Contact AWS support"],
                "retry_recommended": True,
                "escalation_required": False
            }

class CircuitBreaker:
    """
    Circuit breaker pattern for handling service failures.
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable):
        """Decorator to apply circuit breaker pattern."""
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception(f"Circuit breaker OPEN. Service unavailable.")
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

class RetryHandler:
    """
    Advanced retry logic with exponential backoff and jitter.
    """
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on: tuple = (Exception,)
    ):
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for exponential backoff
            jitter: Add randomness to delay to prevent thundering herd
            retry_on: Tuple of exceptions to retry on
        """
        import random
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
                    
            except retry_on as e:
                last_exception = e
                
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                    break
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                
                # Add jitter to prevent thundering herd
                if jitter:
                    delay *= (0.5 + random.random() * 0.5)
                
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception

class SQSErrorHandler:
    """
    Specialized error handling for SQS operations.
    """
    
    def __init__(self, queue_url: str, region: str = 'us-east-1'):
        self.queue_url = queue_url
        self.region = region
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=(ClientError, EndpointConnectionError, NoCredentialsError)
        )
    
    @CircuitBreaker(failure_threshold=3, recovery_timeout=30)
    async def send_message_with_retry(self, message_body: str, message_attributes: Dict = None):
        """
        Send SQS message with comprehensive error handling.
        """
        async def _send_message():
            try:
                sqs = boto3.client('sqs', region_name=self.region)
                
                params = {
                    'QueueUrl': self.queue_url,
                    'MessageBody': message_body
                }
                
                if message_attributes:
                    params['MessageAttributes'] = message_attributes
                
                response = sqs.send_message(**params)
                logger.info(f"✅ Message sent successfully: {response['MessageId']}")
                return response
                
            except Exception as e:
                error_info = ProductionErrorHandler.categorize_aws_error(e)
                logger.error(f"❌ SQS send failed: {error_info}")
                
                # Log detailed error information
                self._log_error_details(e, error_info)
                
                if not error_info['retry_recommended']:
                    raise e
                
                # Re-raise for retry logic
                raise e
        
        return await RetryHandler.retry_with_backoff(
            _send_message,
            max_retries=3,
            base_delay=1.0,
            retry_on=(ClientError, EndpointConnectionError)
        )
    
    async def receive_messages_with_retry(self, max_messages: int = 10, wait_time: int = 20):
        """
        Receive SQS messages with error handling.
        """
        async def _receive_messages():
            try:
                sqs = boto3.client('sqs', region_name=self.region)
                
                response = sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time,
                    MessageAttributeNames=['All']
                )
                
                messages = response.get('Messages', [])
                logger.info(f"✅ Received {len(messages)} messages from SQS")
                return messages
                
            except Exception as e:
                error_info = ProductionErrorHandler.categorize_aws_error(e)
                logger.error(f"❌ SQS receive failed: {error_info}")
                
                self._log_error_details(e, error_info)
                raise e
        
        return await RetryHandler.retry_with_backoff(
            _receive_messages,
            max_retries=2,
            base_delay=2.0,
            retry_on=(ClientError, EndpointConnectionError)
        )
    
    def _log_error_details(self, error: Exception, error_info: Dict[str, Any]):
        """Log detailed error information for debugging."""
        logger.error(f"SQS Error Details:")
        logger.error(f"  Category: {error_info['category']}")
        logger.error(f"  Severity: {error_info['severity']}")
        logger.error(f"  Message: {error_info['message']}")
        logger.error(f"  Queue URL: {self.queue_url}")
        logger.error(f"  Region: {self.region}")
        logger.error(f"  Suggested Actions: {error_info['actions']}")
        
        if error_info['escalation_required']:
            logger.critical(f"🚨 ESCALATION REQUIRED for SQS error: {error}")

# Example usage in your test file
async def test_sqs_with_production_error_handling():
    """Example of using production error handling with SQS."""
    
    queue_url = "https://sqs.us-east-1.amazonaws.com/720375049643/new_visitor_signup.fifo"
    sqs_handler = SQSErrorHandler(queue_url)
    
    try:
        # Test message sending with retry and circuit breaker
        test_message = json.dumps({
            "visitor_id": "test-123",
            "event_type": "new_visitor_signup",
            "timestamp": datetime.now().isoformat()
        })
        
        response = await sqs_handler.send_message_with_retry(test_message)
        logger.info(f"✅ Test message sent: {response}")
        
    except Exception as e:
        error_info = ProductionErrorHandler.categorize_aws_error(e)
        logger.error(f"❌ Production test failed: {error_info}")
        
        # In production, you might want to:
        # 1. Send alert to monitoring system
        # 2. Fall back to alternative queue
        # 3. Store message for later retry
        # 4. Update health check status