# VigilEye Plugin - Documentação Completa

## Visão Geral

Plugin event-driven para detecção de sonolência em motoristas, integrado via RabbitMQ com VMS Hub.

## Arquitetura

```
VMS Hub (CRUD) → RabbitMQ → VigilEye Plugin → RabbitMQ → VMS Hub (Alertas)
```

### Camadas (DDD)

1. **Domain**: Entidades e eventos de negócio
2. **Application**: Handlers e orquestração
3. **Infrastructure**: Implementações técnicas (RabbitMQ, MediaPipe, OpenCV)

## Estrutura do Projeto

```
vigileye-plugin/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   └── detection_session.py      # Sessão de detecção
│   │   └── events/
│   │       └── domain_events.py           # Eventos publicados
│   │
│   ├── application/
│   │   └── handlers/
│   │       └── camera_handler.py          # Processa eventos
│   │
│   └── infrastructure/
│       ├── messaging/
│       │   ├── consumer.py                # Consome eventos
│       │   └── publisher.py               # Publica eventos
│       ├── ml/
│       │   └── drowsiness_detector.py     # MediaPipe + EAR
│       └── video/
│           └── stream_processor.py        # Processa RTSP
│
├── tests/
│   └── unit/
│       └── test_detection_session.py
│
├── main.py                                # Entry point
├── requirements.txt
└── .env.example
```

## Fluxo de Funcionamento

### 1. Inicialização
```python
# main.py carrega configurações
# Conecta ao RabbitMQ (consumer + publisher)
# Registra handlers para eventos
# Inicia consumo
```

### 2. Evento: camera.added
```
VMS Hub publica → RabbitMQ → Plugin consome
                                    ↓
                          CameraEventHandler.handle_camera_added()
                                    ↓
                          Cria DetectionSession
                                    ↓
                          Inicia StreamProcessor (thread)
                                    ↓
                          Processa frames continuamente
```

### 3. Processamento de Frame
```
StreamProcessor captura frame → callback
                                    ↓
                          DrowsinessDetector.detect(frame)
                                    ↓
                          Calcula EAR (MediaPipe)
                                    ↓
                          EAR < 0.2? → Incrementa contador
                                    ↓
                          Contador >= 20? → Dispara alerta
```

### 4. Alerta Disparado
```
CameraEventHandler._trigger_alert()
                ↓
    Cria DrowsinessDetectedEvent
                ↓
    Cria AlertTriggeredEvent
                ↓
    Publisher.publish() → RabbitMQ → VMS Hub
```

### 5. Evento: camera.removed
```
VMS Hub publica → RabbitMQ → Plugin consome
                                    ↓
                          CameraEventHandler.handle_camera_removed()
                                    ↓
                          Para StreamProcessor
                                    ↓
                          Remove DetectionSession
```

## Componentes Principais

### DetectionSession (Domain Entity)
```python
# Representa sessão de detecção para uma câmera
- camera_id: Identificador
- rtsp_url: URL do stream
- last_ear: Último valor EAR calculado
- frame_counter: Frames consecutivos com olhos fechados
- total_alerts: Total de alertas disparados
```

### DrowsinessDetector (Infrastructure)
```python
# Detecta sonolência usando MediaPipe
- detect(frame): Calcula EAR de um frame
- is_drowsy(ear): Verifica se EAR indica sonolência
```

### StreamProcessor (Infrastructure)
```python
# Processa stream RTSP em thread separada
- start(): Inicia captura
- stop(): Para captura
- _process_stream(): Loop de captura (30 FPS)
```

### EventConsumer (Infrastructure)
```python
# Consome eventos do RabbitMQ
- connect(): Conecta ao broker
- register_handler(): Registra handler para evento
- start_consuming(): Inicia consumo (blocking)
```

### EventPublisher (Infrastructure)
```python
# Publica eventos para RabbitMQ
- connect(): Conecta ao broker
- publish(routing_key, event): Publica evento
```

### CameraEventHandler (Application)
```python
# Orquestra processamento de eventos
- handle_camera_added(): Inicia detecção
- handle_camera_removed(): Para detecção
- _process_frame(): Processa cada frame
- _trigger_alert(): Dispara alerta
```

## Eventos

### Input (Consome)

**camera.added**
```json
{
  "event_type": "camera.added",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "camera_id": "cam-001",
    "rtsp_url": "rtsp://localhost:8554/stream1"
  }
}
```

**camera.removed**
```json
{
  "event_type": "camera.removed",
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "camera_id": "cam-001"
  }
}
```

### Output (Publica)

**drowsiness.detected**
```json
{
  "event_type": "drowsiness.detected",
  "timestamp": "2024-01-15T10:31:45Z",
  "source": "vigileye-plugin",
  "camera_id": "cam-001",
  "ear_value": 0.15,
  "severity": "high",
  "duration_ms": 850
}
```

**alert.triggered**
```json
{
  "event_type": "alert.triggered",
  "timestamp": "2024-01-15T10:31:45Z",
  "source": "vigileye-plugin",
  "camera_id": "cam-001",
  "alert_type": "drowsiness",
  "priority": "critical",
  "message": "Sonolência detectada - EAR: 0.150"
}
```

## Configuração

### Variáveis de Ambiente (.env)
```bash
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_EXCHANGE=vms.events
RABBITMQ_QUEUE=vigileye.queue
RABBITMQ_ROUTING_KEYS=camera.added,camera.removed

# Detecção
MODEL_PATH=face_landmarker.task
EAR_THRESHOLD=0.2
CONSEC_FRAMES=20
```

## Instalação

```bash
# 1. Clonar repositório
cd vigileye-plugin

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Baixar modelo MediaPipe
# https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas configurações

# 5. Executar
python main.py
```

## Testes

```bash
# Testes unitários
pytest tests/unit/

# Testes com cobertura
pytest --cov=src tests/
```

## Princípios SOLID Aplicados

### Single Responsibility
- `DetectionSession`: Apenas gerencia estado da sessão
- `DrowsinessDetector`: Apenas detecta sonolência
- `StreamProcessor`: Apenas processa stream

### Open/Closed
- Novos handlers podem ser adicionados sem modificar consumer
- Novos eventos podem ser criados sem modificar publisher

### Liskov Substitution
- `DomainEvent` é base para todos os eventos
- Qualquer evento pode ser publicado via `EventPublisher`

### Interface Segregation
- `EventConsumer` não depende de `EventPublisher`
- `StreamProcessor` não conhece `DrowsinessDetector`

### Dependency Inversion
- `CameraEventHandler` depende de abstrações (interfaces)
- Implementações concretas injetadas via construtor

## Monitoramento

### Logs
```
INFO - Conectado: localhost:5672
INFO - Handler: camera.added
INFO - Evento: camera.added
INFO - Adicionando câmera: cam-001
INFO - Stream iniciado: cam-001
INFO - Conectado: cam-001
WARNING - ALERTA: cam-001 - EAR: 0.150
INFO - Evento publicado: drowsiness.detected
```

### Métricas (futuro)
- Total de câmeras ativas
- Total de alertas por câmera
- EAR médio por câmera
- Uptime do plugin

## Troubleshooting

### Plugin não conecta ao RabbitMQ
- Verificar se RabbitMQ está rodando
- Verificar credenciais no .env
- Verificar firewall/portas

### Stream não inicia
- Verificar URL RTSP
- Verificar se MediaMTX está rodando
- Verificar logs do StreamProcessor

### Alertas não são publicados
- Verificar se EventPublisher está conectado
- Verificar exchange no RabbitMQ
- Verificar logs do handler

## Próximos Passos

1. Adicionar health check endpoint (FastAPI)
2. Implementar métricas (Prometheus)
3. Adicionar retry automático
4. Implementar dead letter queue
5. Adicionar testes de integração
6. Dockerizar plugin

## Referências

- RabbitMQ: https://www.rabbitmq.com/
- MediaPipe: https://developers.google.com/mediapipe
- DDD: Domain-Driven Design (Eric Evans)
- SOLID: Clean Architecture (Robert C. Martin)
