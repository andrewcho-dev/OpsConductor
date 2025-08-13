"""
WebSocket infrastructure for real-time updates.
"""
import json
import asyncio
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store connections by room/channel
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, room: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Add to user connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Add to room if specified
        if room:
            if room not in self.rooms:
                self.rooms[room] = set()
            self.rooms[room].add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "room": room,
            "connected_at": asyncio.get_event_loop().time()
        }
        
        logger.info(f"WebSocket connected: user_id={user_id}, room={room}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata[websocket]
            user_id = metadata["user_id"]
            room = metadata["room"]
            
            # Remove from user connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from room
            if room and room in self.rooms:
                self.rooms[room].discard(websocket)
                if not self.rooms[room]:
                    del self.rooms[room]
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected: user_id={user_id}, room={room}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """Send a message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected:
                self.disconnect(websocket)
    
    async def send_to_room(self, message: Dict[str, Any], room: str):
        """Send a message to all connections in a room."""
        if room in self.rooms:
            disconnected = set()
            for websocket in self.rooms[room]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to room {room}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected:
                self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = set()
        for websocket in self.connection_metadata.keys():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connection_metadata)
    
    def get_user_connection_count(self, user_id: int) -> int:
        """Get number of connections for a specific user."""
        return len(self.active_connections.get(user_id, set()))
    
    def get_room_connection_count(self, room: str) -> int:
        """Get number of connections in a room."""
        return len(self.rooms.get(room, set()))


# Global connection manager instance
connection_manager = ConnectionManager()


class WebSocketEventHandler:
    """Handles WebSocket events and message routing."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def handle_job_execution_started(self, event_data: Dict[str, Any]):
        """Handle job execution started event."""
        message = {
            "type": "job_execution_started",
            "data": event_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send to job monitoring room
        await self.connection_manager.send_to_room(
            message, 
            f"job_executions"
        )
        
        # Send to specific job room
        await self.connection_manager.send_to_room(
            message, 
            f"job_{event_data.get('job_id')}"
        )
    
    async def handle_job_execution_progress(self, event_data: Dict[str, Any]):
        """Handle job execution progress event."""
        message = {
            "type": "job_execution_progress",
            "data": event_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send to specific execution room
        await self.connection_manager.send_to_room(
            message, 
            f"execution_{event_data.get('execution_id')}"
        )
    
    async def handle_job_execution_completed(self, event_data: Dict[str, Any]):
        """Handle job execution completed event."""
        message = {
            "type": "job_execution_completed",
            "data": event_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send to job monitoring room
        await self.connection_manager.send_to_room(
            message, 
            f"job_executions"
        )
        
        # Send to specific job room
        await self.connection_manager.send_to_room(
            message, 
            f"job_{event_data.get('job_id')}"
        )
    
    async def handle_job_execution_failed(self, event_data: Dict[str, Any]):
        """Handle job execution failed event."""
        message = {
            "type": "job_execution_failed",
            "data": event_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send to job monitoring room
        await self.connection_manager.send_to_room(
            message, 
            f"job_executions"
        )
        
        # Send to specific job room
        await self.connection_manager.send_to_room(
            message, 
            f"job_{event_data.get('job_id')}"
        )
    
    async def handle_system_alert(self, event_data: Dict[str, Any]):
        """Handle system alert event."""
        message = {
            "type": "system_alert",
            "data": event_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Broadcast to all connected users
        await self.connection_manager.broadcast(message)


# Global WebSocket event handler
websocket_handler = WebSocketEventHandler(connection_manager)