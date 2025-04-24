from typing import Dict, Any
from kafka import KafkaProducer, KafkaConsumer
import json

class MessageQueue:
    def __init__(self, kafka_servers: list):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.consumers = {}

    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message to Kafka topic"""
        try:
            future = self.producer.send(topic, message)
            await future
        except Exception as e:
            raise Exception(f"Error publishing message: {str(e)}")

    async def subscribe(self, topic: str, callback):
        """Subscribe to Kafka topic"""
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.kafka_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        self.consumers[topic] = consumer

        async for message in consumer:
            await callback(message.value)

    async def close(self):
        """Close all connections"""
        self.producer.close()
        for consumer in self.consumers.values():
            consumer.close() 