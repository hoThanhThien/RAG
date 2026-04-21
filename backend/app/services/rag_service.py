from __future__ import annotations

import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

from app.database import get_db_connection
from app.services.customer_segmentation_service import get_user_segment

try:
    import faiss  # type: ignore
except Exception:
    faiss = None


BASE_DIR = Path(__file__).resolve().parents[2]
RAG_DIR = BASE_DIR / "rag_store"
INDEX_FILE = RAG_DIR / "tour_index.faiss"
METADATA_FILE = RAG_DIR / "chunks.json"
STATE_FILE = RAG_DIR / "state.json"
VECTORIZER_FILE = RAG_DIR / "tfidf_vectorizer.pkl"
VECTORS_FILE = RAG_DIR / "vectors.npy"

DEFAULT_CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

_RAG_CACHE: Dict[str, Any] = {
    "loaded": False,
    "loaded_at": 0.0,
    "chunks": [],
    "state": {},
    "vectorizer": None,
    "vectors": None,
    "index": None,
}

_BEACH_TERMS = ["biển", "bien", "beach", "island", "coast", "phú quốc", "phu quoc", "nha trang", "đà nẵng", "da nang", "hạ long", "ha long", "quy nhơn", "quy nhon", "côn đảo", "con dao", "vũng tàu", "vung tau"]
_MOUNTAIN_TERMS = ["núi", "nui", "mountain", "sapa", "sa pa", "đà lạt", "da lat", "mộc châu", "moc chau", "tam đảo", "tam dao"]
_FAMILY_TERMS = ["gia đình", "gia dinh", "family", "trẻ em", "tre em", "kids"]
_BUDGET_TERMS = ["giá rẻ", "gia re", "giá tốt", "gia tot", "tiết kiệm", "tiet kiem", "budget", "cheap", "affordable", "sale"]
_PREMIUM_TERMS = ["cao cấp", "cao cap", "premium", "luxury", "sang trọng", "sang trong"]


def _ensure_store_dir() -> None:
    RAG_DIR.mkdir(parents=True, exist_ok=True)


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _normalize_whitespace(text: Any) -> str:
    return " ".join(str(text or "").split())


def _normalize_lower(text: Any) -> str:
    return _normalize_whitespace(text).lower()


def _split_text(text: str, chunk_size: int = 120, overlap: int = 24) -> List[str]:
    words = _normalize_whitespace(text).split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        piece = " ".join(words[start:end]).strip()
        if piece:
            chunks.append(piece)
        if end >= len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _segment_instruction(segment: Optional[Dict[str, Any]]) -> str:
    segment_name = str((segment or {}).get("segment_name") or "Khách mới")
    mapping = {
        "Khách mua nhiều": "Ưu tiên tour cao cấp, trải nghiệm chất lượng cao, lịch trình thoải mái và dịch vụ tốt.",
        "Khách săn sale": "Ưu tiên tour giá tốt, tour đang đáng tiền, nêu rõ mức giá để người dùng dễ so sánh.",
        "Khách ít tương tác": "Ưu tiên tour phổ biến, dễ quyết định, mô tả ngắn gọn và ít rủi ro.",
        "Khách mới": "Ưu tiên tour dễ đi, được nhiều người chọn, giải thích đơn giản.",
        "Khách trung thành": "Ưu tiên tour mới, tour nổi bật, hoặc tour phù hợp sở thích đã thể hiện trước đó.",
    }
    favorite_category = str((segment or {}).get("favorite_category") or "General")
    return f"{mapping.get(segment_name, 'Cá nhân hóa gợi ý theo hành vi khách hàng.')} Sở thích danh mục gần nhất: {favorite_category}."


def _extract_query_intents(query: str) -> Dict[str, bool]:
    text = _normalize_lower(query)
    return {
        "beach": any(term in text for term in _BEACH_TERMS),
        "mountain": any(term in text for term in _MOUNTAIN_TERMS),
        "family": any(term in text for term in _FAMILY_TERMS),
        "budget": any(term in text for term in _BUDGET_TERMS),
        "premium": any(term in text for term in _PREMIUM_TERMS),
    }


def _rerank_results(query: str, items: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    intents = _extract_query_intents(query)
    reranked: List[Dict[str, Any]] = []

    for item in items:
        text = _normalize_lower(item.get("text"))
        score = float(item.get("score") or 0.0)
        price = _safe_float(item.get("price"))

        if intents.get("beach"):
            score += 0.45 if any(term in text for term in _BEACH_TERMS) else -0.20
        if intents.get("mountain"):
            score += 0.45 if any(term in text for term in _MOUNTAIN_TERMS) else -0.20
        if intents.get("family"):
            score += 0.25 if any(term in text for term in _FAMILY_TERMS) else 0.0
        if intents.get("budget") and price > 0:
            score += max(0.0, 0.40 - min(price / 15000000.0, 0.40))
        if intents.get("premium") and price > 0:
            score += min(price / 20000000.0, 0.35)

        enriched = dict(item)
        enriched["score"] = round(score, 4)
        reranked.append(enriched)

    reranked.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
    return reranked[:top_k]


def _call_openai_embeddings(texts: List[str]) -> np.ndarray:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    response = requests.post(
        f"{DEFAULT_OPENAI_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEFAULT_EMBEDDING_MODEL,
            "input": texts,
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    vectors = np.array([item["embedding"] for item in payload.get("data", [])], dtype="float32")
    if vectors.size == 0:
        raise RuntimeError("Embedding API returned no vectors")
    return vectors


def _fit_local_embeddings(texts: List[str]) -> Tuple[TfidfVectorizer, np.ndarray]:
    vectorizer = TfidfVectorizer(max_features=4096, ngram_range=(1, 2), min_df=1)
    vectors = vectorizer.fit_transform(texts).toarray().astype("float32")
    return vectorizer, vectors


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    if vectors.size == 0:
        return vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def _fetch_tour_rows() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.TourID AS tour_id,
                    t.Title AS title,
                    t.Location AS location,
                    t.Description AS description,
                    t.Price AS price,
                    t.StartDate AS start_date,
                    t.EndDate AS end_date,
                    t.Capacity AS capacity,
                    t.Status AS status,
                    c.CategoryName AS category_name,
                    COALESCE(AVG(cm.Rating), 0) AS avg_rating,
                    COALESCE(COUNT(DISTINCT CASE WHEN b.Status IN ('Confirmed', 'Paid') THEN b.BookingID END), 0) AS booking_count,
                    COALESCE(GROUP_CONCAT(DISTINCT LEFT(cm.Content, 160) SEPARATOR ' | '), '') AS review_snippets
                FROM tour t
                LEFT JOIN category c ON t.CategoryID = c.CategoryID
                LEFT JOIN booking b ON b.TourID = t.TourID
                LEFT JOIN comment cm ON cm.TourID = t.TourID
                WHERE (t.Status IS NULL OR t.Status <> 'Deleted')
                GROUP BY
                    t.TourID, t.Title, t.Location, t.Description, t.Price,
                    t.StartDate, t.EndDate, t.Capacity, t.Status, c.CategoryName
                ORDER BY t.TourID DESC
                """
            )
            return list(cur.fetchall() or [])
    finally:
        conn.close()


def _build_chunks(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []

    for row in rows:
        tour_id = _safe_int(row.get("tour_id"))
        title = _normalize_whitespace(row.get("title") or f"Tour {tour_id}")
        location = _normalize_whitespace(row.get("location"))
        category_name = _normalize_whitespace(row.get("category_name") or "General")
        description = _normalize_whitespace(row.get("description"))
        review_snippets = _normalize_whitespace(row.get("review_snippets"))
        price = _safe_float(row.get("price"))
        avg_rating = _safe_float(row.get("avg_rating"))
        booking_count = _safe_int(row.get("booking_count"))
        capacity = _safe_int(row.get("capacity"))
        status = _normalize_whitespace(row.get("status") or "Available")
        start_date = row.get("start_date").isoformat() if row.get("start_date") else "N/A"
        end_date = row.get("end_date").isoformat() if row.get("end_date") else "N/A"

        overview = (
            f"Tour {title}. Điểm đến: {location}. Danh mục: {category_name}. "
            f"Giá: {price:,.0f} VND. Sức chứa: {capacity}. Trạng thái: {status}. "
            f"Khởi hành: {start_date}. Kết thúc: {end_date}. "
            f"Đánh giá trung bình: {avg_rating:.1f}. Số booking đã xác nhận: {booking_count}."
        )
        chunks.append(
            {
                "tour_id": tour_id,
                "title": title,
                "location": location,
                "category_name": category_name,
                "price": price,
                "chunk_type": "overview",
                "text": overview,
            }
        )

        for index, piece in enumerate(_split_text(description), start=1):
            chunks.append(
                {
                    "tour_id": tour_id,
                    "title": title,
                    "location": location,
                    "category_name": category_name,
                    "price": price,
                    "chunk_type": f"description_{index}",
                    "text": f"Mô tả tour {title}: {piece}",
                }
            )

        if review_snippets:
            for index, piece in enumerate(_split_text(review_snippets, chunk_size=80, overlap=12), start=1):
                chunks.append(
                    {
                        "tour_id": tour_id,
                        "title": title,
                        "location": location,
                        "category_name": category_name,
                        "price": price,
                        "chunk_type": f"reviews_{index}",
                        "text": f"Nhận xét khách hàng về tour {title}: {piece}",
                    }
                )

    return chunks


def build_vector_store(force: bool = False) -> Dict[str, Any]:
    _ensure_store_dir()

    if not force and INDEX_FILE.exists() and METADATA_FILE.exists() and STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {
            "message": "RAG index already exists",
            "documents": state.get("document_count", 0),
            "embedding_provider": state.get("embedding_provider", "unknown"),
            "path": str(RAG_DIR),
        }

    rows = _fetch_tour_rows()
    chunks = _build_chunks(rows)
    texts = [chunk["text"] for chunk in chunks]
    if not texts:
        raise RuntimeError("No tour data found to build the RAG index")

    vectorizer = None
    embedding_provider = "local-tfidf"
    if os.getenv("OPENAI_API_KEY"):
        vectors = _call_openai_embeddings(texts)
        embedding_provider = "openai"
    else:
        vectorizer, vectors = _fit_local_embeddings(texts)

    vectors = _normalize_vectors(vectors.astype("float32"))

    index = None
    if faiss is not None:
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        faiss.write_index(index, str(INDEX_FILE))

    np.save(VECTORS_FILE, vectors)
    METADATA_FILE.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    state = {
        "built_at": int(time.time()),
        "document_count": len(chunks),
        "tour_count": len(rows),
        "embedding_provider": embedding_provider,
        "embedding_model": DEFAULT_EMBEDDING_MODEL if embedding_provider == "openai" else "tfidf",
        "retriever": "faiss" if faiss is not None else "numpy-cosine",
    }
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    if vectorizer is not None:
        with VECTORIZER_FILE.open("wb") as file_obj:
            pickle.dump(vectorizer, file_obj)
    elif VECTORIZER_FILE.exists():
        VECTORIZER_FILE.unlink()

    _RAG_CACHE.update(
        {
            "loaded": True,
            "loaded_at": time.time(),
            "chunks": chunks,
            "state": state,
            "vectorizer": vectorizer,
            "vectors": vectors,
            "index": index,
        }
    )

    return {
        "message": "RAG index built successfully",
        "documents": len(chunks),
        "tour_count": len(rows),
        "embedding_provider": embedding_provider,
        "path": str(RAG_DIR),
    }


def load_vector_store(force_reload: bool = False) -> Dict[str, Any]:
    if _RAG_CACHE.get("loaded") and not force_reload:
        return _RAG_CACHE

    if not INDEX_FILE.exists() or not METADATA_FILE.exists() or not STATE_FILE.exists() or not VECTORS_FILE.exists():
        build_vector_store(force=True)
        return _RAG_CACHE

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    chunks = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    vectors = np.load(VECTORS_FILE)

    vectorizer = None
    if VECTORIZER_FILE.exists():
        with VECTORIZER_FILE.open("rb") as file_obj:
            vectorizer = pickle.load(file_obj)

    index = None
    if faiss is not None and INDEX_FILE.exists():
        index = faiss.read_index(str(INDEX_FILE))

    _RAG_CACHE.update(
        {
            "loaded": True,
            "loaded_at": time.time(),
            "chunks": chunks,
            "state": state,
            "vectorizer": vectorizer,
            "vectors": vectors,
            "index": index,
        }
    )
    return _RAG_CACHE


def _embed_query(query: str, cache: Dict[str, Any]) -> np.ndarray:
    provider = str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf")
    if provider == "openai":
        vectors = _call_openai_embeddings([query])
    else:
        vectorizer = cache.get("vectorizer")
        if vectorizer is None:
            raise RuntimeError("Local vectorizer is not loaded")
        vectors = vectorizer.transform([query]).toarray().astype("float32")
    return _normalize_vectors(vectors.astype("float32"))


def retrieve_documents(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    cache = load_vector_store()
    chunks = cache.get("chunks") or []
    if not chunks:
        return []

    query_vector = _embed_query(query, cache)
    search_k = min(max(top_k * 4, 8), len(chunks))

    indices: List[int]
    scores: List[float]
    if faiss is not None and cache.get("index") is not None:
        score_matrix, idx_matrix = cache["index"].search(query_vector, search_k)
        indices = [int(i) for i in idx_matrix[0] if int(i) >= 0]
        scores = [float(score_matrix[0][offset]) for offset in range(len(indices))]
    else:
        vectors = cache.get("vectors")
        similarity = (vectors @ query_vector.T).reshape(-1)
        ranked = np.argsort(similarity)[::-1][:search_k]
        indices = [int(i) for i in ranked]
        scores = [float(similarity[i]) for i in ranked]

    seen_tours = set()
    results: List[Dict[str, Any]] = []
    for idx, score in zip(indices, scores):
        item = dict(chunks[idx])
        tour_id = item.get("tour_id")
        dedupe_key = (tour_id, item.get("chunk_type"))
        if dedupe_key in seen_tours:
            continue
        seen_tours.add(dedupe_key)
        item["score"] = round(score, 4)
        results.append(item)
        if len(results) >= search_k:
            break
    return _rerank_results(query, results, top_k=top_k)


def _build_context(sources: List[Dict[str, Any]], max_context_chars: int) -> str:
    parts: List[str] = []
    current_length = 0
    for index, source in enumerate(sources, start=1):
        block = (
            f"[{index}] TourID={source.get('tour_id')} | Title={source.get('title')} | "
            f"Location={source.get('location')} | Category={source.get('category_name')} | "
            f"Price={source.get('price')} | ChunkType={source.get('chunk_type')}\n"
            f"{source.get('text')}"
        )
        if current_length + len(block) > max_context_chars:
            break
        parts.append(block)
        current_length += len(block)
    return "\n\n".join(parts)


def _fallback_answer(query: str, segment: Optional[Dict[str, Any]], sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "Hiện tôi chưa tìm thấy tour phù hợp trong dữ liệu. Bạn hãy hỏi rõ hơn về ngân sách, địa điểm hoặc thời gian đi."

    segment_name = str((segment or {}).get("segment_name") or "Khách mới")
    intro = f"Gợi ý phù hợp cho bạn ({segment_name}):"
    lines = [intro]
    for source in sources[:3]:
        price = _safe_float(source.get("price"))
        lines.append(
            f"- {source.get('title')} ở {source.get('location')}, giá khoảng {price:,.0f} VND, danh mục {source.get('category_name')}."
        )
    lines.append(f"Câu hỏi: {query}")
    return "\n".join(lines)


def _generate_answer(query: str, segment: Optional[Dict[str, Any]], sources: List[Dict[str, Any]], max_context_chars: int) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_answer(query, segment, sources)

    context = _build_context(sources, max_context_chars=max_context_chars)
    personalization = _segment_instruction(segment)
    payload = {
        "model": DEFAULT_CHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Bạn là chatbot tư vấn tour du lịch dùng RAG trên dữ liệu nội bộ. "
                    "Chỉ dùng thông tin trong context. Nếu dữ liệu không đủ, nói rõ là chưa có trong hệ thống. "
                    "Trả lời ngắn gọn, thực tế, ưu tiên tour phù hợp nhất và nêu giá khi có. "
                    f"{personalization}"
                ),
            },
            {
                "role": "user",
                "content": f"Câu hỏi: {query}\n\nCustomer segment: {json.dumps(segment or {}, ensure_ascii=False)}\n\nContext:\n{context}",
            },
        ],
        "temperature": 0.3,
        "max_tokens": 350,
    }

    try:
        response = requests.post(
            f"{DEFAULT_OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=40,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return _fallback_answer(query, segment, sources)


def answer_chat(query: str, user_id: Optional[int] = None, top_k: int = 4, max_context_chars: int = 3500) -> Dict[str, Any]:
    cache = load_vector_store()
    segment = get_user_segment(user_id) if user_id else None

    sources = retrieve_documents(query, top_k=top_k)
    answer = _generate_answer(query, segment, sources, max_context_chars=max_context_chars)

    return {
        "answer": answer,
        "query": query,
        "top_k": top_k,
        "retriever": str((cache.get("state") or {}).get("retriever") or "faiss"),
        "embedding_provider": str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf"),
        "segment": segment,
        "sources": sources,
    }
