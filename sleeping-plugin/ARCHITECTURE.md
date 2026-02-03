# VigilEye Plugin - Event-Driven Architecture

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────┐
│                      VMS HUB (Main System)                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  CRUD    │───▶│ RabbitMQ │───▶│ Plugins  │             │
│  │  API     │    │ Exchange │    │ (Workers)│             │
│  └──────────┘    └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   VigilEye Plugin (Drowsiness)       │
        │                                      │
        │  ┌────────────────────────────┐     │
        │  │  Event Consumer            │     │
        │  │  - camera.added            │     │
        │  │  - camera.removed          │     │
        │  └────────────────────────────┘     │
        │              ▼                       │
        │  ┌────────────────────────────┐     │
        │  │  Processing Engine         │     │
        │  │  - MediaPipe Detection     │     │
        │  │  - EAR Calculation         │     │
        │  └────────────────────────────┘     │
        │              ▼                       │
        │  ┌────────────────────────────┐     │
        │  │  Event Publisher           │     │
        │  │  - drowsiness.detected     │     │
        │  │  - alert.triggered         │     │
        │  └────────────────────────────┘     │
        └──────────────────────────────────────┘
```

## Eventos (Contratos)

### Input: camera.added
```json
{
  "event_type": "camera.added",
  "camera_id": "cam-001",
  "rtsp_url": "rtsp://localhost:8554/stream1"
}
```

### Output: drowsiness.detected
```json
{
  "event_type": "drowsiness.detected",
  "camera_id": "cam-001",
  "ear_value": 0.15,
  "timestamp": "2024-01-15T10:31:45Z"
}
```
