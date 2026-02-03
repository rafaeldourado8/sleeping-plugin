"""
Event Consumer - RabbitMQ
Consome eventos do VMS Hub
"""
import pika
import json
import logging
from typing import Callable
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class RabbitMQConfig:
    host: str
    port: int
    username: str
    password: str
    exchange: str
    queue: str
    routing_keys: list[str]

class EventConsumer:
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self.connection = None
        self.channel = None
        self.handlers = {}
    
    def connect(self):
        credentials = pika.PlainCredentials(self.config.username, self.config.password)
        parameters = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        self.channel.exchange_declare(
            exchange=self.config.exchange,
            exchange_type='topic',
            durable=True
        )
        
        self.channel.queue_declare(queue=self.config.queue, durable=True)
        
        for routing_key in self.config.routing_keys:
            self.channel.queue_bind(
                exchange=self.config.exchange,
                queue=self.config.queue,
                routing_key=routing_key
            )
        
        logger.info(f"Conectado: {self.config.host}:{self.config.port}")
    
    def register_handler(self, event_type: str, handler: Callable):
        self.handlers[event_type] = handler
        logger.info(f"Handler: {event_type}")
    
    def _on_message(self, channel, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            event_type = message.get('event_type')
            
            logger.info(f"Evento: {event_type}")
            
            handler = self.handlers.get(event_type)
            if handler:
                handler(message)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.warning(f"Sem handler: {event_type}")
                channel.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            logger.error(f"Erro: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.config.queue,
            on_message_callback=self._on_message,
            auto_ack=False
        )
        
        logger.info("Consumindo eventos...")
        self.channel.start_consuming()
    
    def stop(self):
        if self.channel:
            self.channel.stop_consuming()
        if self.connection:
            self.connection.close()
        logger.info("Consumer parado")
