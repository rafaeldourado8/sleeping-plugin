"""
Testes Unitários - DetectionSession (unittest)
"""
import unittest
from datetime import datetime
from src.domain.entities.detection_session import DetectionSession

class TestDetectionSession(unittest.TestCase):
    
    def test_create_detection_session(self):
        session = DetectionSession(
            camera_id="cam-001",
            rtsp_url="rtsp://localhost:8554/stream1",
            started_at=datetime.now()
        )
        
        self.assertEqual(session.camera_id, "cam-001")
        self.assertTrue(session.is_active)
        self.assertEqual(session.total_alerts, 0)
    
    def test_update_ear(self):
        session = DetectionSession(
            camera_id="cam-001",
            rtsp_url="rtsp://localhost:8554/stream1",
            started_at=datetime.now()
        )
        
        session.update_ear(0.25)
        self.assertEqual(session.last_ear, 0.25)
    
    def test_increment_frame_counter(self):
        session = DetectionSession(
            camera_id="cam-001",
            rtsp_url="rtsp://localhost:8554/stream1",
            started_at=datetime.now()
        )
        
        session.increment_frame_counter()
        session.increment_frame_counter()
        self.assertEqual(session.frame_counter, 2)
    
    def test_reset_frame_counter(self):
        session = DetectionSession(
            camera_id="cam-001",
            rtsp_url="rtsp://localhost:8554/stream1",
            started_at=datetime.now()
        )
        
        session.increment_frame_counter()
        session.reset_frame_counter()
        self.assertEqual(session.frame_counter, 0)
    
    def test_trigger_alert(self):
        session = DetectionSession(
            camera_id="cam-001",
            rtsp_url="rtsp://localhost:8554/stream1",
            started_at=datetime.now()
        )
        
        session.trigger_alert()
        self.assertEqual(session.total_alerts, 1)
        self.assertIsNotNone(session.last_alert_at)
    
    def test_stop_session(self):
        session = DetectionSession(
            camera_id="cam-001",
            rtsp_url="rtsp://localhost:8554/stream1",
            started_at=datetime.now()
        )
        
        session.stop()
        self.assertFalse(session.is_active)

if __name__ == '__main__':
    unittest.main()
