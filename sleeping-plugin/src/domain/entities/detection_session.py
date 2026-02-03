"""
Domain Entity: DetectionSession
Representa uma sessão de detecção de sonolência para uma câmera
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DetectionSession:
    camera_id: str
    rtsp_url: str
    started_at: datetime
    last_ear: float = 0.0
    frame_counter: int = 0
    total_alerts: int = 0
    is_active: bool = True
    last_alert_at: Optional[datetime] = None
    
    def update_ear(self, ear_value: float):
        """Atualiza valor do EAR"""
        self.last_ear = ear_value
    
    def increment_frame_counter(self):
        """Incrementa contador de frames com olhos fechados"""
        self.frame_counter += 1
    
    def reset_frame_counter(self):
        """Reseta contador de frames"""
        self.frame_counter = 0
    
    def trigger_alert(self):
        """Registra um alerta"""
        self.total_alerts += 1
        self.last_alert_at = datetime.now()
    
    def stop(self):
        """Para a sessão"""
        self.is_active = False
