from typing import Dict, Any
import boto3
import json

class MessagingService:
    def __init__(self, region_name: str):
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.queue_urls = {}

    async def publish(self, queue_name: str, message: Dict[str, Any]):
        """Publish message to SQS queue"""
        # Get or create queue URL if not cached
        if queue_name not in self.queue_urls:
            response = self.sqs.get_queue_url(QueueName=queue_name)
            self.queue_urls[queue_name] = response['QueueUrl']
        
        # Send message to SQS queue
        self.sqs.send_message(
            QueueUrl=self.queue_urls[queue_name],
            MessageBody=json.dumps(message)
        )
