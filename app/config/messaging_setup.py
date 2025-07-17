"""Setup messaging infrastructure for REQ-0"""

from app.infastructure.aws.sqs_client import SQSClient
from app.config.settings import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

async def setup_member_service_integration():
    """Setup SQS subscription to member service SNS topic"""
    sqs_client = SQSClient()
    
    # Subscribe AI notes queue to member service topic
    try:
        result = await sqs_client.subscribe_to_topic(
            topic_arn=settings.MEMBER_SERVICE_TOPIC_ARN,
            queue_name='ai_notes',
            filter_policy={
                'event_type': ['new_visitor', 'visitor_updated', 'follow_up_required']
            }
        )
        
        logger.info(f"Successfully subscribed to member service topic: {result['subscription_arn']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to setup member service integration: {str(e)}")
        raise