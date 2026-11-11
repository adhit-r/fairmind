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

# Application-layer adapters preserve API contracts while keeping dependency direction clean.
from src.application.services.monitoring_service import MonitoringService
from src.application.services.alert_service import AlertService
from ..models.core import BaseResponse
from api.routes.org_scope import org_member, org_mutator, tenant_key, untenant, ws_member
from src.application.services.governance_assurance_service import OrgMembership

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
# The REST routes sit on their own router so every one of them requires an active
# organisation member; the WebSocket authenticates itself (ws_member).
_rest = APIRouter(dependencies=[Depends(org_member)])

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

# The services below keep one process-wide store keyed by model id and rule id.
# Every id is namespaced with the caller's organisation on the way in and stripped
# on the way out, so tenants neither collide nor read each other's records.

# REST API Endpoints
def _out(org_id: str, record: Any) -> Any:
    """A stored record with its tenant-qualified ids turned back into the caller's own."""
    if isinstance(record, list):
        return [_out(org_id, item) for item in record]
    if not isinstance(record, dict):
        return record
    clean = dict(record)
    for field in ("model_id", "rule_id"):
        if isinstance(clean.get(field), str):
            clean[field] = untenant(org_id, clean[field]) or clean[field]
    if isinstance(clean.get("id"), str) and clean["id"].startswith(f"{org_id}/"):
        clean["id"] = untenant(org_id, clean["id"])
    return clean


def _owned_rule(org_id: str, rule_id: str) -> str:
    key = tenant_key(org_id, rule_id)
    if key not in alert_service.rules:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return key


@_rest.post("/config", response_model=BaseResponse)
async def create_monitoring_config(config: MonitoringConfig, m: OrgMembership = Depends(org_mutator)):
    """Create monitoring configuration for a model"""
    try:
        payload = config.model_dump()
        payload["model_id"] = tenant_key(m.org_id, config.model_id)
        result = await monitoring_service.create_config(payload)
        return BaseResponse(
            success=True,
            message="Monitoring configuration created successfully",
            data=_out(m.org_id, result)
        )
    except Exception as e:
        logger.error(f"Error creating monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.get("/config/{model_id}", response_model=BaseResponse)
async def get_monitoring_config(model_id: str, m: OrgMembership = Depends(org_member)):
    """Get monitoring configuration for a model"""
    try:
        config = await monitoring_service.get_config(tenant_key(m.org_id, model_id))
        return BaseResponse(
            success=True,
            message="Monitoring configuration retrieved successfully",
            data=_out(m.org_id, config)
        )
    except Exception as e:
        logger.error(f"Error getting monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.put("/config/{model_id}", response_model=BaseResponse)
async def update_monitoring_config(model_id: str, config: MonitoringConfig, m: OrgMembership = Depends(org_mutator)):
    """Update monitoring configuration for a model"""
    try:
        key = tenant_key(m.org_id, model_id)
        if await monitoring_service.get_config(key) is None:
            raise HTTPException(status_code=404, detail="Monitoring configuration not found")
        payload = config.dict()
        payload["model_id"] = key
        result = await monitoring_service.update_config(key, payload)
        return BaseResponse(
            success=True,
            message="Monitoring configuration updated successfully",
            data=_out(m.org_id, result)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.delete("/config/{model_id}", response_model=BaseResponse)
async def delete_monitoring_config(model_id: str, m: OrgMembership = Depends(org_mutator)):
    """Delete monitoring configuration for a model"""
    try:
        await monitoring_service.delete_config(tenant_key(m.org_id, model_id))
        return BaseResponse(
            success=True,
            message="Monitoring configuration deleted successfully"
        )
    except Exception as e:
        logger.error(f"Error deleting monitoring config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.post("/alerts/rules", response_model=BaseResponse)
async def create_alert_rule(rule: AlertRule, m: OrgMembership = Depends(org_mutator)):
    """Create an alert rule"""
    try:
        payload = rule.model_dump()
        payload["id"] = tenant_key(m.org_id, rule.id)
        payload["model_id"] = tenant_key(m.org_id, rule.model_id)
        result = await alert_service.create_rule(payload)
        return BaseResponse(
            success=True,
            message="Alert rule created successfully",
            data=_out(m.org_id, result)
        )
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.get("/alerts/rules", response_model=BaseResponse)
async def list_alert_rules(model_id: Optional[str] = None, m: OrgMembership = Depends(org_member)):
    """List alert rules, optionally filtered by model"""
    try:
        rules = await alert_service.list_rules(tenant_key(m.org_id, model_id) if model_id else None)
        rules = [r for r in rules if untenant(m.org_id, r["model_id"]) is not None]
        return BaseResponse(
            success=True,
            message="Alert rules retrieved successfully",
            data=_out(m.org_id, rules)
        )
    except Exception as e:
        logger.error(f"Error listing alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.put("/alerts/rules/{rule_id}", response_model=BaseResponse)
async def update_alert_rule(rule_id: str, rule: AlertRule, m: OrgMembership = Depends(org_mutator)):
    """Update an alert rule"""
    try:
        key = _owned_rule(m.org_id, rule_id)
        payload = rule.dict()
        payload["id"] = key
        payload["model_id"] = tenant_key(m.org_id, rule.model_id)
        result = await alert_service.update_rule(key, payload)
        return BaseResponse(
            success=True,
            message="Alert rule updated successfully",
            data=_out(m.org_id, result)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.delete("/alerts/rules/{rule_id}", response_model=BaseResponse)
async def delete_alert_rule(rule_id: str, m: OrgMembership = Depends(org_mutator)):
    """Delete an alert rule"""
    try:
        await alert_service.delete_rule(tenant_key(m.org_id, rule_id))
        return BaseResponse(
            success=True,
            message="Alert rule deleted successfully"
        )
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.get("/alerts", response_model=BaseResponse)
async def list_alerts(
    model_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    m: OrgMembership = Depends(org_member),
):
    """List alerts with optional filtering"""
    try:
        # The service paginates the whole process-wide store, so ask for everything,
        # keep this organisation's alerts, then paginate.
        alerts = await alert_service.list_alerts(
            model_id=tenant_key(m.org_id, model_id) if model_id else None,
            severity=severity,
            acknowledged=acknowledged,
            limit=len(alert_service.alerts),
            offset=0,
        )
        alerts = [a for a in alerts if untenant(m.org_id, a["model_id"]) is not None]
        return BaseResponse(
            success=True,
            message="Alerts retrieved successfully",
            data=_out(m.org_id, alerts[offset:offset + limit])
        )
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.post("/alerts/{alert_id}/acknowledge", response_model=BaseResponse)
async def acknowledge_alert(alert_id: str, user_id: Optional[str] = None, m: OrgMembership = Depends(org_mutator)):
    """Acknowledge an alert as the signed-in user (a user_id query value is ignored)."""
    try:
        alert = alert_service.alerts.get(alert_id)
        if alert is None or untenant(m.org_id, alert.model_id) is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        result = await alert_service.acknowledge_alert(alert_id, m.user_id)
        return BaseResponse(
            success=True,
            message="Alert acknowledged successfully",
            data=_out(m.org_id, result)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.get("/metrics/{model_id}", response_model=BaseResponse)
async def get_model_metrics(
    model_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    m: OrgMembership = Depends(org_member),
):
    """Get metrics for a model within a time range"""
    try:
        metrics = await monitoring_service.get_metrics(
            model_id=tenant_key(m.org_id, model_id),
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return BaseResponse(
            success=True,
            message="Model metrics retrieved successfully",
            data=_out(m.org_id, metrics)
        )
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.post("/metrics", response_model=BaseResponse)
async def record_metrics(metrics: ModelMetrics, m: OrgMembership = Depends(org_mutator)):
    """Record metrics for a model"""
    try:
        payload = metrics.model_dump()
        payload["model_id"] = tenant_key(m.org_id, metrics.model_id)
        result = await monitoring_service.record_metrics(payload)

        # Check for alerts
        alerts = await alert_service.check_alerts(payload)

        # Broadcast to WebSocket subscribers of this organisation's model
        if alerts:
            for alert in alerts:
                await manager.broadcast(
                    json.dumps({
                        "type": "alert",
                        "data": _out(m.org_id, alert)
                    }, default=str),
                    model_id=payload["model_id"]
                )

        return BaseResponse(
            success=True,
            message="Metrics recorded successfully",
            data={"metrics": _out(m.org_id, result), "alerts": _out(m.org_id, alerts)}
        )
    except Exception as e:
        logger.error(f"Error recording metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@_rest.get("/health", response_model=BaseResponse)
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

@_rest.get("/metrics")
def get_monitoring_metrics():
    """Get monitoring metrics for dashboard"""
    raise HTTPException(status_code=501, detail="Fleet monitoring metrics are not collected yet. Use /metrics/{model_id} for recorded metrics.")


# WebSocket Endpoints
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, m: OrgMembership = Depends(ws_member)):
    """WebSocket endpoint for real-time monitoring (token via ?token= or Authorization header)"""
    if user_id != m.user_id:
        await websocket.close(code=1008)
        return
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Receive subscription/unsubscription messages
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "subscribe":
                manager.subscribe(user_id, tenant_key(m.org_id, message["model_id"]))
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "model_id": message["model_id"]
                }))

            elif message["type"] == "unsubscribe":
                manager.unsubscribe(user_id, tenant_key(m.org_id, message["model_id"]))
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
@_rest.get("/events/{model_id}")
async def model_events(model_id: str, m: OrgMembership = Depends(org_member)):
    """Server-sent events endpoint for model monitoring"""
    key = tenant_key(m.org_id, model_id)

    async def event_generator():
        while True:
            try:
                # Get latest metrics
                metrics = await monitoring_service.get_latest_metrics(key)
                if metrics:
                    yield f"data: {json.dumps(_out(m.org_id, metrics))}\n\n"

                # Check for alerts
                alerts = await alert_service.get_unacknowledged_alerts(key)
                if alerts:
                    for alert in alerts:
                        yield f"data: {json.dumps({'type': 'alert', 'data': _out(m.org_id, alert)}, default=str)}\n\n"

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


router.include_router(_rest)
