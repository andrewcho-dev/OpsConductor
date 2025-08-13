"""
WebSocket endpoints for real-time updates.
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional

from app.shared.infrastructure.websocket import connection_manager
from app.core.security import verify_token
from app.models.user_models import User

router = APIRouter()
security = HTTPBearer()


async def get_user_from_token(token: str) -> Optional[User]:
    """Get user from WebSocket token."""
    try:
        user = verify_token(token)
        return user
    except Exception:
        return None


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, room: Optional[str] = None):
    """WebSocket endpoint for real-time updates."""
    # Verify token and get user
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect to WebSocket
    await connection_manager.connect(websocket, user.id, room)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(websocket, user, message)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }))
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, user: User, message: dict):
    """Handle incoming client messages."""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": asyncio.get_event_loop().time()
        }))
    
    elif message_type == "subscribe":
        # Subscribe to a specific room/channel
        room = message.get("room")
        if room:
            # Add connection to room
            if room not in connection_manager.rooms:
                connection_manager.rooms[room] = set()
            connection_manager.rooms[room].add(websocket)
            
            # Update metadata
            if websocket in connection_manager.connection_metadata:
                connection_manager.connection_metadata[websocket]["room"] = room
            
            await websocket.send_text(json.dumps({
                "type": "subscribed",
                "room": room
            }))
    
    elif message_type == "unsubscribe":
        # Unsubscribe from a room/channel
        room = message.get("room")
        if room and room in connection_manager.rooms:
            connection_manager.rooms[room].discard(websocket)
            if not connection_manager.rooms[room]:
                del connection_manager.rooms[room]
            
            await websocket.send_text(json.dumps({
                "type": "unsubscribed",
                "room": room
            }))
    
    elif message_type == "get_status":
        # Send connection status
        await websocket.send_text(json.dumps({
            "type": "status",
            "user_id": user.id,
            "username": user.username,
            "connected_at": connection_manager.connection_metadata.get(websocket, {}).get("connected_at"),
            "total_connections": connection_manager.get_connection_count()
        }))
    
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": connection_manager.get_connection_count(),
        "active_users": len(connection_manager.active_connections),
        "active_rooms": len(connection_manager.rooms),
        "rooms": {
            room: len(connections) 
            for room, connections in connection_manager.rooms.items()
        }
    }