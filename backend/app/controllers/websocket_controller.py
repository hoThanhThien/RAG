from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
import anyio
from app.dependencies.auth_dependencies import get_current_user_ws
from app.database import get_db_connection
from fastapi import Depends

router = APIRouter()

# ================= Tour WebSocket ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, tour_id: int):
        await websocket.accept()
        if tour_id not in self.active_connections:
            self.active_connections[tour_id] = []
        self.active_connections[tour_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, tour_id: int):
        if tour_id in self.active_connections:
            self.active_connections[tour_id].remove(websocket)
            if not self.active_connections[tour_id]:
                del self.active_connections[tour_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_tour(self, message: str, tour_id: int):
        if tour_id in self.active_connections:
            for connection in self.active_connections[tour_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass  # ignore broken connections

manager = ConnectionManager()

@router.websocket("/ws/tour/{tour_id}")
async def websocket_endpoint(websocket: WebSocket, tour_id: int):
    await manager.connect(websocket, tour_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_id = message_data.get("user_id")
            message_content = message_data.get("message")
            message_type = message_data.get("type", "chat")

            if message_type == "comment":
                connection = get_db_connection()
                cursor = connection.cursor()
                try:
                    cursor.execute("SELECT FullName FROM user WHERE UserID = %s", (user_id,))
                    user = cursor.fetchone()

                    if user:
                        broadcast_message = {
                            "type": "comment",
                            "user_id": user_id,
                            "user_name": user["FullName"],
                            "tour_id": tour_id,
                            "message": message_content,
                            "timestamp": str(asyncio.get_event_loop().time())
                        }
                        await manager.broadcast_to_tour(json.dumps(broadcast_message), tour_id)

                finally:
                    cursor.close()
                    connection.close()

    except WebSocketDisconnect:
        manager.disconnect(websocket, tour_id)

@router.get("/tours/{tour_id}/live-stats")
async def get_tour_live_stats(tour_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        online_count = len(manager.active_connections.get(tour_id, []))

        cursor.execute("""
            SELECT 
                COUNT(*) as total_bookings,
                SUM(CASE WHEN Status = 'Confirmed' THEN NumberOfPeople ELSE 0 END) as confirmed_people,
                SUM(CASE WHEN Status = 'Pending' THEN NumberOfPeople ELSE 0 END) as pending_people
            FROM booking 
            WHERE TourID = %s
        """, (tour_id,))
        booking_stats = cursor.fetchone()

        cursor.execute("""
            SELECT AVG(Rating) as avg_rating, COUNT(*) as total_comments
            FROM comment 
            WHERE TourID = %s
        """, (tour_id,))
        rating_stats = cursor.fetchone()

        return {
            "tour_id": tour_id,
            "online_users": online_count,
            "total_bookings": booking_stats["total_bookings"],
            "confirmed_people": booking_stats["confirmed_people"],
            "pending_people": booking_stats["pending_people"],
            "avg_rating": float(rating_stats["avg_rating"]) if rating_stats["avg_rating"] else 0,
            "total_comments": rating_stats["total_comments"]
        }

    finally:
        cursor.close()
        connection.close()


# ================= Support WebSocket ====================

SUPPORT_CONNECTIONS = {}  # room → set of websockets

def ws_broadcast_safe(room: str, message: dict):
    async def _send():
        for ws in list(SUPPORT_CONNECTIONS.get(room, [])):
            try:
                await ws.send_json(message)
            except:
                pass
    anyio.from_thread.run(_send)

async def support_join(room: str, ws: WebSocket):
    SUPPORT_CONNECTIONS.setdefault(room, set()).add(ws)

async def support_leave(ws: WebSocket):
    for room, conns in list(SUPPORT_CONNECTIONS.items()):
        if ws in conns:
            conns.remove(ws)
            if not conns:
                SUPPORT_CONNECTIONS.pop(room, None)

@router.websocket("/ws/support")
async def ws_support(websocket: WebSocket, user=Depends(get_current_user_ws)):
    await websocket.accept()

    if user.get("role_id") != 1:
        await support_join(f"support:user:{user['UserID']}", websocket)
    else:
        await support_join("support:admin", websocket)

    try:
        while True:
            data = await websocket.receive_json()
            t = data.get("type")

            if t == "join":
                room = data.get("room")
                if user.get("role_id") == 1 and room and room.startswith("support:user:"):
                    await support_join(room, websocket)

            elif t == "typing":
                room = data.get("room")
                thread_id = data.get("thread_id")
                if thread_id:
                    # Broadcast typing indicator
                    typing_payload = {
                        "type": "support:typing",
                        "thread_id": thread_id,
                        "user_id": user["UserID"],
                        "is_admin": 1 if user.get("role_id") == 1 else 0
                    }
                    
                    # Gửi cho admin nếu user đang gõ
                    if user.get("role_id") != 1:
                        ws_broadcast_safe("support:admin", typing_payload)
                    # Gửi cho user nếu admin đang gõ
                    else:
                        ws_broadcast_safe(f"support:user:{data.get('user_id')}", typing_payload)

            elif t == "message":
                room = data.get("room")
                message = data.get("message")

                if room and message:
                    ws_broadcast_safe(room, {
                        "type": "message",
                        "room": room,
                        "content": message,
                        "user_id": user["UserID"],
                        "is_admin": user.get("role_id") == 1,
                        "full_name": user.get("full_name", "Unknown")
                    })

    except WebSocketDisconnect:
        await support_leave(websocket)
