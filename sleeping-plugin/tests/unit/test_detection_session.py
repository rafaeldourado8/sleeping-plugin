"""
Testes Unitários - DetectionSession
"""
import pytest
from datetime import datetime
from src.domain.entities.detection_session import DetectionSession

def test_create_detection_session():
    session = DetectionSession(
        camera_id="cam-001",
        rtsp_url="rtsp://localhost:8554/stream1",
        started_at=datetime.now()
    )
    
    assert session.camera_id == "cam-001"
    assert session.is_active == True
    assert session.total_alerts == 0

def test_update_ear():
    session = DetectionSession(
        camera_id="cam-001",
        rtsp_url="rtsp://localhost:8554/stream1",
        started_at=datetime.now()
    )
    
    session.update_ear(0.25)
    assert session.last_ear == 0.25

def test_increment_frame_counter():
    session = DetectionSession(
        camera_id="cam-001",
        rtsp_url="rtsp://localhost:8554/stream1",
        started_at=datetime.now()
    )
    
    session.increment_frame_counter()
    session.increment_frame_counter()
    assert session.frame_counter == 2

def test_reset_frame_counter():
    session = DetectionSession(
        camera_id="cam-001",
        rtsp_url="rtsp://localhost:8554/stream1",
        started_at=datetime.now()
    )
    
    session.increment_frame_counter()
    session.reset_frame_counter()
    assert session.frame_counter == 0

def test_trigger_alert():
    session = DetectionSession(
        camera_id="cam-001",
        rtsp_url="rtsp://localhost:8554/stream1",
        started_at=datetime.now()
    )
    
    session.trigger_alert()
    assert session.total_alerts == 1
    assert session.last_alert_at is not None

def test_stop_session():
    session = DetectionSession(
        camera_id="cam-001",
        rtsp_url="rtsp://localhost:8554/stream1",
        started_at=datetime.now()
    )
    
    session.stop()
    assert session.is_active == False
