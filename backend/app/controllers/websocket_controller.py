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

# Global reference to main event loop (set when first WS connects)
_main_loop = None

def ws_broadcast_safe(room: str, message: dict):
    """Broadcast message to all connections in a room (thread-safe)"""
    import asyncio
    import threading
    
    async def _send():
        for ws in list(SUPPORT_CONNECTIONS.get(room, [])):
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"⚠️ WS broadcast error to {room}: {e}")
    
    global _main_loop
    
    if _main_loop and _main_loop.is_running():
        # Schedule in the main event loop
        asyncio.run_coroutine_threadsafe(_send(), _main_loop)
    else:
        # Fallback: run in new thread with new event loop
        def run_in_thread():
            try:
                asyncio.run(_send())
            except Exception as e:
                print(f"⚠️ WS broadcast thread error: {e}")
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

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
    import asyncio
    global _main_loop
    
    # Store reference to main event loop for cross-thread broadcasting
    _main_loop = asyncio.get_event_loop()
    
    await websocket.accept()
    
    # 🔧 FIX: Database trả về RoleID (chữ hoa), không phải role_id
    is_admin = user.get("RoleID") == 1
    user_id = user.get("UserID")

    if not is_admin:
        await support_join(f"support:user:{user_id}", websocket)
    else:
        await support_join("support:admin", websocket)

    try:
        while True:
            data = await websocket.receive_json()
            t = data.get("type")

            if t == "join":
                room = data.get("room")
                if is_admin and room and room.startswith("support:user:"):
                    await support_join(room, websocket)

            elif t == "typing":
                room = data.get("room")
                thread_id = data.get("thread_id")
                if thread_id:
                    # Broadcast typing indicator
                    typing_payload = {
                        "type": "support:typing",
                        "thread_id": thread_id,
                        "user_id": user_id,
                        "is_admin": 1 if is_admin else 0
                    }
                    
                    # Gửi cho admin nếu user đang gõ
                    if not is_admin:
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
                        "user_id": user_id,
                        "is_admin": is_admin,
                        "full_name": user.get("FullName", "Unknown")
                    })

    except WebSocketDisconnect:
        await support_leave(websocket)
