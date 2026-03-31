from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.dependencies.auth_dependencies import get_current_user, require_admin
from app.schemas.support_schema import MessageIn, MessageOut, ThreadOut
from app.database import get_db_connection  # ✅ Dùng pymysql connection

router = APIRouter(prefix="/support", tags=["support"])

# 🟢 Mở hoặc tạo thread
@router.post("/threads/open-or-create")
def open_or_create_thread(user=Depends(get_current_user), db=Depends(get_db_connection)):
    cur = db.cursor()
    cur.execute("SELECT id FROM support_thread WHERE user_id=%s", (user["UserID"],))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO support_thread (user_id) VALUES (%s)", (user["UserID"],))
        db.commit()
        thread_id = cur.lastrowid
    else:
        thread_id = row["id"]
    cur.close()
    return {"thread_id": thread_id}

# 🟢 Danh sách tất cả các thread (dành cho admin)
@router.get("/threads", response_model=List[ThreadOut], dependencies=[Depends(require_admin)])
def list_threads(db=Depends(get_db_connection)):
    cur = db.cursor()
    sql = """
    SELECT t.id AS thread_id, t.user_id, u.FullName AS full_name,
           (SELECT content FROM support_message m WHERE m.thread_id=t.id ORDER BY m.id DESC LIMIT 1) AS last_content,
           (SELECT created_at FROM support_message m WHERE m.thread_id=t.id ORDER BY m.id DESC LIMIT 1) AS last_time
    FROM support_thread t
    LEFT JOIN user u ON t.user_id = u.UserID
    ORDER BY last_time DESC, t.id DESC
    """
    cur.execute(sql)
    items = cur.fetchall()
    result = []
    for row in items:
        result.append({
        "thread_id": row["thread_id"],
        "user_id": row["user_id"],
        "full_name": row["full_name"] or "Ẩn danh",
        "last_content": row["last_content"] or None,
        "last_time": row["last_time"] if row["last_time"] else None
    })


    cur.close()
    return result

# 🆕 Lấy tất cả threads của user hiện tại (ĐẶT TRƯỚC /{thread_id})
@router.get("/threads/my/all")
def get_my_threads(user=Depends(get_current_user), db=Depends(get_db_connection)):
    cur = db.cursor()
    try:
        sql = """
        SELECT t.id AS thread_id, t.created_at,
               (SELECT content FROM support_message m WHERE m.thread_id=t.id ORDER BY m.id DESC LIMIT 1) AS last_content,
               (SELECT created_at FROM support_message m WHERE m.thread_id=t.id ORDER BY m.id DESC LIMIT 1) AS last_time,
               (SELECT COUNT(*) FROM support_message m WHERE m.thread_id=t.id) AS message_count
        FROM support_thread t
        WHERE t.user_id = %s
        ORDER BY last_time DESC, t.id DESC
        """
        cur.execute(sql, (user["UserID"],))
        rows = cur.fetchall()
        
        threads = []
        for row in rows:
            threads.append({
                "thread_id": row["thread_id"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "last_content": row["last_content"] or "Chưa có tin nhắn",
                "last_time": row["last_time"].isoformat() if row["last_time"] else None,
                "message_count": row["message_count"]
            })
        
        return threads
    except Exception as e:
        print(f"❌ Error getting threads: {e}")
        raise HTTPException(500, f"Không thể lấy danh sách threads: {str(e)}")
    finally:
        cur.close()
        db.close()


# 🆕 Tạo thread mới (luôn tạo thread mới)
@router.post("/threads/new")
def create_new_thread(user=Depends(get_current_user), db=Depends(get_db_connection)):
    cur = db.cursor()
    try:
        # Luôn tạo thread mới (đã xóa UNIQUE constraint)
        cur.execute("INSERT INTO support_thread (user_id) VALUES (%s)", (user["UserID"],))
        db.commit()
        thread_id = cur.lastrowid
        return {
            "thread_id": thread_id, 
            "message": "Đã tạo cuộc trò chuyện mới"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Không thể tạo thread: {str(e)}")
    finally:
        cur.close()
        db.close()

# support_controller.py - Route động (ĐẶT SAU các route cụ thể)
@router.get("/threads/{thread_id}")
def get_thread_info(thread_id: int, db=Depends(get_db_connection), user=Depends(get_current_user)):
    cur = db.cursor()
    try:
        cur.execute("SELECT user_id FROM support_thread WHERE id = %s", (thread_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Thread not found")
        return {"user_id": row["user_id"]}
    finally:
        cur.close()
        db.close()

# 🆕 Xóa thread (chỉ user sở hữu hoặc admin mới được xóa)
@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: int, user=Depends(get_current_user), db=Depends(get_db_connection)):
    cur = db.cursor()
    try:
        # Check ownership
        cur.execute("SELECT user_id FROM support_thread WHERE id = %s", (thread_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(404, "Thread không tồn tại")
        
        # Only owner or admin can delete
        if user["RoleID"] != 1 and row["user_id"] != user["UserID"]:
            raise HTTPException(403, "Bạn không có quyền xóa cuộc trò chuyện này")
        
        # Delete messages first (foreign key constraint)
        cur.execute("DELETE FROM support_message WHERE thread_id = %s", (thread_id,))
        
        # Delete thread
        cur.execute("DELETE FROM support_thread WHERE id = %s", (thread_id,))
        db.commit()
        
        return {"message": "Đã xóa cuộc trò chuyện thành công"}
    finally:
        cur.close()
        db.close()


# 🟢 Lấy tin nhắn trong một thread
@router.get("/threads/{thread_id}/messages", response_model=List[MessageOut])
def get_messages(thread_id: int, user=Depends(get_current_user), db=Depends(get_db_connection)):
    cur = db.cursor()
    cur.execute("SELECT user_id FROM support_thread WHERE id=%s", (thread_id,))
    owner = cur.fetchone()
    if not owner:
        cur.close()
        raise HTTPException(404, "Thread not found")
    if user["RoleID"] != 1 and owner["user_id"] != user["UserID"]:
        cur.close()
        raise HTTPException(403, "Forbidden")

    cur.execute("""
        SELECT m.id, m.sender_id, m.is_admin, m.content, m.created_at, u.FullName
        FROM support_message m
        JOIN user u ON m.sender_id = u.UserID
        WHERE m.thread_id=%s
        ORDER BY m.id ASC
        LIMIT 200
    """, (thread_id,))

    msgs_raw = cur.fetchall()
    messages = []
    for row in msgs_raw:
        messages.append({
            "id": row["id"],
            "sender_id": row["sender_id"],
            "is_admin": row["is_admin"],
            "content": row["content"],
            "created_at": row["created_at"].isoformat(),
            "full_name": row["FullName"]
        })
    cur.close()
    return messages

# 🟢 Gửi tin nhắn mới vào thread
# 🟢 Gửi tin nhắn mới vào thread
@router.post("/threads/{thread_id}/messages")
def post_message(thread_id: int, body: MessageIn, user=Depends(get_current_user), db=Depends(get_db_connection)):
    cur = db.cursor()
    try:
        # 📌 Lấy user_id chủ sở hữu thread
        cur.execute("SELECT user_id FROM support_thread WHERE id=%s", (thread_id,))
        owner = cur.fetchone()
        if not owner:
            raise HTTPException(404, "Thread not found")
        
        owner_user_id = owner["user_id"]

        if user["RoleID"] != 1 and owner_user_id != user["UserID"]:
            raise HTTPException(403, "Forbidden")

        is_admin = 1 if user["RoleID"] == 1 else 0

        # 💾 Ghi tin nhắn vào DB
        cur.execute(
            "INSERT INTO support_message (thread_id, sender_id, is_admin, content) VALUES (%s,%s,%s,%s)",
            (thread_id, user["UserID"], is_admin, body.content)
        )
        db.commit()
        msg_id = cur.lastrowid

        # 🧠 Lấy tên người gửi và thời gian
        cur.execute("SELECT FullName FROM user WHERE UserID = %s", (user["UserID"],))
        full_name_row = cur.fetchone()
        full_name = full_name_row["FullName"] if full_name_row else "Unknown"
        
        # Lấy created_at từ DB
        cur.execute("SELECT created_at FROM support_message WHERE id = %s", (msg_id,))
        created_at_row = cur.fetchone()
        created_at = created_at_row["created_at"].isoformat() if created_at_row else None

        # 📡 Gửi tin nhắn WebSocket
        from app.controllers.websocket_controller import ws_broadcast_safe

        message_payload = {
            "type": "support:new_message",
            "thread_id": thread_id,
            "message": {
                "id": msg_id,
                "sender_id": user["UserID"],
                "is_admin": is_admin,
                "content": body.content,
                "full_name": full_name,
                "thread_id": thread_id,
                "created_at": created_at
            }
        }

        ws_broadcast_safe(f"support:user:{owner_user_id}", message_payload)
        ws_broadcast_safe("support:admin", message_payload)

        # ✅ ✅ ✅ Tự động gửi phản hồi nếu admin chưa từng trả lời
        if is_admin == 0:  # Chỉ thực hiện nếu là user gửi
            cur.execute(
                "SELECT COUNT(*) as admin_count FROM support_message WHERE thread_id = %s AND is_admin = 1",
                (thread_id,)
            )
            result = cur.fetchone()
            if result["admin_count"] == 0:
                auto_msg = f"Chào {full_name} 👋🥰, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!"
                cur.execute(
                    "INSERT INTO support_message (thread_id, sender_id, is_admin, content) VALUES (%s, NULL, 1, %s)",
                    (thread_id, auto_msg)
                )
                db.commit()
                auto_msg_id = cur.lastrowid
                
                # Lấy created_at của auto message
                cur.execute("SELECT created_at FROM support_message WHERE id = %s", (auto_msg_id,))
                auto_created_row = cur.fetchone()
                auto_created_at = auto_created_row["created_at"].isoformat() if auto_created_row else None

                auto_payload = {
                    "type": "support:new_message",
                    "thread_id": thread_id,
                    "message": {
                        "id": auto_msg_id,
                        "sender_id": None,
                        "is_admin": 1,
                        "content": auto_msg,
                        "full_name": "Hệ thống",
                        "thread_id": thread_id,
                        "created_at": auto_created_at
                    }
                }

                # Gửi auto-reply về cho user (KHÔNG gửi cho admin)
                ws_broadcast_safe(f"support:user:{owner_user_id}", auto_payload)

        # Trả về thông tin tin nhắn vừa tạo
        return {
            "ok": True,
            "id": msg_id,
            "sender_id": user["UserID"],
            "is_admin": is_admin,
            "content": body.content,
            "full_name": full_name,
            "created_at": created_at,
            "thread_id": thread_id
        }

    finally:
        cur.close()
        db.close()


