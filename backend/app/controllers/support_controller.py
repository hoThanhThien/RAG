from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
import unicodedata
from app.dependencies.auth_dependencies import get_current_user, require_admin
from app.schemas.support_schema import MessageIn, MessageOut, ThreadOut
from app.database import get_db_connection  # ✅ Dùng pymysql connection
from app.services.rag_service import answer_chat


def to_utc_iso(dt):
    if not dt:
        return None
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

router = APIRouter(prefix="/support", tags=["support"])


def is_admin_user(user):
    role_name = str(user.get("RoleName", "")).strip().lower()
    return role_name == "admin" or user.get("RoleID") == 1


def normalize_support_text(value: str) -> str:
    text = " ".join(str(value or "").lower().split())
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def should_use_ai_support(content: str) -> bool:
    """
    Returns True when the AI should respond.
    Rules (in priority order):
      1. Has '?' → always ask AI
      2. Sentence has > 3 words → treat as a real query
      3. Short message matches any travel keyword
    """
    if not content or not content.strip():
        return False

    # Rule 1: explicit question
    if "?" in content:
        return True

    text = normalize_support_text(content)
    if not text or len(text) < 2:
        return False

    # Rule 2: long enough to be a real query
    if len(text.split()) > 3:
        return True

    # Rule 3: short message keyword check
    keywords = [
        # Tour / travel intent
        "goi y", "recommend", "de xuat", "tour nao", "phu hop",
        "du lich", "di dau", "muon di", "tu van", "tour",
        "gia dinh", "gia re", "nghi duong", "bien", "nuoc ngoai",
        "quoc te", "nong qua", "troi nong", "mat me", "tranh nong", "doi gio",
        "luxury", "budget", "family", "beach", "mountain",
        # Destinations (normalized — no diacritics)
        "chau au", "chau a", "nhat ban", "han quoc", "thai lan",
        "singapore", "malaysia", "indonesia", "philippines",
        "tay ban nha", "anh quoc", "ha lan",
        "tho nhi ky", "dubai", "australia", "canada",
        "trung quoc", "bac kinh", "thuong hai",
        "ha long", "sa pa", "ninh binh", "hoi an", "da nang",
        "phu quoc", "nha trang", "da lat", "hue", "vung tau",
        "bangkok", "pattaya", "bali", "tokyo",
        # Question / info words
        "bao nhieu", "gia tour", "chi phi", "khi nao", "lich trinh",
        "bao lau", "may ngay", "con cho", "dat cho", "thanh toan",
        "uu dai", "khuyen mai", "giam gia",
    ]
    return any(kw in text for kw in keywords)


def build_ai_support_reply(user_id: int, prompt: str) -> str:
    try:
        rec = answer_chat(query=prompt, user_id=user_id, top_k=3)
        recommendations = rec.get("sources") or []
        answer = (rec.get("answer") or "").strip()

        lines = [" Gợi ý cho bạn:"]
        if answer:
            lines.append(answer)

        has_bullets_in_answer = "\n- " in answer or "\n• " in answer

        if recommendations and not has_bullets_in_answer:
            lines.append("Tour phù hợp:")
            for item in recommendations[:3]:
                price = float(item.get("price") or 0)
                price_label = f"{price:,.0f}đ" if price > 0 else "Liên hệ"
                lines.append(f"• {item.get('title')} - {item.get('location')} - {price_label}")

        lines.append("Nếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.")
        return "\n".join(lines)
    except Exception as e:
        print(f"⚠️ AI support recommendation error: {e}")
        return " Mình có thể gợi ý tour theo nhu cầu của bạn. Hãy thử nói rõ hơn như: tour gia đình, tour biển, tour giá rẻ hoặc tour nghỉ dưỡng."


def queue_ai_support_reply(thread_id: int, owner_user_id: int, full_name: str, prompt: str):
    db = get_db_connection()
    cur = db.cursor()
    try:
        auto_msg = None
        auto_sender_name = "Trợ lý AI"

        cur.execute(
            "SELECT COUNT(*) as admin_count FROM support_message WHERE thread_id = %s AND is_admin = 1",
            (thread_id,)
        )
        result = cur.fetchone()
        admin_count = int(result.get("admin_count") or 0) if result else 0

        if should_use_ai_support(prompt) or admin_count > 0:
            # Always respond with AI when: query matches travel keywords OR thread already has prior replies
            auto_msg = build_ai_support_reply(owner_user_id, prompt)
        else:
            # First message with no travel intent → show greeting
            auto_msg = (
                f"Chào {full_name} 👋 Mình là trợ lý AI hỗ trợ du lịch. "
                "Bạn có thể hỏi ngay như: gợi ý tour gia đình, tour biển, tour giá rẻ hoặc tour nghỉ dưỡng."
            )

        if not auto_msg:
            return

        cur.execute(
            "INSERT INTO support_message (thread_id, sender_id, is_admin, content) VALUES (%s, NULL, 1, %s)",
            (thread_id, auto_msg)
        )
        db.commit()
        auto_msg_id = cur.lastrowid

        cur.execute("SELECT created_at FROM support_message WHERE id = %s", (auto_msg_id,))
        auto_created_row = cur.fetchone()
        auto_created_at = to_utc_iso(auto_created_row["created_at"]) if auto_created_row else None

        from app.controllers.websocket_controller import ws_broadcast_safe

        auto_payload = {
            "type": "support:new_message",
            "thread_id": thread_id,
            "message": {
                "id": auto_msg_id,
                "sender_id": None,
                "is_admin": 1,
                "content": auto_msg,
                "full_name": auto_sender_name,
                "thread_id": thread_id,
                "created_at": auto_created_at
            }
        }

        ws_broadcast_safe(f"support:user:{owner_user_id}", auto_payload)
        ws_broadcast_safe("support:admin", auto_payload)
    except Exception as e:
        print(f"⚠️ queue_ai_support_reply error: {e}")
    finally:
        cur.close()
        db.close()

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
                "created_at": to_utc_iso(row["created_at"]),
                "last_content": row["last_content"] or "Chưa có tin nhắn",
                "last_time": to_utc_iso(row["last_time"]),
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
        if not is_admin_user(user) and row["user_id"] != user["UserID"]:
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
    if not is_admin_user(user) and owner["user_id"] != user["UserID"]:
        cur.close()
        raise HTTPException(403, "Forbidden")

    cur.execute("""
        SELECT m.id, m.sender_id, m.is_admin, m.content, m.created_at, 
               CASE 
                   WHEN m.sender_id IS NULL AND m.is_admin = 1 THEN 'Trợ lý AI'
                   ELSE COALESCE(u.FullName, 'Hệ thống')
               END as FullName
        FROM support_message m
        LEFT JOIN user u ON m.sender_id = u.UserID
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
            "created_at": to_utc_iso(row["created_at"]),
            "full_name": row["FullName"]
        })
    cur.close()
    return messages

# 🟢 Gửi tin nhắn mới vào thread
# 🟢 Gửi tin nhắn mới vào thread
@router.post("/threads/{thread_id}/messages")
def post_message(
    thread_id: int,
    body: MessageIn,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    db=Depends(get_db_connection),
):
    cur = db.cursor()
    try:
        # 📌 Lấy user_id chủ sở hữu thread
        cur.execute("SELECT user_id FROM support_thread WHERE id=%s", (thread_id,))
        owner = cur.fetchone()
        if not owner:
            raise HTTPException(404, "Thread not found")
        
        owner_user_id = owner["user_id"]

        if not is_admin_user(user) and owner_user_id != user["UserID"]:
            raise HTTPException(403, "Forbidden")

        is_admin = 1 if is_admin_user(user) else 0

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
        created_at = to_utc_iso(created_at_row["created_at"]) if created_at_row else None

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

        # ✅ Sinh phản hồi AI nền để không làm treo thao tác gửi tin nhắn
        if is_admin == 0:
            background_tasks.add_task(
                queue_ai_support_reply,
                thread_id,
                owner_user_id,
                full_name,
                body.content,
            )

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


