"""
Real-time Monitoring and Alerting System

This module provides comprehensive monitoring capabilities for:
- Model performance tracking
- Data drift detection
- Bias monitoring
- System health monitoring
- Real-time alerts and notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional, Union
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
from enum import Enum

# Import services
from ..services.monitoring_service import MonitoringService
from ..services.alert_service import AlertService
from ..models.core import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # user_id -> list of model_ids

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.subscriptions[user_id] = []
        logger.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.subscriptions:
            del self.subscriptions[user_id]
        logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast(self, message: str, model_id: Optional[str] = None):
        """Broadcast message to all users subscribed to a specific model"""
        for user_id, subscriptions in self.subscriptions.items():
            if model_id is None or model_id in subscriptions:
                await self.send_personal_message(message, user_id)

    def subscribe(self, user_id: str, model_id: str):
        """Subscribe user to model updates"""
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = []
        if model_id not in self.subscriptions[user_id]:
            self.subscriptions[user_id].append(model_id)
        logger.info(f"User {user_id} subscribed to model {model_id}")

    def unsubscribe(self, user_id: str, model_id: str):
        """Unsubscribe user from model updates"""
        if user_id in self.subscriptions and model_id in self.subscriptions[user_id]:
            self.subscriptions[user_id].remove(model_id)
        logger.info(f"User {user_id} unsubscribed from model {model_id}")

manager = ConnectionManager()

# Pydantic models
class MonitoringConfig(BaseModel):
    model_id: str = Field(..., description="Model ID to monitor")
    metrics: List[str] = Field(default=["accuracy", "bias", "drift"], description="Metrics to monitor")
    thresholds: Dict[str, float] = Field(default={}, description="Alert thresholds")
    frequency: int = Field(default=300, description="Monitoring frequency in seconds")
    enabled: bool = Field(default=True, description="Whether monitoring is enabled")

class AlertRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Alert rule name")
    model_id: str = Field(..., description="Model ID to monitor")
    metric: str = Field(..., description="Metric to monitor")
    condition: str = Field(..., description="Alert condition (>, <, =, !=)")
    threshold: float = Field(..., description="Alert threshold")
    severity: str = Field(default="medium", description="Alert severity")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = Field(..., description="Alert rule ID")
    model_id: str = Field(..., description="Model ID")
    metric: str = Field(..., description="Metric that triggered alert")
    value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Alert threshold")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = Field(default=False, description="Whether alert is acknowledged")
    acknowledged_by: Optional[str] = Field(default=None, description="User who acknowledged")
    acknowledged_at: Optional[datetime] = Field(default=None, description="When alert was acknowledged")

class ModelMetrics(BaseModel):
    model_id: str = Field(..., description="Model ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    accuracy: Optional[float] = Field(default=None, description="Model accuracy")
    bias_score: Optional[float] = Field(default=None, description="Bias detection score")
    drift_score: Optional[float] = Field(default=None, description="Data drift score")
    latency: Optional[float] = Field(default=None, description="Prediction latency in ms")
    throughput: Optional[float] = Field(default=None, description="Predictions per second")
    error_rate: Optional[float] = Field(default=None, description="Error rate percentage")
    custom_metrics: Dict[str, float] = Field(default={}, description="Custom metrics")

# Initialize services
monitoring_service = MonitoringService()
alert_service = AlertService()

# REST API Endpoints
@router.post("/config", response_model=BaseResponse)
async def create_monitoring_config(config: MonitoringConfig):
    """Create monitoring configuration for a model"""
    try:
        result = await monitoring_service.create_config(config.model_dump())
        return BaseResponse(
            success=True,
            message="Monitoring configuration created successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error creating monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/{model_id}", response_model=BaseResponse)
async def get_monitoring_config(model_id: str):
    """Get monitoring configuration for a model"""
    try:
        config = await monitoring_service.get_config(model_id)
        return BaseResponse(
            success=True,
            message="Monitoring configuration retrieved successfully",
            data=config
        )
    except Exception as e:
        logger.error(f"Error getting monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/{model_id}", response_model=BaseResponse)
async def update_monitoring_config(model_id: str, config: MonitoringConfig):
    """Update monitoring configuration for a model"""
    try:
        result = await monitoring_service.update_config(model_id, config.dict())
        return BaseResponse(
            success=True,
            message="Monitoring configuration updated successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error updating monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/config/{model_id}", response_model=BaseResponse)
async def delete_monitoring_config(model_id: str):
    """Delete monitoring configuration for a model"""
    try:
        await monitoring_service.delete_config(model_id)
        return BaseResponse(
            success=True,
            message="Monitoring configuration deleted successfully"
        )
    except Exception as e:
        logger.error(f"Error deleting monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/rules", response_model=BaseResponse)
async def create_alert_rule(rule: AlertRule):
    """Create an alert rule"""
    try:
        result = await alert_service.create_rule(rule.model_dump())
        return BaseResponse(
            success=True,
            message="Alert rule created successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/rules", response_model=BaseResponse)
async def list_alert_rules(model_id: Optional[str] = None):
    """List alert rules, optionally filtered by model"""
    try:
        rules = await alert_service.list_rules(model_id)
        return BaseResponse(
            success=True,
            message="Alert rules retrieved successfully",
            data=rules
        )
    except Exception as e:
        logger.error(f"Error listing alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/rules/{rule_id}", response_model=BaseResponse)
async def update_alert_rule(rule_id: str, rule: AlertRule):
    """Update an alert rule"""
    try:
        result = await alert_service.update_rule(rule_id, rule.dict())
        return BaseResponse(
            success=True,
            message="Alert rule updated successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts/rules/{rule_id}", response_model=BaseResponse)
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule"""
    try:
        await alert_service.delete_rule(rule_id)
        return BaseResponse(
            success=True,
            message="Alert rule deleted successfully"
        )
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=BaseResponse)
async def list_alerts(
    model_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """List alerts with optional filtering"""
    try:
        alerts = await alert_service.list_alerts(
            model_id=model_id,
            severity=severity,
            acknowledged=acknowledged,
            limit=limit,
            offset=offset
        )
        return BaseResponse(
            success=True,
            message="Alerts retrieved successfully",
            data=alerts
        )
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge", response_model=BaseResponse)
async def acknowledge_alert(alert_id: str, user_id: str):
    """Acknowledge an alert"""
    try:
        result = await alert_service.acknowledge_alert(alert_id, user_id)
        return BaseResponse(
            success=True,
            message="Alert acknowledged successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{model_id}", response_model=BaseResponse)
async def get_model_metrics(
    model_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
):
    """Get metrics for a model within a time range"""
    try:
        metrics = await monitoring_service.get_metrics(
            model_id=model_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return BaseResponse(
            success=True,
            message="Model metrics retrieved successfully",
            data=metrics
        )
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics", response_model=BaseResponse)
async def record_metrics(metrics: ModelMetrics):
    """Record metrics for a model"""
    try:
        result = await monitoring_service.record_metrics(metrics.model_dump())
        
        # Check for alerts
        alerts = await alert_service.check_alerts(metrics.model_dump())
        
        # Broadcast to WebSocket subscribers
        if alerts:
            for alert in alerts:
                await manager.broadcast(
                    json.dumps({
                        "type": "alert",
                        "data": alert
                    }),
                    model_id=metrics.model_id
                )
        
        return BaseResponse(
            success=True,
            message="Metrics recorded successfully",
            data={"metrics": result, "alerts": alerts}
        )
    except Exception as e:
        logger.error(f"Error recording metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=BaseResponse)
async def get_system_health():
    """Get overall system health status"""
    try:
        health = await monitoring_service.get_system_health()
        return BaseResponse(
            success=True,
            message="System health retrieved successfully",
            data=health
        )
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_monitoring_metrics():
    """Get monitoring metrics for dashboard"""
    try:
        # Return mock monitoring metrics
        metrics = {
            "summary": {
                "avg_accuracy": 87.5,
                "avg_latency": 120,
                "uptime": 99.8,
                "throughput": 1500
            },
            "metrics": [
                {
                    "date": "2024-01-20",
                    "accuracy": 85.2,
                    "latency": 125,
                    "throughput": 1450
                },
                {
                    "date": "2024-01-21",
                    "accuracy": 88.1,
                    "latency": 118,
                    "throughput": 1520
                },
                {
                    "date": "2024-01-22",
                    "accuracy": 89.3,
                    "latency": 115,
                    "throughput": 1580
                }
            ]
        }
        
        return {
            "success": True,
            "metrics": metrics["metrics"],
            "summary": metrics["summary"]
        }
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoints
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time monitoring"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Receive subscription/unsubscription messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "subscribe":
                manager.subscribe(user_id, message["model_id"])
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "model_id": message["model_id"]
                }))
            
            elif message["type"] == "unsubscribe":
                manager.unsubscribe(user_id, message["model_id"])
                await websocket.send_text(json.dumps({
                    "type": "unsubscribed",
                    "model_id": message["model_id"]
                }))
            
            elif message["type"] == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)

# SSE Endpoint for server-sent events
@router.get("/events/{model_id}")
async def model_events(model_id: str):
    """Server-sent events endpoint for model monitoring"""
    async def event_generator():
        while True:
            try:
                # Get latest metrics
                metrics = await monitoring_service.get_latest_metrics(model_id)
                if metrics:
                    yield f"data: {json.dumps(metrics)}\n\n"
                
                # Check for alerts
                alerts = await alert_service.get_unacknowledged_alerts(model_id)
                if alerts:
                    for alert in alerts:
                        yield f"data: {json.dumps({'type': 'alert', 'data': alert})}\n\n"
                
                await asyncio.sleep(5)  # Send updates every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in event generator: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )
