"""
Event Handlers
Processa eventos recebidos do VMS Hub
"""
import logging
from typing import Dict
from ..domain.entities.detection_session import DetectionSession
from ..domain.events.domain_events import DrowsinessDetectedEvent, AlertTriggeredEvent
from ..infrastructure.video.stream_processor import StreamProcessor
from ..infrastructure.ml.drowsiness_detector import DrowsinessDetector
from ..infrastructure.messaging.publisher import EventPublisher

logger = logging.getLogger(__name__)

class CameraEventHandler:
    def __init__(self, detector: DrowsinessDetector, publisher: EventPublisher, consec_frames: int):
        self.detector = detector
        self.publisher = publisher
        self.consec_frames = consec_frames
        self.sessions: Dict[str, DetectionSession] = {}
        self.processors: Dict[str, StreamProcessor] = {}
    
    def handle_camera_added(self, message: dict):
        """Handler: camera.added"""
        data = message.get('data', {})
        camera_id = data.get('camera_id')
        rtsp_url = data.get('rtsp_url')
        
        if not camera_id or not rtsp_url:
            logger.error("Evento inválido: faltam camera_id ou rtsp_url")
            return
        
        logger.info(f"Adicionando câmera: {camera_id}")
        
        from datetime import datetime
        session = DetectionSession(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            started_at=datetime.now()
        )
        self.sessions[camera_id] = session
        
        processor = StreamProcessor(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            frame_callback=self._process_frame
        )
        self.processors[camera_id] = processor
        processor.start()
    
    def handle_camera_removed(self, message: dict):
        """Handler: camera.removed"""
        data = message.get('data', {})
        camera_id = data.get('camera_id')
        
        if not camera_id:
            logger.error("Evento inválido: falta camera_id")
            return
        
        logger.info(f"Removendo câmera: {camera_id}")
        
        if camera_id in self.processors:
            self.processors[camera_id].stop()
            del self.processors[camera_id]
        
        if camera_id in self.sessions:
            self.sessions[camera_id].stop()
            del self.sessions[camera_id]
    
    def _process_frame(self, camera_id: str, frame):
        """Processa frame e detecta sonolência"""
        session = self.sessions.get(camera_id)
        if not session or not session.is_active:
            return
        
        ear_value = self.detector.detect(frame)
        if ear_value is None:
            return
        
        session.update_ear(ear_value)
        
        if self.detector.is_drowsy(ear_value):
            session.increment_frame_counter()
            
            if session.frame_counter >= self.consec_frames:
                self._trigger_alert(session)
        else:
            session.reset_frame_counter()
    
    def _trigger_alert(self, session: DetectionSession):
        """Dispara alerta de sonolência"""
        session.trigger_alert()
        
        duration_ms = session.frame_counter * 33
        
        drowsiness_event = DrowsinessDetectedEvent(
            camera_id=session.camera_id,
            ear_value=round(session.last_ear, 3),
            severity="high",
            duration_ms=duration_ms
        )
        
        alert_event = AlertTriggeredEvent(
            camera_id=session.camera_id,
            alert_type="drowsiness",
            priority="critical",
            message=f"Sonolência detectada - EAR: {session.last_ear:.3f}"
        )
        
        self.publisher.publish("drowsiness.detected", drowsiness_event.to_dict())
        self.publisher.publish("alert.triggered", alert_event.to_dict())
        
        logger.warning(f"ALERTA: {session.camera_id} - EAR: {session.last_ear:.3f}")
