"""
Stream Processor
Processa stream RTSP de uma câmera
"""
import cv2
import threading
import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class StreamProcessor:
    def __init__(self, camera_id: str, rtsp_url: str, frame_callback: Callable):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.frame_callback = frame_callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.cap: Optional[cv2.VideoCapture] = None
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_stream, daemon=True)
        self.thread.start()
        logger.info(f"Stream iniciado: {self.camera_id}")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        logger.info(f"Stream parado: {self.camera_id}")
    
    def _process_stream(self):
        self.cap = cv2.VideoCapture(self.rtsp_url)
        
        if not self.cap.isOpened():
            logger.error(f"Erro ao conectar: {self.camera_id}")
            self.running = False
            return
        
        logger.info(f"Conectado: {self.camera_id}")
        
        while self.running:
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.1)
                continue
            
            try:
                self.frame_callback(self.camera_id, frame)
            except Exception as e:
                logger.error(f"Erro no callback: {e}")
            
            time.sleep(0.033)
        
        self.cap.release()
