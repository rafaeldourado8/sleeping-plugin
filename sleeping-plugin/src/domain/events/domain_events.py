"""
Domain Events
Eventos publicados pelo plugin
"""
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class DomainEvent:
    """Base para eventos de domínio"""
    event_type: str
    timestamp: str
    source: str = "vigileye-plugin"
    
    def to_dict(self):
        return asdict(self)

@dataclass
class DrowsinessDetectedEvent(DomainEvent):
    """Evento: Sonolência detectada"""
    camera_id: str
    ear_value: float
    severity: str
    duration_ms: int
    
    def __init__(self, camera_id: str, ear_value: float, severity: str, duration_ms: int):
        super().__init__(
            event_type="drowsiness.detected",
            timestamp=datetime.now().isoformat()
        )
        self.camera_id = camera_id
        self.ear_value = ear_value
        self.severity = severity
        self.duration_ms = duration_ms

@dataclass
class AlertTriggeredEvent(DomainEvent):
    """Evento: Alerta crítico disparado"""
    camera_id: str
    alert_type: str
    priority: str
    message: str
    
    def __init__(self, camera_id: str, alert_type: str, priority: str, message: str):
        super().__init__(
            event_type="alert.triggered",
            timestamp=datetime.now().isoformat()
        )
        self.camera_id = camera_id
        self.alert_type = alert_type
        self.priority = priority
        self.message = message
