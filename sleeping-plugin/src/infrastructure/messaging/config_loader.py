"""
Configuration Loader
Carrega configurações de variáveis de ambiente
"""
import os
from typing import List
from .consumer import RabbitMQConfig

def load_rabbitmq_config() -> RabbitMQConfig:
    """Carrega configuração do RabbitMQ de variáveis de ambiente"""
    routing_keys_str = os.getenv("RABBITMQ_ROUTING_KEYS", "")
    routing_keys = [key.strip() for key in routing_keys_str.split(",") if key.strip()]
    
    return RabbitMQConfig(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        username=os.getenv("RABBITMQ_USER"),
        password=os.getenv("RABBITMQ_PASS"),
        exchange=os.getenv("RABBITMQ_EXCHANGE"),
        queue=os.getenv("RABBITMQ_QUEUE"),
        routing_keys=routing_keys
    )
