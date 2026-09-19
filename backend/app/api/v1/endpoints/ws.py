import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from app.services.data_store import data_store

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial snapshot immediately upon connection
        await websocket.send_json({
            "type": "INITIAL_SNAPSHOT",
            "sensors": [s.model_dump() for s in data_store.sensors.values()],
            "zones": [z.model_dump() for z in data_store.zones.values()],
            "simulation": data_store.simulation_state
        })

        # Keep connection alive & listen for incoming ping or client messages
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "PING":
                    await websocket.send_json({"type": "PONG", "timestamp": int(asyncio.get_event_loop().time() * 1000)})
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
