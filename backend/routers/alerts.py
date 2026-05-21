"""
WebSocket alert endpoint + REST alert log.

WS  /alerts/ws  — real-time push when NEO < threshold LD
GET /alerts/log — persisted alert history
"""

import json
import asyncio
from datetime import datetime
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services import neo_service
from backend.models.neo import AlertLog

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ── Connection Manager ────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, payload: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    return manager


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws")
async def alerts_ws(websocket: WebSocket):
    """
    WebSocket stream.  Client receives JSON alerts:
      { "type": "alert", "neo_id": ..., "neo_name": ...,
        "miss_distance_ld": ..., "approach_date": ..., "triggered_at": ... }
    """
    await manager.connect(websocket)
    try:
        # Keep connection alive; client can send pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "heartbeat"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── REST log endpoint ─────────────────────────────────────────────────────────

@router.get("/log")
async def alert_log(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Persisted alert history (most recent first)."""
    return await neo_service.get_alert_log(db, limit=limit)


# ── Broadcast helper (called by scheduler) ───────────────────────────────────

async def fire_alert(db: AsyncSession, neo_id: str, neo_name: str,
                     miss_ld: float, approach_date: str):
    """Persist alert to DB and broadcast over WebSocket."""
    payload = {
        "type": "alert",
        "neo_id": neo_id,
        "neo_name": neo_name,
        "miss_distance_ld": round(miss_ld, 4),
        "approach_date": approach_date,
        "triggered_at": datetime.utcnow().isoformat(),
    }
    log = AlertLog(
        neo_id=neo_id,
        neo_name=neo_name,
        miss_distance_ld=miss_ld,
        approach_date=approach_date,
        payload=payload,
    )
    db.add(log)
    await db.flush()
    await manager.broadcast(payload)
