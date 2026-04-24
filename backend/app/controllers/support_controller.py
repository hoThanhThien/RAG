import json
import os
import re
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Any, Dict, List
from app.dependencies.auth_dependencies import get_current_user, require_admin
from app.schemas.support_schema import MessageIn, MessageOut, ThreadOut
from app.database import get_db_connection  # ✅ Dùng pymysql connection
from app.services.rag.intents import BEACH_TERMS, INTERNATIONAL_TERMS, MOUNTAIN_TERMS, RELAX_TERMS, extract_query_intents, normalize_text, source_match_text
from app.services.rag.bm25 import BM25Index
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


def _public_api_base_url() -> str:
    return (
        os.getenv("SUPPORT_PUBLIC_API_BASE_URL")
        or os.getenv("PUBLIC_API_BASE_URL")
        or os.getenv("BACKEND_PUBLIC_BASE_URL")
        or "http://localhost:8000"
    ).rstrip("/")


def _absolute_image_url(image_url: str) -> str:
    value = str(image_url or "").strip()
    if not value:
        return "https://placehold.co/600x400?text=Tour"
    if value.startswith(("http://", "https://")):
        return value
    if not value.startswith("/"):
        value = f"/{value}"
    return f"{_public_api_base_url()}{value}"


def _truncate_support_description(value: str, max_chars: int = 140) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return "Tour nổi bật đang được nhiều khách quan tâm."
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip(" ,.;:") + "..."


def _strip_segment_label(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    text = re.sub(r"\s*\((Khách[^)]*)\)(?=[:.!?]|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def _serialize_support_payload(mode: str, message: str, tours: List[Dict[str, Any]] | None = None) -> str:
    payload: Dict[str, Any] = {
        "mode": mode,
        "message": str(message or "").strip(),
    }
    if mode == "suggest_tour":
        payload["tours"] = tours or []
    return json.dumps(payload, ensure_ascii=False)


def _match_any_phrase(text: str, phrases: List[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _match_any_pattern(text: str, patterns: List[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _classify_support_intent(prompt: str) -> str:
    text = normalize_text(prompt)
    if not text:
        return "chitchat"

    chitchat_phrases = [
        "chan qua", "chan", "buon", "met", "te", "that vong", "khong on", "do qua",
        "xin chao", "chao", "hello", "hi", "helo", "cam on", "thanks", "thank you",
    ]
    consulting_phrases = [
        "co gi choi", "an gi", "review", "kinh nghiem", "thoi tiet", "khi hau", "mua nao",
        "co dep khong", "lich su", "van hoa", "dac san", "di chuyen", "o dau ngon", "nen an gi",
        "choi gi", "tham quan gi", "co gi hay", "co gi vui", "noi tieng ve gi",
    ]
    suggestion_phrases = [
        "goi y", "de xuat", "recommend", "nen di dau", "di dau", "di dau dep", "di dau choi", "cuoi tuan",
        "nghi le", "muon di", "dinh di", "can tim", "phu hop voi", "hop voi", "tour nao",
        "dat tour", "tour cho", "nghi duong", "tranh nong", "doi gio",
    ]
    suggestion_patterns = [
        r"\b(nen|muon|dinh|can|tim)\b.*\b(di|choi|nghi|du lich)\b",
        r"\b(di|choi|nghi)\b.*\b(o dau|cho nao|noi nao)\b",
        r"\b(o dau|cho nao|noi nao)\b.*\b(dep|hop|ly tuong)\b",
        r"\b(phu hop|hop)\b.*\b(gia dinh|cap doi|2 nguoi|tre em|ban be|minh)\b",
        r"\b(ngan sach|chi phi|gia)\b.*\b(nao|bao nhieu|phu hop)\b",
    ]

    if _match_any_phrase(text, chitchat_phrases):
        return "chitchat"

    if _match_any_phrase(text, suggestion_phrases) or _match_any_pattern(text, suggestion_patterns):
        return "suggest_tour"

    if re.match(r"^(di|den|toi)\s+[a-z0-9 ]+$", text) and len(text.split()) <= 4:
        return "suggest_tour"

    if _match_any_phrase(text, consulting_phrases):
        return "consulting"

    intents = extract_query_intents(prompt)
    if any(intents.get(key) for key in ("beach", "mountain", "family", "budget", "premium", "international", "hot_weather", "relax", "similar")):
        return "suggest_tour"

    if "?" in str(prompt or ""):
        return "consulting"

    if len(text.split()) <= 4:
        return "consulting"

    return "consulting"


def _build_conversational_support_reply(prompt: str) -> str | None:
    text = normalize_text(prompt)
    if not text:
        return None

    negative_cues = ["chan qua", "chan", "buon", "met", "te", "that vong", "khong on", "do qua"]
    greeting_cues = ["xin chao", "chao", "hello", "hi", "helo"]
    thanks_cues = ["cam on", "thanks", "thank you"]

    if any(cue in text for cue in negative_cues):
        return (
            "Mình vẫn ở đây để tư vấn hỗ trợ cho bạn. Nếu gợi ý trước chưa đúng ý, "
            "bạn nói rõ thêm điểm đến, ngân sách hoặc kiểu chuyến đi mong muốn để mình tư vấn sát hơn nhé."
        )

    if any(cue == text or text.startswith(f"{cue} ") for cue in greeting_cues):
        return (
            "Chào bạn, mình vẫn hỗ trợ tư vấn du lịch bình thường. "
            "Bạn có thể hỏi về điểm đến, chi phí, lịch trình hoặc nhờ mình gợi ý tour phù hợp."
        )

    if any(cue in text for cue in thanks_cues):
        return "Mình vẫn sẵn sàng hỗ trợ. Nếu cần, bạn cứ hỏi tiếp về tour, chi phí, lịch trình hoặc thời điểm đi nhé."

    return None


def _support_topic_tokens(prompt: str) -> List[str]:
    text = normalize_text(prompt)
    stopwords = {
        "o", "la", "co", "gi", "choi", "an", "review", "kinh", "nghiem", "mua", "nao", "thoi", "tiet",
        "di", "dau", "nen", "toi", "voi", "va", "hay", "khong", "dep", "the", "nao", "duoc", "khong", "vui",
    }
    tokens = [token for token in re.findall(r"[a-z0-9]+", text) if len(token) > 1 and token not in stopwords]
    alias_map = {
        "thai": ["thai lan", "bangkok", "pattaya"],
        "han": ["han quoc", "seoul", "nami"],
        "nhat": ["nhat ban", "tokyo", "phu si", "phu sy"],
        "ninh": ["ninh binh"],
    }
    expanded_tokens: List[str] = []
    for token in tokens:
        expanded_tokens.append(token)
        expanded_tokens.extend(alias_map.get(token, []))
    if "thai lan" in text:
        expanded_tokens.extend(["thai lan", "bangkok", "pattaya"])
    if "ninh binh" in text:
        expanded_tokens.append("ninh binh")
    return list(dict.fromkeys(expanded_tokens))


def _source_matches_support_topic(source: Dict[str, Any], topic_tokens: List[str]) -> bool:
    if not topic_tokens:
        return True
    match_text = source_match_text(source)
    for token in topic_tokens:
        normalized_token = normalize_text(token)
        if not normalized_token:
            continue
        if " " in normalized_token:
            if normalized_token in match_text:
                return True
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(normalized_token)}(?![a-z0-9])", match_text):
            return True
    return False


def _is_ambiguous_short_query(prompt: str) -> bool:
    text = normalize_text(prompt)
    if not text:
        return False

    words = text.split()
    if len(words) != 1:
        return False

    token = words[0]
    if len(token) >= 4:
        return False

    if _classify_support_intent(prompt) == "chitchat":
        return False

    return True


def _is_followup_query(prompt: str) -> bool:
    text = normalize_text(prompt)
    followup_phrases = [
        "lich trinh", "chi phi", "gia", "bao nhieu", "chi tiet", "thoi gian", "may ngay",
        "di bao lau", "o dau", "co gi dac biet", "ve cai do", "ve cai nay",
    ]
    return _match_any_phrase(text, followup_phrases)


def _extract_support_payload_summary(content: str) -> str:
    raw = str(content or "").strip()
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
    except Exception:
        return raw

    if not isinstance(parsed, dict):
        return raw

    message = str(parsed.get("message") or "").strip()
    tours = parsed.get("tours") if isinstance(parsed.get("tours"), list) else []
    tour_names = [str(tour.get("name") or "").strip() for tour in tours if isinstance(tour, dict) and str(tour.get("name") or "").strip()]
    if tour_names:
        return f"{message} {'; '.join(tour_names[:3])}".strip()
    return message or raw


def _load_recent_thread_context(thread_id: int, current_prompt: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sender_id, is_admin, content
                FROM support_message
                WHERE thread_id = %s
                ORDER BY id DESC
                LIMIT 6
                """,
                (thread_id,),
            )
            rows = cur.fetchall() or []
    finally:
        conn.close()

    recent: List[Dict[str, Any]] = []
    skipped_current = False
    normalized_current = normalize_text(current_prompt)
    for row in rows:
        content = str((row or {}).get("content") or "").strip()
        if not content:
            continue
        if not skipped_current and normalize_text(content) == normalized_current and not (row or {}).get("is_admin"):
            skipped_current = True
            continue
        recent.append({
            "is_admin": bool((row or {}).get("is_admin")),
            "content": content,
        })
    return recent


def _compose_effective_support_query(prompt: str, recent_messages: List[Dict[str, Any]]) -> str:
    if not _is_followup_query(prompt) or not recent_messages:
        return prompt

    previous_user = ""
    previous_ai = ""
    for item in recent_messages:
        if item.get("is_admin") and not previous_ai:
            previous_ai = _extract_support_payload_summary(item.get("content") or "")
        if not item.get("is_admin") and not previous_user:
            previous_user = str(item.get("content") or "").strip()
        if previous_user and previous_ai:
            break

    context_parts = [part for part in [previous_user, previous_ai] if part]
    if not context_parts:
        return prompt
    return f"Ngữ cảnh trước: {' | '.join(context_parts)}. Câu hỏi hiện tại: {prompt}"


def _rerank_support_sources(prompt: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not sources:
        return sources
    documents = [source_match_text(s) for s in sources]
    bm25 = BM25Index(documents)
    query = normalize_text(prompt)
    ranked = bm25.search(query, top_n=len(sources))
    if not ranked:
        return sources
    ranked_indices = {idx for idx, _ in ranked}
    reranked = [sources[idx] for idx, _ in ranked]
    reranked += [s for i, s in enumerate(sources) if i not in ranked_indices]
    return reranked


def _filter_support_sources_by_intent(sources: List[Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
    intents = extract_query_intents(prompt)
    has_hard_intent = any(intents.get(key) for key in ("beach", "mountain", "international", "hot_weather"))
    if not has_hard_intent:
        return sources

    def has_any(text: str, terms: List[str]) -> bool:
        return any(term in text for term in terms)

    filtered: List[Dict[str, Any]] = []
    for source in sources:
        text = source_match_text(source)
        match = True
        if intents.get("international"):
            match = match and has_any(text, INTERNATIONAL_TERMS)
        if intents.get("beach"):
            match = match and has_any(text, BEACH_TERMS)
        if intents.get("mountain"):
            match = match and has_any(text, MOUNTAIN_TERMS)
        if intents.get("hot_weather"):
            match = match and (has_any(text, BEACH_TERMS) or has_any(text, MOUNTAIN_TERMS) or has_any(text, RELAX_TERMS))
        if match:
            filtered.append(source)

    return filtered


def _matches_support_card_intent(prompt: str, row: Dict[str, Any], source: Dict[str, Any]) -> bool:
    intents = extract_query_intents(prompt)
    has_hard_intent = any(intents.get(key) for key in ("beach", "mountain", "international", "hot_weather"))
    specific_topic_tokens = _support_topic_tokens(prompt)

    card_text = normalize_text(
        " ".join(
            [
                str(row.get("title") or source.get("title") or ""),
                str(row.get("description") or ""),
                str(source.get("location") or ""),
                str(source.get("category_name") or ""),
            ]
        )
    )

    def has_any(terms: List[str]) -> bool:
        return any(term in card_text for term in terms)

    if intents.get("international") and not has_any(INTERNATIONAL_TERMS):
        return False
    if intents.get("beach") and not has_any(BEACH_TERMS):
        return False
    if intents.get("mountain") and not has_any(MOUNTAIN_TERMS):
        return False
    if intents.get("hot_weather") and not (has_any(BEACH_TERMS) or has_any(MOUNTAIN_TERMS) or has_any(RELAX_TERMS)):
        return False

    if specific_topic_tokens:
        topic_source = {
            "title": row.get("title") or source.get("title"),
            "location": source.get("location") or row.get("description"),
            "category_name": source.get("category_name"),
            "text": row.get("description") or source.get("text"),
        }
        if not _source_matches_support_topic(topic_source, specific_topic_tokens):
            return False

    if not has_hard_intent and not specific_topic_tokens:
        return True
    return True


def _fetch_support_tour_cards(conn, sources: List[Dict[str, Any]], prompt: str, top_k: int = 3) -> List[Dict[str, Any]]:
    ordered_ids: List[int] = []
    source_map: Dict[int, Dict[str, Any]] = {}
    for source in sources:
        try:
            tour_id = int(source.get("tour_id") or 0)
        except Exception:
            tour_id = 0
        if tour_id <= 0 or tour_id in source_map:
            continue
        ordered_ids.append(tour_id)
        source_map[tour_id] = source

    if not ordered_ids:
        return []

    placeholders = ",".join(["%s"] * len(ordered_ids))
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                t.TourID AS tour_id,
                t.Title AS title,
                t.Price AS price,
                t.Description AS description,
                COALESCE(
                    (
                        SELECT p.ImageURL
                        FROM photo p
                        WHERE p.TourID = t.TourID
                        ORDER BY p.IsPrimary DESC, p.PhotoID DESC
                        LIMIT 1
                    ),
                    ''
                ) AS image_url
            FROM tour t
            WHERE t.TourID IN ({placeholders})
            """,
            ordered_ids,
        )
        rows = cur.fetchall() or []

    row_map = {int(row["tour_id"]): row for row in rows}
    cards: List[Dict[str, Any]] = []
    for tour_id in ordered_ids:
        row = row_map.get(tour_id)
        source = source_map.get(tour_id) or {}
        if not row:
            continue
        if not _matches_support_card_intent(prompt, row, source):
            continue
        price_value = float(row.get("price") or source.get("price") or 0.0)
        cards.append(
            {
                "id": str(tour_id),
                "name": str(row.get("title") or source.get("title") or "Tour"),
                "price": f"{price_value:,.0f} VND" if price_value > 0 else "Liên hệ",
                "image": _absolute_image_url(str(row.get("image_url") or "")),
                "description": _truncate_support_description(
                    str(row.get("description") or source.get("text") or source.get("title") or "")
                ),
                "url": f"/tours/{tour_id}",
            }
        )
        if len(cards) >= top_k:
            break
    return cards


def should_use_ai_support(content: str) -> bool:
    if not content or not content.strip():
        return False

    text = normalize_text(content)
    return any(char.isalnum() for char in text)


def build_ai_support_reply(user_id: int, prompt: str, thread_id: int | None = None) -> str:
    try:
        # 1. Block ambiguous single-char queries
        if _is_ambiguous_short_query(prompt):
            return _serialize_support_payload(
                "consulting",
                "Mình chưa chắc bạn đang muốn hỏi về địa điểm nào. Bạn nói rõ hơn giúp mình, ví dụ tên điểm đến đầy đủ hoặc nhu cầu như đi đâu, lịch trình hay chi phí nhé.",
            )

        # 2. Chitchat — handle without RAG
        intent = _classify_support_intent(prompt)
        if intent == "chitchat":
            reply = _build_conversational_support_reply(prompt)
            if reply:
                return _serialize_support_payload("chitchat", reply)

        # 3. Build effective query (enriched with thread context for follow-ups)
        recent_messages = _load_recent_thread_context(thread_id, prompt) if thread_id else []
        effective_query = _compose_effective_support_query(prompt, recent_messages)

        # 4. RAG — source of truth
        rec = answer_chat(query=effective_query, user_id=user_id, top_k=5)
        answer = (rec.get("answer") or "").strip()
        sources = _rerank_support_sources(
            prompt,
            _filter_support_sources_by_intent(rec.get("sources") or [], prompt),
        )

        # 5. suggest_tour: attach cards, keep RAG answer as message
        if intent == "suggest_tour":
            conn = get_db_connection()
            try:
                tours = _fetch_support_tour_cards(conn, sources, prompt, top_k=3)
            finally:
                conn.close()
            message = answer if answer else (
                "Hiện chưa có tour phù hợp, bạn muốn mình gợi ý theo ngân sách hoặc địa điểm khác không?"
            )
            return _serialize_support_payload("suggest_tour", message, tours)

        # 6. consulting — return RAG answer as-is, no rewriting
        if not answer:
            answer = "Hiện chưa có dữ liệu phù hợp với câu hỏi của bạn."
        return _serialize_support_payload("consulting", answer)

    except Exception as e:
        print(f"⚠️ AI support recommendation error: {e}")
        return _serialize_support_payload(
            "consulting",
            "Mình có thể hỗ trợ tư vấn thêm. Bạn hãy nói rõ hơn địa điểm, nhu cầu hoặc ngân sách để mình hỗ trợ chính xác hơn.",
        )


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
            auto_msg = build_ai_support_reply(owner_user_id, prompt, thread_id=thread_id)
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


