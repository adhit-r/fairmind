"""
WebSocket endpoint for real-time updates
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            'dashboard': set(),
            'governance_metrics': set(),
            'models': set(),
            'simulations': set(),
            'compliance': set(),
            'ai_bill': set()
        }

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        # Add to all channels for now
        for channel in self.active_connections.values():
            channel.add(websocket)
        logger.info(f"Client {client_id} connected")

    def disconnect(self, websocket: WebSocket, client_id: str):
        for channel in self.active_connections.values():
            channel.discard(websocket)
        logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(message)

    async def broadcast_to_channel(self, message: dict, channel: str):
        if channel in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[channel]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_text(json.dumps(message))
                    else:
                        disconnected.add(connection)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.active_connections[channel].discard(connection)

    async def broadcast_to_all(self, message: dict):
        for channel in self.active_connections.values():
            await self.broadcast_to_channel(message, channel)

# Global connection manager
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    client_id = f"client_{id(websocket)}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.info(f"Received message from {client_id}: {message}")
                
                # Handle different message types
                if message.get('type') == 'ping':
                    await manager.send_personal_message(
                        json.dumps({'type': 'pong', 'timestamp': datetime.now().isoformat()}),
                        websocket
                    )
                elif message.get('type') == 'subscribe':
                    # Handle subscription to specific channels
                    channels = message.get('channels', [])
                    logger.info(f"Client {client_id} subscribed to channels: {channels}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(websocket, client_id)

# Background task to send periodic updates
async def send_periodic_updates():
    """Send periodic updates to all connected clients"""
    while True:
        try:
            # Simulate real-time updates
            update_data = {
                'type': 'dashboard_update',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'governance_metrics': 'updated',
                    'models': 'updated',
                    'simulations': 'updated',
                    'compliance': 'updated'
                }
            }
            
            await manager.broadcast_to_all(update_data)
            
            # Wait 30 seconds before next update
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(5)

# Function to start the background task
def start_periodic_updates():
    """Start the periodic updates task"""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(send_periodic_updates())
    except RuntimeError:
        # No event loop running, will be started when server starts
        pass 