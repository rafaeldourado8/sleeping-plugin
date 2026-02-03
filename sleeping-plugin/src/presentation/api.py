"""
FastAPI - Minimal Performance-Focused
Health check e métricas com overhead mínimo
"""
from fastapi import FastAPI
from typing import Dict
import threading

app = FastAPI(title="VigilEye", docs_url=None, redoc_url=None)

_handler = None

@app.get("/health")
def health():
    active = sum(1 for s in _handler.sessions.values() if s.is_active)
    return {"status": "ok", "active": active}

@app.get("/metrics")
def metrics():
    sessions = _handler.sessions
    return {
        "total": len(sessions),
        "active": sum(1 for s in sessions.values() if s.is_active),
        "alerts": sum(s.total_alerts for s in sessions.values())
    }

def start_api(handler, port: int = 8000):
    global _handler
    _handler = handler
    
    import uvicorn
    thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=port, log_level="error"),
        daemon=True
    )
    thread.start()
