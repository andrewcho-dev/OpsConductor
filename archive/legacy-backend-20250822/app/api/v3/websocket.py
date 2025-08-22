"""
WebSocket API v3 - Consolidated from v2/websocket_enhanced.py
All real-time communication endpoints in v3 structure
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import logging

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

api_base_url = os.getenv("API_BASE_URL", "/api/v1")
router = APIRouter(prefix=f"{api_base_url}/websocket", tags=["WebSocket v1"])

# Configure structured logger
logger = get_structured_logger(__name__)


# MODELS

class WebSocketConnectionInfo(BaseModel):
    """Model for WebSocket connection information"""
    connection_id: str
    user_id: int
    room: Optional[str] = None
    connected_at: datetime
    last_activity: datetime
    client_info: Dict[str, Any] = Field(default_factory=dict)


class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    sender_id: Optional[int] = None
    room: Optional[str] = None


class WebSocketRoom(BaseModel):
    """Model for WebSocket rooms"""
    name: str
    description: Optional[str] = None
    created_at: datetime
    member_count: int
    is_private: bool = False


# Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, List[str]] = {}
        self.room_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int, room: Optional[str] = None):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        if room:
            if room not in self.room_connections:
                self.room_connections[room] = []
            self.room_connections[room].append(connection_id)

    def disconnect(self, connection_id: str, user_id: int, room: Optional[str] = None):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        if room and room in self.room_connections:
            if connection_id in self.room_connections[room]:
                self.room_connections[room].remove(connection_id)
            if not self.room_connections[room]:
                del self.room_connections[room]

    async def send_personal_message(self, message: str, connection_id: str):
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_text(message)

    async def send_to_user(self, message: str, user_id: int):
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                await self.send_personal_message(message, connection_id)

    async def send_to_room(self, message: str, room: str):
        if room in self.room_connections:
            for connection_id in self.room_connections[room]:
                await self.send_personal_message(message, connection_id)

    async def broadcast(self, message: str):
        for connection_id in self.active_connections:
            await self.send_personal_message(message, connection_id)


# Global connection manager
manager = ConnectionManager()


# WEBSOCKET ENDPOINTS

@router.websocket("/connect/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    room: Optional[str] = None
):
    """Main WebSocket connection endpoint"""
    try:
        # In a real implementation, you would validate the token here
        # For now, we'll use a mock user ID
        user_id = 1  # Mock user ID
        connection_id = f"conn_{user_id}_{datetime.now().timestamp()}"
        
        await manager.connect(websocket, connection_id, user_id, room)
        logger.info(f"WebSocket connected: {connection_id}, user: {user_id}, room: {room}")
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "user_id": user_id,
                "room": room,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process message based on type
                message_type = message_data.get("type", "unknown")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    pong_message = {
                        "type": "pong",
                        "data": {"timestamp": datetime.now(timezone.utc).isoformat()}
                    }
                    await websocket.send_text(json.dumps(pong_message))
                
                elif message_type == "join_room":
                    # Join a room
                    new_room = message_data.get("data", {}).get("room")
                    if new_room:
                        if new_room not in manager.room_connections:
                            manager.room_connections[new_room] = []
                        manager.room_connections[new_room].append(connection_id)
                        
                        join_message = {
                            "type": "room_joined",
                            "data": {"room": new_room, "timestamp": datetime.now(timezone.utc).isoformat()}
                        }
                        await websocket.send_text(json.dumps(join_message))
                
                elif message_type == "leave_room":
                    # Leave a room
                    leave_room = message_data.get("data", {}).get("room")
                    if leave_room and leave_room in manager.room_connections:
                        if connection_id in manager.room_connections[leave_room]:
                            manager.room_connections[leave_room].remove(connection_id)
                        
                        leave_message = {
                            "type": "room_left",
                            "data": {"room": leave_room, "timestamp": datetime.now(timezone.utc).isoformat()}
                        }
                        await websocket.send_text(json.dumps(leave_message))
                
                elif message_type == "broadcast":
                    # Broadcast message to room or all users
                    broadcast_data = message_data.get("data", {})
                    target_room = broadcast_data.get("room")
                    message_content = broadcast_data.get("message", "")
                    
                    broadcast_message = {
                        "type": "broadcast_message",
                        "data": {
                            "message": message_content,
                            "sender_id": user_id,
                            "room": target_room,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    
                    if target_room:
                        await manager.send_to_room(json.dumps(broadcast_message), target_room)
                    else:
                        await manager.broadcast(json.dumps(broadcast_message))
                
                else:
                    # Echo unknown messages back
                    echo_message = {
                        "type": "echo",
                        "data": message_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await websocket.send_text(json.dumps(echo_message))
                    
        except WebSocketDisconnect:
            manager.disconnect(connection_id, user_id, room)
            logger.info(f"WebSocket disconnected: {connection_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()


# REST ENDPOINTS FOR WEBSOCKET MANAGEMENT

@router.get("/connections", response_model=List[WebSocketConnectionInfo])
async def get_active_connections(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of active WebSocket connections"""
    try:
        connections = []
        for connection_id, websocket in manager.active_connections.items():
            # Mock connection info
            connections.append(WebSocketConnectionInfo(
                connection_id=connection_id,
                user_id=1,  # Mock user ID
                room=None,  # Would need to track this properly
                connected_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                client_info={"ip": "127.0.0.1", "user_agent": "Mock Client"}
            ))
        
        return connections
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket connections: {str(e)}"
        )


@router.get("/rooms", response_model=List[WebSocketRoom])
async def get_websocket_rooms(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of WebSocket rooms"""
    try:
        rooms = []
        for room_name, connections in manager.room_connections.items():
            rooms.append(WebSocketRoom(
                name=room_name,
                description=f"Room for {room_name}",
                created_at=datetime.now(timezone.utc),
                member_count=len(connections),
                is_private=False
            ))
        
        return rooms
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket rooms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket rooms: {str(e)}"
        )


@router.post("/broadcast")
async def broadcast_message(
    message: WebSocketMessage,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Broadcast a message to WebSocket connections"""
    try:
        broadcast_data = {
            "type": message.type,
            "data": message.data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sender_id": current_user["id"]
        }
        
        if message.room:
            await manager.send_to_room(json.dumps(broadcast_data), message.room)
            target = f"room '{message.room}'"
        else:
            await manager.broadcast(json.dumps(broadcast_data))
            target = "all connections"
        
        return {
            "message": f"Message broadcasted to {target}",
            "type": message.type,
            "timestamp": broadcast_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast WebSocket message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast message: {str(e)}"
        )


@router.post("/send-to-user/{user_id}")
async def send_message_to_user(
    user_id: int,
    message: WebSocketMessage,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to a specific user"""
    try:
        message_data = {
            "type": message.type,
            "data": message.data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sender_id": current_user["id"]
        }
        
        await manager.send_to_user(json.dumps(message_data), user_id)
        
        return {
            "message": f"Message sent to user {user_id}",
            "type": message.type,
            "timestamp": message_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket message to user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message to user: {str(e)}"
        )


@router.get("/stats")
async def get_websocket_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get WebSocket statistics"""
    try:
        stats = {
            "total_connections": len(manager.active_connections),
            "total_users": len(manager.user_connections),
            "total_rooms": len(manager.room_connections),
            "connections_by_room": {
                room: len(connections) 
                for room, connections in manager.room_connections.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket stats: {str(e)}"
        )