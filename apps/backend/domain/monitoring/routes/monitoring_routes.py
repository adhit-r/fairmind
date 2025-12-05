"""
Monitoring Domain Routes.

Handles real-time monitoring, alerts, and WebSocket/SSE connections.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.container import inject
from domain.monitoring.services.monitoring_service import MonitoringService
from domain.monitoring.services.alert_service import AlertService


router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.subscriptions[user_id] = []

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.subscriptions:
            del self.subscriptions[user_id]

    async def broadcast(self, message: str, model_id: Optional[str] = None):
        for user_id, subscriptions in self.subscriptions.items():
            if model_id is None or model_id in subscriptions:
                if user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_text(message)
                    except Exception:
                        pass

    def subscribe(self, user_id: str, model_id: str):
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = []
        if model_id not in self.subscriptions[user_id]:
            self.subscriptions[user_id].append(model_id)

    def unsubscribe(self, user_id: str, model_id: str):
        if user_id in self.subscriptions and model_id in self.subscriptions[user_id]:
            self.subscriptions[user_id].remove(model_id)

manager = ConnectionManager()


# Models
class MonitoringConfig(BaseModel):
    model_id: str
    metrics: List[str] = ["accuracy", "bias", "drift"]
    thresholds: Dict[str, float] = {}
    frequency: int = 300
    enabled: bool = True

class AlertRuleCreate(BaseModel):
    name: str
    model_id: str
    metric: str
    condition: str
    threshold: float
    severity: str = "medium"
    enabled: bool = True

class ModelMetrics(BaseModel):
    model_id: str
    timestamp: Optional[datetime] = None
    accuracy: Optional[float] = None
    bias_score: Optional[float] = None
    drift_score: Optional[float] = None
    latency: Optional[float] = None
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    custom_metrics: Dict[str, float] = {}


# Routes

@router.post("/config")
async def create_config(
    config: MonitoringConfig,
    service: MonitoringService = Depends(inject(MonitoringService))
):
    return await service.create_config(config.model_dump())

@router.get("/config/{model_id}")
async def get_config(
    model_id: str,
    service: MonitoringService = Depends(inject(MonitoringService))
):
    return await service.get_config(model_id)

@router.post("/metrics")
async def record_metrics(
    metrics: ModelMetrics,
    monitor_service: MonitoringService = Depends(inject(MonitoringService)),
    alert_service: AlertService = Depends(inject(AlertService))
):
    # Record metrics
    result = await monitor_service.record_metrics(metrics.model_dump())
    
    # Check alerts
    alerts = await alert_service.check_alerts(metrics.model_dump())
    
    # Broadcast alerts
    if alerts:
        for alert in alerts:
            await manager.broadcast(
                json.dumps({"type": "alert", "data": alert, "timestamp": datetime.now().isoformat()}),
                model_id=metrics.model_id
            )
            
    return {"metrics": result, "alerts": alerts}

@router.get("/metrics/{model_id}")
async def get_metrics(
    model_id: str,
    limit: int = 100,
    service: MonitoringService = Depends(inject(MonitoringService))
):
    return await service.get_metrics(model_id, limit=limit)

@router.get("/health")
async def get_system_health(
    service: MonitoringService = Depends(inject(MonitoringService))
):
    return await service.get_system_health()

# Alert Routes

@router.post("/alerts/rules")
async def create_alert_rule(
    rule: AlertRuleCreate,
    service: AlertService = Depends(inject(AlertService))
):
    return await service.create_rule(rule.model_dump())

@router.get("/alerts")
async def list_alerts(
    model_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    service: AlertService = Depends(inject(AlertService))
):
    return await service.list_alerts(model_id, severity, acknowledged)

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user_id: str,
    service: AlertService = Depends(inject(AlertService))
):
    return await service.acknowledge_alert(alert_id, user_id)

# WebSocket Endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "subscribe":
                manager.subscribe(user_id, message["model_id"])
                await websocket.send_text(json.dumps({"type": "subscribed", "model_id": message["model_id"]}))
            
            elif message["type"] == "unsubscribe":
                manager.unsubscribe(user_id, message["model_id"])
                await websocket.send_text(json.dumps({"type": "unsubscribed", "model_id": message["model_id"]}))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# SSE Endpoint
@router.get("/events/{model_id}")
async def model_events(
    model_id: str,
    monitor_service: MonitoringService = Depends(inject(MonitoringService)),
    alert_service: AlertService = Depends(inject(AlertService))
):
    async def event_generator():
        while True:
            try:
                metrics = await monitor_service.get_latest_metrics(model_id)
                if metrics:
                    yield f"data: {json.dumps(metrics)}\n\n"
                
                alerts = await alert_service.get_unacknowledged_alerts(model_id)
                if alerts:
                    for alert in alerts:
                        yield f"data: {json.dumps({'type': 'alert', 'data': alert})}\n\n"
                
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )
