from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

router = APIRouter()

# In-memory storage for active connections (use Redis in production)
active_connections: Dict[str, List[WebSocket]] = {}

async def _async_push_progress(job_id: str, agent: str, state: dict):
    if job_id in active_connections:
        message = {
            "job_id": job_id,
            "current_agent": agent,
            "progress_pct": state.get("progress_pct", 0),
            "message": f"Running {agent}...",
            "status": state.get("status", "running"),
            "timestamp": state.get("created_at", ""),
        }
        disconnected = []
        for ws in active_connections[job_id]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(ws)
        # Clean up disconnected
        for ws in disconnected:
            if ws in active_connections.get(job_id, []):
                active_connections[job_id].remove(ws)

def push_progress(job_id: str, agent: str, state: dict):
    """Push progress update to all connected WebSocket clients for a job (sync-safe)"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_async_push_progress(job_id, agent, state))
        else:
            loop.run_until_complete(_async_push_progress(job_id, agent, state))
    except RuntimeError:
        try:
            asyncio.run(_async_push_progress(job_id, agent, state))
        except Exception:
            pass
    except Exception:
        pass

@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)
    
    try:
        while True:
            # Keep connection alive, wait for messages (ping/pong)
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(json.dumps({"type": "pong", "data": data}))
    except WebSocketDisconnect:
        if job_id in active_connections:
            active_connections[job_id].remove(websocket)
            if not active_connections[job_id]:
                del active_connections[job_id]