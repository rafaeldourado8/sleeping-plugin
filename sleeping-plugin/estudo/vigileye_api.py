"""
VigilEye API Server - Driver Drowsiness Detection with MediaMTX Support
Versão: 2.0 - API REST + RTSP Streams
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import threading
import time
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configurações globais
CAMERAS = {}  # {camera_id: CameraProcessor}
ALERTS = []   # Histórico de alertas
MAX_ALERTS = 1000

class CameraProcessor:
    def __init__(self, camera_id, rtsp_url):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.running = False
        self.thread = None
        self.last_ear = 0.0
        self.alert_active = False
        self.frame_counter = 0
        self.total_alerts = 0
        self.last_alert_time = None
        
        # MediaPipe setup
        base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
        options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
        self.detector = vision.FaceLandmarker.create_from_options(options)
        
        # Eye landmarks
        self.left_eye = [362, 385, 387, 263, 373, 380]
        self.right_eye = [33, 160, 158, 133, 153, 144]
        
        # Thresholds
        self.EAR_THRESHOLD = 0.2
        self.CONSEC_FRAMES = 20
    
    def euclidean_distance(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    def calculate_ear(self, eye_landmarks, landmarks):
        p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in eye_landmarks]
        vertical1 = self.euclidean_distance(p2, p6)
        vertical2 = self.euclidean_distance(p3, p5)
        horizontal = self.euclidean_distance(p1, p4)
        return (vertical1 + vertical2) / (2.0 * horizontal)
    
    def process_stream(self):
        cap = cv2.VideoCapture(self.rtsp_url)
        
        if not cap.isOpened():
            print(f"[ERROR] Não foi possível conectar à câmera {self.camera_id}")
            self.running = False
            return
        
        print(f"[INFO] Câmera {self.camera_id} conectada: {self.rtsp_url}")
        
        while self.running:
            success, frame = cap.read()
            if not success:
                time.sleep(0.1)
                continue
            
            # Processa frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            results = self.detector.detect(mp_image)
            
            if results.face_landmarks:
                for face_landmarks in results.face_landmarks:
                    right_ear = self.calculate_ear(self.right_eye, face_landmarks)
                    left_ear = self.calculate_ear(self.left_eye, face_landmarks)
                    self.last_ear = (right_ear + left_ear) / 2.0
                    
                    if self.last_ear < self.EAR_THRESHOLD:
                        self.frame_counter += 1
                        if self.frame_counter >= self.CONSEC_FRAMES:
                            if not self.alert_active:
                                self.trigger_alert()
                    else:
                        self.frame_counter = 0
                        self.alert_active = False
            
            time.sleep(0.033)  # ~30 FPS
        
        cap.release()
        print(f"[INFO] Câmera {self.camera_id} desconectada")
    
    def trigger_alert(self):
        self.alert_active = True
        self.total_alerts += 1
        self.last_alert_time = datetime.now()
        
        alert = {
            'camera_id': self.camera_id,
            'timestamp': self.last_alert_time.isoformat(),
            'ear_value': round(self.last_ear, 3),
            'alert_number': self.total_alerts
        }
        
        ALERTS.append(alert)
        if len(ALERTS) > MAX_ALERTS:
            ALERTS.pop(0)
        
        print(f"[ALERT] Câmera {self.camera_id} - Sonolência detectada! EAR: {self.last_ear:.3f}")
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.process_stream, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def get_status(self):
        return {
            'camera_id': self.camera_id,
            'rtsp_url': self.rtsp_url,
            'running': self.running,
            'last_ear': round(self.last_ear, 3),
            'alert_active': self.alert_active,
            'total_alerts': self.total_alerts,
            'last_alert_time': self.last_alert_time.isoformat() if self.last_alert_time else None
        }

# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica status da API"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'active_cameras': len([c for c in CAMERAS.values() if c.running]),
        'total_cameras': len(CAMERAS)
    })

@app.route('/api/cameras', methods=['GET'])
def list_cameras():
    """Lista todas as câmeras"""
    cameras_status = [cam.get_status() for cam in CAMERAS.values()]
    return jsonify({
        'cameras': cameras_status,
        'count': len(cameras_status)
    })

@app.route('/api/cameras', methods=['POST'])
def add_camera():
    """
    Adiciona nova câmera
    Body: {
        "camera_id": "cam01",
        "rtsp_url": "rtsp://localhost:8554/stream1"
    }
    """
    data = request.json
    camera_id = data.get('camera_id')
    rtsp_url = data.get('rtsp_url')
    
    if not camera_id or not rtsp_url:
        return jsonify({'error': 'camera_id e rtsp_url são obrigatórios'}), 400
    
    if camera_id in CAMERAS:
        return jsonify({'error': f'Câmera {camera_id} já existe'}), 409
    
    # Cria e inicia processador
    processor = CameraProcessor(camera_id, rtsp_url)
    processor.start()
    CAMERAS[camera_id] = processor
    
    return jsonify({
        'message': f'Câmera {camera_id} adicionada com sucesso',
        'camera': processor.get_status()
    }), 201

@app.route('/api/cameras/<camera_id>', methods=['GET'])
def get_camera(camera_id):
    """Obtém status de uma câmera específica"""
    if camera_id not in CAMERAS:
        return jsonify({'error': f'Câmera {camera_id} não encontrada'}), 404
    
    return jsonify(CAMERAS[camera_id].get_status())

@app.route('/api/cameras/<camera_id>', methods=['DELETE'])
def remove_camera(camera_id):
    """Remove uma câmera"""
    if camera_id not in CAMERAS:
        return jsonify({'error': f'Câmera {camera_id} não encontrada'}), 404
    
    processor = CAMERAS[camera_id]
    processor.stop()
    del CAMERAS[camera_id]
    
    return jsonify({'message': f'Câmera {camera_id} removida com sucesso'})

@app.route('/api/cameras/<camera_id>/start', methods=['POST'])
def start_camera(camera_id):
    """Inicia processamento de uma câmera"""
    if camera_id not in CAMERAS:
        return jsonify({'error': f'Câmera {camera_id} não encontrada'}), 404
    
    CAMERAS[camera_id].start()
    return jsonify({'message': f'Câmera {camera_id} iniciada'})

@app.route('/api/cameras/<camera_id>/stop', methods=['POST'])
def stop_camera(camera_id):
    """Para processamento de uma câmera"""
    if camera_id not in CAMERAS:
        return jsonify({'error': f'Câmera {camera_id} não encontrada'}), 404
    
    CAMERAS[camera_id].stop()
    return jsonify({'message': f'Câmera {camera_id} parada'})

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    Lista alertas
    Query params:
        - camera_id: filtrar por câmera
        - limit: número máximo de alertas (padrão: 100)
    """
    camera_id = request.args.get('camera_id')
    limit = int(request.args.get('limit', 100))
    
    filtered_alerts = ALERTS
    if camera_id:
        filtered_alerts = [a for a in ALERTS if a['camera_id'] == camera_id]
    
    return jsonify({
        'alerts': filtered_alerts[-limit:],
        'count': len(filtered_alerts)
    })

@app.route('/api/alerts', methods=['DELETE'])
def clear_alerts():
    """Limpa histórico de alertas"""
    ALERTS.clear()
    return jsonify({'message': 'Histórico de alertas limpo'})

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Estatísticas gerais do sistema"""
    total_alerts = len(ALERTS)
    cameras_with_alerts = len(set(a['camera_id'] for a in ALERTS))
    
    stats = {
        'total_cameras': len(CAMERAS),
        'active_cameras': len([c for c in CAMERAS.values() if c.running]),
        'total_alerts': total_alerts,
        'cameras_with_alerts': cameras_with_alerts,
        'alerts_by_camera': {}
    }
    
    for cam_id, processor in CAMERAS.items():
        stats['alerts_by_camera'][cam_id] = processor.total_alerts
    
    return jsonify(stats)

# ==================== MAIN ====================

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         VigilEye API Server v2.0                      ║
    ║    Driver Drowsiness Detection with MediaMTX         ║
    ╚═══════════════════════════════════════════════════════╝
    
    API Endpoints:
    - GET    /api/health              - Status da API
    - GET    /api/cameras             - Listar câmeras
    - POST   /api/cameras             - Adicionar câmera
    - GET    /api/cameras/<id>        - Status da câmera
    - DELETE /api/cameras/<id>        - Remover câmera
    - POST   /api/cameras/<id>/start  - Iniciar câmera
    - POST   /api/cameras/<id>/stop   - Parar câmera
    - GET    /api/alerts              - Listar alertas
    - DELETE /api/alerts              - Limpar alertas
    - GET    /api/stats               - Estatísticas
    
    Servidor rodando em: http://0.0.0.0:5000
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
