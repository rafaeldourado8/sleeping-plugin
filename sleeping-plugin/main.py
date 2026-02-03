"""
VigilEye Plugin - Main Entry Point
Plugin de detecção de sonolência para VMS Hub
"""
import os
import logging
from dotenv import load_dotenv
from src.infrastructure.messaging.consumer import EventConsumer, RabbitMQConfig
from src.infrastructure.messaging.publisher import EventPublisher, PublisherConfig
from src.infrastructure.ml.drowsiness_detector import DrowsinessDetector
from src.application.handlers.camera_handler import CameraEventHandler
from src.presentation.api import start_api

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Carrega configurações do ambiente"""
    load_dotenv()
    
    routing_keys = os.getenv("RABBITMQ_ROUTING_KEYS", "").split(",")
    routing_keys = [k.strip() for k in routing_keys if k.strip()]
    
    rabbitmq_config = RabbitMQConfig(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        username=os.getenv("RABBITMQ_USER"),
        password=os.getenv("RABBITMQ_PASS"),
        exchange=os.getenv("RABBITMQ_EXCHANGE"),
        queue=os.getenv("RABBITMQ_QUEUE"),
        routing_keys=routing_keys
    )
    
    publisher_config = PublisherConfig(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        username=os.getenv("RABBITMQ_USER"),
        password=os.getenv("RABBITMQ_PASS"),
        exchange=os.getenv("RABBITMQ_EXCHANGE")
    )
    
    model_path = os.getenv("MODEL_PATH", "face_landmarker.task")
    ear_threshold = float(os.getenv("EAR_THRESHOLD", "0.2"))
    consec_frames = int(os.getenv("CONSEC_FRAMES", "20"))
    
    return rabbitmq_config, publisher_config, model_path, ear_threshold, consec_frames

def main():
    logger.info("=" * 60)
    logger.info("VigilEye Plugin - Driver Drowsiness Detection")
    logger.info("=" * 60)
    
    rabbitmq_config, publisher_config, model_path, ear_threshold, consec_frames = load_config()
    
    detector = DrowsinessDetector(model_path, ear_threshold, consec_frames)
    logger.info(f"Detector inicializado: EAR={ear_threshold}, Frames={consec_frames}")
    
    publisher = EventPublisher(publisher_config)
    publisher.connect()
    
    handler = CameraEventHandler(detector, publisher, consec_frames)
    
    api_port = int(os.getenv("API_PORT", "8000"))
    start_api(handler, api_port)
    logger.info(f"API iniciada: http://0.0.0.0:{api_port}")
    
    consumer = EventConsumer(rabbitmq_config)
    consumer.register_handler("camera.added", handler.handle_camera_added)
    consumer.register_handler("camera.removed", handler.handle_camera_removed)
    
    consumer.connect()
    
    logger.info("Plugin pronto. Aguardando eventos...")
    
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Encerrando plugin...")
        consumer.stop()
        publisher.close()
        logger.info("Plugin encerrado")

if __name__ == "__main__":
    main()
