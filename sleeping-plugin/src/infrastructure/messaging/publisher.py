"""
Event Publisher - RabbitMQ
Publica eventos para o VMS Hub
"""
import pika
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PublisherConfig:
    host: str
    port: int
    username: str
    password: str
    exchange: str

class EventPublisher:
    def __init__(self, config: PublisherConfig):
        self.config = config
        self.connection = None
        self.channel = None
    
    def connect(self):
        credentials = pika.PlainCredentials(self.config.username, self.config.password)
        parameters = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            credentials=credentials
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        self.channel.exchange_declare(
            exchange=self.config.exchange,
            exchange_type='topic',
            durable=True
        )
        
        logger.info(f"Publisher conectado: {self.config.host}")
    
    def publish(self, routing_key: str, event: dict):
        if not self.channel:
            raise RuntimeError("Publisher não conectado")
        
        self.channel.basic_publish(
            exchange=self.config.exchange,
            routing_key=routing_key,
            body=json.dumps(event),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        logger.info(f"Evento publicado: {routing_key}")
    
    def close(self):
        if self.connection:
            self.connection.close()
        logger.info("Publisher fechado")
