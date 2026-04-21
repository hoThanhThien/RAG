from __future__ import annotations

import json
import logging
import os
import pickle
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

from app.database import get_db_connection
from app.services.customer_segmentation_service import get_user_segment
from app.services.rag.bm25 import BM25Index
from app.services.rag.cache import InMemoryTTLCache, RedisCache, decode_vector, encode_vector
from app.services.rag.chunking import build_semantic_chunks
from app.services.rag.config import get_rag_settings
from app.services.rag.intents import (
    BEACH_TERMS,
    DOMESTIC_TERMS,
    DOMESTIC_EXPLICIT_TERMS,
    FAMILY_TERMS,
    INTERNATIONAL_TERMS,
    MOUNTAIN_TERMS,
    RELAX_TERMS,
    SIMILAR_TERMS,
    extract_query_intents,
    normalize_text,
    source_match_text,
)
from app.services.rag.metrics import rag_metrics
from app.services.rag.prompting import build_context, build_system_prompt, build_user_prompt

try:
    import faiss  # type: ignore
except Exception:
    faiss = None


settings = get_rag_settings()

BASE_DIR = settings.base_dir
RAG_DIR = settings.rag_dir
INDEX_FILE = settings.index_file
METADATA_FILE = settings.metadata_file
STATE_FILE = settings.state_file
VECTORIZER_FILE = settings.vectorizer_file
VECTORS_FILE = settings.vectors_file
DEFAULT_CHAT_MODEL = settings.default_chat_model
DEFAULT_EMBEDDING_MODEL = settings.default_embedding_model
DEFAULT_OPENAI_BASE_URL = settings.openai_base_url

logger = logging.getLogger(__name__)
_HTTP_SESSION = requests.Session()

_RAG_CACHE: Dict[str, Any] = {
    "loaded": False,
    "loaded_at": 0.0,
    "chunks": [],
    "state": {},
    "vectorizer": None,
    "vectors": None,
    "index": None,
    "bm25": None,
    "normalized_docs": [],
}
_LOCAL_QUERY_EMBED_CACHE = InMemoryTTLCache(max_size=settings.query_cache_size)
_LOCAL_RESPONSE_CACHE = InMemoryTTLCache(max_size=settings.query_cache_size)
_REDIS_CACHE: RedisCache | None = None
_REDIS_DISABLED = False
_RESPONSE_CACHE_EPOCH = 0


def _get_redis_cache() -> RedisCache | None:
    global _REDIS_CACHE, _REDIS_DISABLED
    if not settings.redis_enabled:
        return None
    if _REDIS_DISABLED:
        return None
    if _REDIS_CACHE is not None:
        return _REDIS_CACHE

    try:
        cache = RedisCache(
            url=settings.redis_url,
            key_prefix=settings.redis_key_prefix,
            timeout_seconds=settings.redis_timeout_seconds,
        )
        if cache.ping():
            _REDIS_CACHE = cache
            logger.info("RAG Redis cache enabled at %s", settings.redis_url)
            return _REDIS_CACHE
        _REDIS_DISABLED = True
        rag_metrics.increment("redis_fallback_total")
        logger.warning("RAG Redis cache unavailable at %s, falling back to in-memory cache", settings.redis_url)
    except Exception:
        _REDIS_DISABLED = True
        rag_metrics.increment("redis_fallback_total")
        logger.warning("Failed to initialize Redis cache, falling back to in-memory cache", exc_info=False)
    return None


def _set_response_cache_epoch(value: int) -> None:
    global _RESPONSE_CACHE_EPOCH
    _RESPONSE_CACHE_EPOCH = value


def _get_response_cache_epoch() -> int:
    redis_cache = _get_redis_cache()
    if redis_cache is not None:
        payload = redis_cache.get_json("response_cache_epoch")
        if payload and isinstance(payload.get("value"), int):
            _set_response_cache_epoch(int(payload["value"]))
            return _RESPONSE_CACHE_EPOCH
    return _RESPONSE_CACHE_EPOCH


def invalidate_rag_response_cache(reason: str = "manual") -> Dict[str, Any]:
    next_epoch = _get_response_cache_epoch() + 1
    _set_response_cache_epoch(next_epoch)
    _LOCAL_RESPONSE_CACHE.clear()
    redis_cache = _get_redis_cache()
    if redis_cache is not None:
        redis_cache.set_json("response_cache_epoch", {"value": next_epoch, "reason": reason}, settings.response_cache_ttl_seconds * 10)
    rag_metrics.mark_invalidation(reason)
    logger.info("RAG response cache invalidated reason=%s epoch=%s", reason, next_epoch)
    return {"message": "RAG response cache invalidated", "reason": reason, "epoch": next_epoch}


def get_rag_metrics() -> Dict[str, Any]:
    snapshot = rag_metrics.snapshot()
    snapshot["response_cache_epoch"] = _get_response_cache_epoch()
    snapshot["redis_enabled"] = bool(settings.redis_enabled)
    snapshot["redis_active"] = _get_redis_cache() is not None
    snapshot["embedding_provider"] = str((_RAG_CACHE.get("state") or {}).get("embedding_provider") or "unknown")
    snapshot["retriever"] = str((_RAG_CACHE.get("state") or {}).get("retriever") or "unknown")
    return snapshot


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


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    if vectors.size == 0:
        return vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def _fit_local_embeddings(texts: List[str]) -> Tuple[TfidfVectorizer, np.ndarray]:
    vectorizer = TfidfVectorizer(max_features=4096, ngram_range=(1, 2), min_df=1)
    vectors = vectorizer.fit_transform(texts).toarray().astype("float32")
    return vectorizer, vectors


def _batched(items: List[str], batch_size: int) -> List[List[str]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def _call_openai_embeddings(texts: List[str]) -> np.ndarray:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    vectors: List[np.ndarray] = []
    for batch in _batched(texts, settings.embedding_batch_size):
        response = _HTTP_SESSION.post(
            f"{DEFAULT_OPENAI_BASE_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEFAULT_EMBEDDING_MODEL,
                "input": batch,
            },
            timeout=settings.openai_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", [])
        if data:
            vectors.append(np.array([item["embedding"] for item in data], dtype="float32"))

    if not vectors:
        raise RuntimeError("Embedding API returned no vectors")
    return np.vstack(vectors)


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


def _generate_enrichment_text(title: str, location: str, category_name: str, price: float, avg_rating: float, booking_count: int) -> str:
    """Generate a rich synthetic keyword chunk from tour metadata to improve RAG retrieval."""
    loc = normalize_text(location or "")
    cat = normalize_text(category_name or "")
    parts: List[str] = [f"Tour {title} tai {location}, danh muc {category_name}."]

    # ---- Geography & destination type ----
    domestic_keywords = ["ha long", "sa pa", "fansipan", "ninh binh", "trang an", "tam coc", "viet nam",
                         "ha noi", "sai gon", "hcm", "da nang", "hoi an", "phu quoc", "nha trang",
                         "da lat", "mui ne", "quy nhon", "gia lai", "kon tum", "vinh long"]
    sea_keywords = ["ha long", "pattaya", "phu quoc", "nha trang", "da nang", "mui ne", "quy nhon",
                    "hong kong", "singapore", "sydney", "dubai", "abu dhabi"]
    mountain_keywords = ["sa pa", "fansipan", "da lat", "sapa", "nui", "everland", "blue mountains"]
    intl_asean_keywords = ["bangkok", "pattaya", "thai lan", "singapore", "kuala lumpur", "malaysia",
                           "bali", "indonesia", "philippines", "myanmar", "campuchia", "cambodia"]
    intl_east_asia = ["tokyo", "nhat ban", "japan", "seoul", "han quoc", "korea", "hong kong",
                      "ma cao", "macau", "dai bac", "cao hung", "taiwan", "dai loan"]
    intl_europe = ["paris", "versailles", "phap", "france", "anh", "y", "duc", "tay ban nha", "bac au",
                   "ha lan", "thuy si", "bi", "ao", "chau au", "europa"]
    intl_oceania = ["sydney", "uc", "australia", "new zealand", "blue mountains"]
    intl_middle_east = ["dubai", "abu dhabi", "uae", "saudi", "trung dong"]

    geo_tags: List[str] = []
    if any(kw in loc for kw in domestic_keywords) or "du lich trong nuoc" in cat:
        geo_tags += ["du lich trong nuoc", "viet nam", "noi dia"]
    else:
        geo_tags += ["du lich nuoc ngoai", "quoc te", "international"]
    if any(kw in loc for kw in intl_asean_keywords):
        geo_tags += ["dong nam a", "asean", "chau a"]
    if any(kw in loc for kw in intl_east_asia):
        geo_tags += ["dong a", "chau a"]
    if any(kw in loc for kw in intl_europe):
        geo_tags += ["chau au", "europe", "nuoc ngoai"]
    if any(kw in loc for kw in intl_oceania):
        geo_tags += ["chau dai duong", "uc", "australia"]
    if any(kw in loc for kw in intl_middle_east):
        geo_tags += ["trung dong", "chau phi", "nuoc ngoai"]
    if any(kw in loc for kw in sea_keywords):
        geo_tags += ["tour bien", "bien ca", "bai bien", "resort bien", "tam bien"]
    if any(kw in loc for kw in mountain_keywords):
        geo_tags += ["tour nui", "leo nui", "khi hau mat", "kham pha thien nhien"]
    if geo_tags:
        parts.append("Khu vuc / loai hinh: " + ", ".join(dict.fromkeys(geo_tags)) + ".")

    # ---- Price tier ----
    if price and price > 0:
        if price < 3_000_000:
            tier = "gia re, phu hop nguoi ít tien, budget, gia thap nhat, tiet kiem"
        elif price < 8_000_000:
            tier = "gia trung binh, phu hop gia dinh, nhom ban, pho thong"
        elif price < 15_000_000:
            tier = "gia cao, cao cap, premium, sang trong"
        else:
            tier = "luxury, rat cao cap, hang sang, premium cao nhat"
        parts.append(f"Muc gia khoang {price:,.0f} VND — {tier}.")

    # ---- Popularity ----
    if avg_rating >= 4.5:
        parts.append("Tour duoc danh gia rat cao, khach rat hai long, hot, pho bien.")
    elif avg_rating >= 3.5:
        parts.append("Tour duoc danh gia tot, nhieu khach chon.")
    if booking_count >= 20:
        parts.append(f"Da co {booking_count} luot dat tour — rat hot, pho bien.")
    elif booking_count >= 5:
        parts.append(f"Da co {booking_count} luot dat tour.")

    # ---- Specific destination hints ----
    location_hints: Dict[str, str] = {
        "ha long": "Vinh Ha Long — ky quan thien nhien the gioi, thuyen tham quan, hang dong, bien xanh.",
        "sa pa": "Sa Pa — suong mu, ruong bac thang, ban lang dan toc, leo nui Fansipan cao nhat Dong Duong.",
        "ninh binh": "Ninh Binh — Trang An, Tam Coc, Bich Dong, thien nhien song nuoc, di san UNESCO.",
        "bangkok": "Bangkok — thu do Thai Lan, chua chien, cho noi, am thuc duong pho, mua sam.",
        "pattaya": "Pattaya — bai bien Pattaya, tu vien, song show, tro choi duoi nuoc, Thai Lan.",
        "singapore": "Singapore — thanh pho hien dai, Gardens by the Bay, Marina Bay, am thuc chau a.",
        "kuala lumpur": "Kuala Lumpur — Thap Doi Petronas, trung tam mua sam, van hoa Malaysia.",
        "tokyo": "Tokyo — nui Phu Si, nghe thuat, am thuc Nhat Ban, anime, cong nghe.",
        "seoul": "Seoul — dao Nami, Everland, Gangnam, K-pop, Han Quoc hien dai.",
        "hong kong": "Hong Kong — sieu do thi, nui Lion Rock, cho dem, am thuc.",
        "ma cao": "Ma Cao — song bac, kien truc Bo Dao Nha, casino, dia diem giai tri.",
        "dai bac": "Dai Bac — thu do Dai Loan, cho dem Shilin, cong vien quoc gia.",
        "cao hung": "Cao Hung — cang bien lon Dai Loan, van hoa bien, cho dem.",
        "paris": "Paris — Thap Eiffel, Louvre, cung dien Versailles, tinh yeu, romance, chau Au.",
        "sydney": "Sydney — Opera House, Blue Mountains, bai bien Bondi, chau Dai Duong.",
        "dubai": "Dubai — Burj Khalifa, sa mac, sang trong, mua sam, xa hoa.",
        "abu dhabi": "Abu Dhabi — cung dien, mo qua truoc, sang trong, UAE.",
    }
    for kw, hint in location_hints.items():
        if kw in loc:
            parts.append(hint)
            break

    return " ".join(parts)


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
            f"Tour {title}. Diem den: {location}. Danh muc: {category_name}. "
            f"Gia: {price:,.0f} VND. Suc chua: {capacity}. Trang thai: {status}. "
            f"Khoi hanh: {start_date}. Ket thuc: {end_date}. "
            f"Danh gia trung binh: {avg_rating:.1f}. So booking da xac nhan: {booking_count}."
        )
        chunks.append(
            {
                "tour_id": tour_id,
                "title": title,
                "location": location,
                "category_name": category_name,
                "price": price,
                "start_date": start_date,
                "end_date": end_date,
                "capacity": capacity,
                "status": status,
                "booking_count": booking_count,
                "chunk_type": "overview",
                "text": overview,
            }
        )

        # --- Synthetic enrichment chunk: adds geography, price-tier, and destination keywords ---
        enrichment_text = _generate_enrichment_text(
            title, location, category_name, price, avg_rating, booking_count
        )
        chunks.append(
            {
                "tour_id": tour_id,
                "title": title,
                "location": location,
                "category_name": category_name,
                "price": price,
                "start_date": start_date,
                "end_date": end_date,
                "capacity": capacity,
                "status": status,
                "booking_count": booking_count,
                "chunk_type": "enrichment",
                "text": enrichment_text,
            }
        )

        for index, piece in enumerate(
            build_semantic_chunks(
                description,
                max_words=settings.chunk_size_words,
                overlap_sentences=settings.chunk_overlap_sentences,
            ),
            start=1,
        ):
            chunks.append(
                {
                    "tour_id": tour_id,
                    "title": title,
                    "location": location,
                    "category_name": category_name,
                    "price": price,
                    "chunk_type": f"description_{index}",
                    "text": f"Mo ta tour {title}: {piece}",
                }
            )

        if review_snippets:
            for index, piece in enumerate(
                build_semantic_chunks(
                    review_snippets,
                    max_words=settings.review_chunk_size_words,
                    overlap_sentences=0,
                ),
                start=1,
            ):
                chunks.append(
                    {
                        "tour_id": tour_id,
                        "title": title,
                        "location": location,
                        "category_name": category_name,
                        "price": price,
                        "chunk_type": f"reviews_{index}",
                        "text": f"Nhan xet khach hang ve tour {title}: {piece}",
                    }
                )

    return chunks


def _build_auxiliary_indexes(chunks: List[Dict[str, Any]]) -> Tuple[List[str], BM25Index]:
    normalized_docs = [source_match_text(chunk) for chunk in chunks]
    return normalized_docs, BM25Index(normalized_docs)


def _update_cache(chunks: List[Dict[str, Any]], state: Dict[str, Any], vectorizer: Any, vectors: np.ndarray, index: Any) -> None:
    normalized_docs, bm25 = _build_auxiliary_indexes(chunks)
    _RAG_CACHE.update(
        {
            "loaded": True,
            "loaded_at": time.time(),
            "chunks": chunks,
            "state": state,
            "vectorizer": vectorizer,
            "vectors": vectors,
            "index": index,
            "bm25": bm25,
            "normalized_docs": normalized_docs,
        }
    )


def build_vector_store(force: bool = False) -> Dict[str, Any]:
    _ensure_store_dir()

    if not force and INDEX_FILE.exists() and METADATA_FILE.exists() and STATE_FILE.exists() and VECTORS_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {
            "message": "RAG index already exists",
            "documents": state.get("document_count", 0),
            "embedding_provider": state.get("embedding_provider", "unknown"),
            "path": str(RAG_DIR),
        }

    started_at = time.perf_counter()
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
    if faiss is not None and vectors.size:
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
        "retriever": "hybrid-faiss-bm25" if faiss is not None else "hybrid-numpy-bm25",
        "chunking": {
            "description_chunk_size_words": settings.chunk_size_words,
            "review_chunk_size_words": settings.review_chunk_size_words,
            "overlap_sentences": settings.chunk_overlap_sentences,
        },
        "weights": {
            "dense": settings.hybrid_dense_weight,
            "lexical": settings.hybrid_lexical_weight,
        },
    }
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    if vectorizer is not None:
        with VECTORIZER_FILE.open("wb") as file_obj:
            pickle.dump(vectorizer, file_obj)
    elif VECTORIZER_FILE.exists():
        VECTORIZER_FILE.unlink()

    _update_cache(chunks, state, vectorizer, vectors, index)
    _LOCAL_QUERY_EMBED_CACHE.clear()
    _LOCAL_RESPONSE_CACHE.clear()
    invalidate_rag_response_cache(reason="rebuild")
    rag_metrics.mark_rebuild()
    logger.info("RAG index built in %.2fs with %s chunks across %s tours", time.perf_counter() - started_at, len(chunks), len(rows))

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

    _update_cache(chunks, state, vectorizer, vectors, index)
    return _RAG_CACHE


def _segment_cache_signature(segment: Optional[Dict[str, Any]]) -> str:
    if not segment:
        return "anonymous"
    return ":".join(
        [
            str(segment.get("segment_name") or "unknown"),
            str(segment.get("favorite_category") or "general"),
        ]
    )


def _response_cache_key(
    query: str,
    user_id: Optional[int],
    top_k: int,
    cache_state: Dict[str, Any],
    segment: Optional[Dict[str, Any]],
    focus_tour_id: Optional[int] = None,
) -> str:
    state = cache_state.get("state") or {}
    built_at = state.get("built_at") or "0"
    embedding_provider = state.get("embedding_provider") or "local-tfidf"
    epoch = _get_response_cache_epoch()
    return (
        f"response:{embedding_provider}:{built_at}:{epoch}:{top_k}:{user_id or 0}:"
        f"{focus_tour_id or 0}:{_segment_cache_signature(segment)}:{normalize_text(query)}"
    )


def _embed_query(query: str, cache: Dict[str, Any]) -> np.ndarray:
    provider = str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf")
    cache_key = f"{provider}:{normalize_text(query)}"
    redis_cache = _get_redis_cache()
    if redis_cache is not None:
        payload = redis_cache.get_bytes(f"embed:{cache_key}")
        if payload:
            vector = decode_vector(payload)
            if vector is not None:
                rag_metrics.increment("embedding_cache_hits_redis")
                return vector

    cached = _LOCAL_QUERY_EMBED_CACHE.get(cache_key)
    if cached is not None:
        rag_metrics.increment("embedding_cache_hits_memory")
        return cached

    if provider == "openai":
        vectors = _call_openai_embeddings([query])
    else:
        vectorizer = cache.get("vectorizer")
        if vectorizer is None:
            raise RuntimeError("Local vectorizer is not loaded")
        vectors = vectorizer.transform([query]).toarray().astype("float32")

    normalized = _normalize_vectors(vectors.astype("float32"))
    _LOCAL_QUERY_EMBED_CACHE.set(cache_key, normalized, settings.query_cache_ttl_seconds)
    if redis_cache is not None:
        redis_cache.set_bytes(f"embed:{cache_key}", encode_vector(normalized), settings.query_cache_ttl_seconds)
    return normalized


def _expand_query_for_retrieval(query: str) -> str:
    normalized_query = normalize_text(query)
    intents = extract_query_intents(query)
    expansions: List[str] = [query]

    if intents.get("hot_weather"):
        expansions.append("tour mat me tranh nong nghi duong bien nui trong nuoc ha long sa pa da lat")
    if intents.get("beach"):
        expansions.append("tour bien dao nghi duong ha long nha trang phu quoc da nang")
    if intents.get("mountain"):
        expansions.append("tour nui khi hau mat me sa pa da lat moc chau tam dao")
    if intents.get("international"):
        expansions.append("tour du lich ngoai nuoc quoc te thai lan han quoc nhat ban chau au")
    if intents.get("family"):
        expansions.append("tour gia dinh de di tre em lich trinh nhe")
    if intents.get("budget"):
        expansions.append("tour gia re tiet kiem khuyen mai gia tot")
    if intents.get("relax"):
        expansions.append("tour nghi duong thu gian resort yen tinh")
    if len(normalized_query.split()) <= 3 and not any(intents.values()):
        expansions.append("tour du lich pho bien de di")

    return " ".join(dict.fromkeys(expansions))


def _adaptive_search_k(query: str, top_k: int, chunk_count: int) -> Tuple[int, int]:
    intents = extract_query_intents(query)
    dense_k = max(settings.min_search_k, top_k * settings.search_multiplier)
    lexical_k = max(settings.min_search_k, top_k * settings.lexical_search_multiplier)
    if intents.get("hot_weather") or intents.get("beach") or intents.get("international"):
        dense_k += top_k * 2
        lexical_k += top_k * 2
    if len(normalize_text(query).split()) <= 4:
        lexical_k += top_k * 2
    return min(dense_k, chunk_count, settings.max_search_k), min(lexical_k, chunk_count, settings.max_search_k)


def _normalize_score_map(items: List[Tuple[int, float]]) -> Dict[int, float]:
    if not items:
        return {}
    scores = [score for _, score in items]
    min_score = min(scores)
    max_score = max(scores)
    if abs(max_score - min_score) < 1e-9:
        return {index: 1.0 for index, _ in items}
    return {index: (score - min_score) / (max_score - min_score) for index, score in items}


def _dense_candidates(query_vector: np.ndarray, cache: Dict[str, Any], search_k: int) -> List[Tuple[int, float]]:
    if search_k <= 0:
        return []
    if faiss is not None and cache.get("index") is not None:
        score_matrix, idx_matrix = cache["index"].search(query_vector, search_k)
        return [(int(index), float(score_matrix[0][offset])) for offset, index in enumerate(idx_matrix[0]) if int(index) >= 0]

    vectors = cache.get("vectors")
    if vectors is None or not len(vectors):
        return []
    similarity = (vectors @ query_vector.T).reshape(-1)
    ranked = np.argsort(similarity)[::-1][:search_k]
    return [(int(index), float(similarity[index])) for index in ranked]


def _lexical_candidates(expanded_query: str, cache: Dict[str, Any], search_k: int) -> List[Tuple[int, float]]:
    bm25 = cache.get("bm25")
    if bm25 is None or search_k <= 0:
        return []
    return bm25.search(normalize_text(expanded_query), search_k)


def _collect_hybrid_candidates(query: str, cache: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
    chunks = cache.get("chunks") or []
    if not chunks:
        return []

    expanded_query = _expand_query_for_retrieval(query)
    dense_k, lexical_k = _adaptive_search_k(query, top_k, len(chunks))
    query_vector = _embed_query(expanded_query, cache)

    dense = _dense_candidates(query_vector, cache, dense_k)
    lexical = _lexical_candidates(expanded_query, cache, lexical_k)
    dense_scores = _normalize_score_map(dense)
    lexical_scores = _normalize_score_map(lexical)

    candidate_indices = set(dense_scores) | set(lexical_scores)
    combined: List[Dict[str, Any]] = []
    for index in candidate_indices:
        item = dict(chunks[index])
        dense_score = dense_scores.get(index, 0.0)
        lexical_score = lexical_scores.get(index, 0.0)
        item["dense_score"] = round(dense_score, 4)
        item["lexical_score"] = round(lexical_score, 4)
        item["score"] = round(dense_score * settings.hybrid_dense_weight + lexical_score * settings.hybrid_lexical_weight, 4)
        combined.append(item)

    combined.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
    return combined[: max(dense_k, lexical_k, top_k * 4)]


def _intent_score_adjustment(query: str, item: Dict[str, Any]) -> float:
    intents = extract_query_intents(query)
    text = source_match_text(item)
    price = _safe_float(item.get("price"))
    score = float(item.get("score") or 0.0)

    is_international = any(term in text for term in INTERNATIONAL_TERMS)
    is_domestic = any(term in text for term in DOMESTIC_TERMS)
    is_beach = any(term in text for term in BEACH_TERMS)
    is_mountain = any(term in text for term in MOUNTAIN_TERMS)
    is_relax = any(term in text for term in RELAX_TERMS)
    is_family = any(term in text for term in FAMILY_TERMS)

    if intents.get("beach"):
        score += 0.55 if is_beach else -0.20
    if intents.get("mountain"):
        score += 0.55 if is_mountain else -0.20
    if intents.get("family"):
        score += 0.25 if is_family else 0.0
    if intents.get("relax"):
        score += 0.25 if is_relax else 0.0
    if intents.get("international"):
        score += 0.70 if is_international else -0.35
    elif is_international:
        score -= 0.08
    if intents.get("hot_weather"):
        score += 0.35 if (is_beach or is_mountain or is_relax) else -0.10
        if is_international and not intents.get("international"):
            score -= 0.45
        if is_domestic:
            score += 0.20
    if intents.get("budget") and price > 0:
        score += max(0.0, 0.40 - min(price / 15000000.0, 0.40))
    if intents.get("premium") and price > 0:
        score += min(price / 20000000.0, 0.35)
    if intents.get("international") and is_domestic:
        score -= 0.20
    return round(score, 4)


def _pick_best_chunk_per_tour(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best_by_tour: Dict[int, Dict[str, Any]] = {}
    for item in items:
        tour_id = _safe_int(item.get("tour_id"))
        current = best_by_tour.get(tour_id)
        if current is None:
            best_by_tour[tour_id] = item
            continue
        current_score = float(current.get("score") or 0.0)
        candidate_score = float(item.get("score") or 0.0)
        if candidate_score > current_score:
            best_by_tour[tour_id] = item
        elif candidate_score == current_score and item.get("chunk_type") == "overview":
            best_by_tour[tour_id] = item
    ranked = list(best_by_tour.values())
    ranked.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
    return ranked


def _find_focus_source(cache: Dict[str, Any], focus_tour_id: Optional[int], items: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    if not focus_tour_id:
        return None

    overview_item = None
    first_item = None
    for item in items or []:
        if _safe_int(item.get("tour_id")) != focus_tour_id:
            continue
        first_item = first_item or item
        if item.get("chunk_type") == "overview":
            overview_item = item
            break
    if overview_item is not None:
        return overview_item

    chunks = cache.get("chunks") or []
    overview_candidate = None
    first_candidate = None
    for chunk in chunks:
        if _safe_int(chunk.get("tour_id")) != focus_tour_id:
            continue
        first_candidate = first_candidate or dict(chunk)
        if chunk.get("chunk_type") == "overview":
            overview_candidate = dict(chunk)
            break
    return overview_candidate or first_candidate or first_item


def _extract_text_field(text: str, label: str) -> str:
    pattern = rf"{re.escape(label)}:\s*([^\.]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return _normalize_whitespace(match.group(1)) if match else ""


def _parse_iso_date(value: str) -> Optional[datetime]:
    cleaned = _normalize_whitespace(value)
    if not cleaned or cleaned.upper() == "N/A":
        return None
    try:
        return datetime.strptime(cleaned[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _format_date_label(value: str) -> str:
    parsed = _parse_iso_date(value)
    return parsed.strftime("%d/%m/%Y") if parsed else "chưa có lịch cụ thể"


def _focus_tour_facts(focus_source: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    source = focus_source or {}
    text = str(source.get("text") or "")
    capacity = _safe_int(source.get("capacity"))
    if capacity <= 0:
        capacity = _safe_int(_extract_text_field(text, "Suc chua"))

    booking_count = _safe_int(source.get("booking_count"))
    if booking_count <= 0:
        booking_count = _safe_int(_extract_text_field(text, "So booking da xac nhan"))

    start_date = str(source.get("start_date") or _extract_text_field(text, "Khoi hanh") or "")
    end_date = str(source.get("end_date") or _extract_text_field(text, "Ket thuc") or "")
    status = str(source.get("status") or _extract_text_field(text, "Trang thai") or "")
    remaining_seats = max(capacity - booking_count, 0) if capacity > 0 else 0

    return {
        "capacity": capacity,
        "booking_count": booking_count,
        "start_date": start_date,
        "end_date": end_date,
        "status": _normalize_whitespace(status or "Available"),
        "remaining_seats": remaining_seats,
    }


def _duration_label(start_date: str, end_date: str) -> str:
    start = _parse_iso_date(start_date)
    end = _parse_iso_date(end_date)
    if start is None or end is None or end < start:
        return ""
    day_count = (end - start).days + 1
    if day_count <= 1:
        return "1 ngày"
    return f"{day_count} ngày {max(day_count - 1, 1)} đêm"


def _detect_transport_hint(text: str) -> str:
    normalized = normalize_text(text)
    mapping = [
        ("may bay", "máy bay"),
        ("xe khach", "xe khách"),
        ("xe bus", "xe buýt"),
        ("tau", "tàu"),
        ("oto", "ô tô"),
    ]
    for needle, label in mapping:
        if needle in normalized:
            return label
    return ""


def _focus_question_answer(query: str, focus_source: Optional[Dict[str, Any]]) -> Optional[str]:
    if not focus_source:
        return None

    normalized_query = normalize_text(query)
    title = str(focus_source.get("title") or "Tour này")
    location = str(focus_source.get("location") or "chưa rõ địa điểm")
    category = str(focus_source.get("category_name") or "chưa rõ danh mục")
    price = _safe_float(focus_source.get("price"))
    price_label = f"{price:,.0f} VND" if price > 0 else "chưa có giá trong hệ thống"
    facts = _focus_tour_facts(focus_source)
    duration_label = _duration_label(facts["start_date"], facts["end_date"])
    start_label = _format_date_label(facts["start_date"])
    end_label = _format_date_label(facts["end_date"])
    transport_label = _detect_transport_hint(str(focus_source.get("text") or ""))

    price_terms = ["gia", "chi phi", "ton bao nhieu", "muc gia", "gia tour"]
    location_terms = ["o dau", "dia diem", "noi nao", "di dau"]
    suitable_terms = ["phu hop voi ai", "phu hop voi", "ai nen di", "co hop", "nen di khong"]
    duration_terms = ["thoi luong", "bao lau", "may ngay", "keo dai bao lau", "di bao nhieu ngay"]
    schedule_terms = ["lich trinh", "lich di", "khoi hanh", "ngay di", "bat dau", "ket thuc", "lich tour"]
    transport_terms = ["phuong tien", "di bang gi", "xe hay may bay", "may bay hay xe", "van chuyen"]
    remaining_terms = ["con bao nhieu cho", "con cho", "so cho", "cho trong", "het cho", "con slot"]

    if any(term in normalized_query for term in price_terms):
        return f"{title} hiện có giá khoảng {price_label}."

    if any(term in normalized_query for term in location_terms):
        return f"{title} hiện đang được giới thiệu cho điểm đến {location}."

    if any(term in normalized_query for term in duration_terms):
        if duration_label:
            return f"{title} dự kiến kéo dài {duration_label}, từ {start_label} đến {end_label}."
        return f"Hiện mình chưa thấy đủ dữ liệu để chốt thời lượng cụ thể của {title}."

    if any(term in normalized_query for term in schedule_terms):
        if start_label != "chưa có lịch cụ thể" or end_label != "chưa có lịch cụ thể":
            return (
                f"Lịch hiện có của {title}: khởi hành {start_label}, kết thúc {end_label}, điểm đến chính là {location}. "
                "Chi tiết từng ngày của lịch trình chưa được lưu tách riêng trong dữ liệu hiện tại."
            )
        return f"Hiện mình chưa thấy lịch khởi hành cụ thể của {title} trong dữ liệu hệ thống."

    if any(term in normalized_query for term in transport_terms):
        if transport_label:
            return f"Theo dữ liệu mình đọc được, {title} đang nhắc đến phương tiện {transport_label}."
        return f"Hiện dữ liệu của {title} chưa có trường phương tiện riêng, nên mình chưa dám khẳng định là đi máy bay, xe hay tàu."

    if any(term in normalized_query for term in remaining_terms):
        if facts["capacity"] > 0:
            return (
                f"{title} có sức chứa tối đa {facts['capacity']} khách. "
                f"Hiện đã có khoảng {facts['booking_count']} booking xác nhận nên còn khoảng {facts['remaining_seats']} chỗ."
            )
        return f"Hiện mình chưa thấy thông tin sức chứa cụ thể của {title}."

    if any(term in normalized_query for term in suitable_terms):
        duration_text = f", thời lượng khoảng {duration_label}" if duration_label else ""
        return (
            f"Nếu bạn đang hỏi riêng {title}, tour này phù hợp với người muốn đi {location}, "
            f"thuộc nhóm {category}, mức giá khoảng {price_label}{duration_text}. "
            "Nếu bạn muốn, mình có thể tư vấn kỹ hơn theo gia đình, cặp đôi hoặc ngân sách cụ thể."
        )

    return None


# Intents that act as HARD filters: results that don't match are always excluded.
_HARD_FILTER_INTENTS = ("beach", "mountain", "international", "hot_weather")


def _filter_results_by_intent(items: List[Dict[str, Any]], query: str, top_k: int) -> List[Dict[str, Any]]:
    intents = extract_query_intents(query)
    has_hard_intent = any(intents.get(k) for k in _HARD_FILTER_INTENTS)

    def has_any(text: str, terms: List[str]) -> bool:
        return any(term in text for term in terms)

    strict_matches: List[Dict[str, Any]] = []
    for item in items:
        text = source_match_text(item)
        match = True
        if intents.get("international"):
            # international is exclusive: must match
            match = match and has_any(text, INTERNATIONAL_TERMS)
        elif intents.get("domestic") and has_any(text, INTERNATIONAL_TERMS):
            # user explicitly said "trong nước / nội địa" → exclude international tours
            match = False
        if intents.get("beach"):
            match = match and has_any(text, BEACH_TERMS)
        if intents.get("mountain"):
            match = match and has_any(text, MOUNTAIN_TERMS)
        if intents.get("hot_weather"):
            match = match and (has_any(text, BEACH_TERMS) or has_any(text, MOUNTAIN_TERMS) or has_any(text, RELAX_TERMS))
        if match:
            strict_matches.append(item)

    # If a hard intent was detected but nothing matched, return empty so fallback
    # gives an honest "no matching tour" message instead of wrong results.
    if has_hard_intent and not strict_matches:
        return []

    candidates = strict_matches if strict_matches else items

    # Price-based sort overrides relevance score for budget / premium intents.
    if intents.get("budget"):
        candidates = sorted(candidates, key=lambda x: _safe_float(x.get("price")) or float("inf"))
    elif intents.get("premium"):
        candidates = sorted(candidates, key=lambda x: _safe_float(x.get("price")) or 0.0, reverse=True)

    return candidates[:top_k]


def retrieve_documents(query: str, top_k: int = 4, focus_tour_id: Optional[int] = None) -> List[Dict[str, Any]]:
    cache = load_vector_store()
    started_at = time.perf_counter()
    intents = extract_query_intents(query)
    is_similar_query = intents.get("similar") and focus_tour_id

    # Resolve focused tour metadata for context-aware filtering
    focus_category: Optional[str] = None
    focus_location: Optional[str] = None
    if focus_tour_id:
        focus_src = _find_focus_source(cache, focus_tour_id)
        if focus_src:
            focus_category = normalize_text(str(focus_src.get("category_name") or ""))
            focus_location = normalize_text(str(focus_src.get("location") or ""))

    candidates = _collect_hybrid_candidates(query, cache, top_k=top_k)
    rescored: List[Dict[str, Any]] = []
    for item in candidates:
        enriched = dict(item)
        tour_id = _safe_int(enriched.get("tour_id"))

        # When user asks "similar": EXCLUDE the focused tour, boost same-category/location
        if is_similar_query:
            if tour_id == focus_tour_id:
                continue  # remove the current tour from similar results
            item_text = normalize_text(str(enriched.get("category_name") or ""))
            item_location = normalize_text(str(enriched.get("location") or ""))
            enriched["score"] = _intent_score_adjustment(query, enriched)
            if focus_category and focus_category in item_text:
                enriched["score"] = round(float(enriched.get("score") or 0.0) + 0.80, 4)
            if focus_location and focus_location in item_location:
                enriched["score"] = round(float(enriched.get("score") or 0.0) + 0.50, 4)
        else:
            enriched["score"] = _intent_score_adjustment(query, enriched)
            # Boost focused tour for non-similar queries
            if focus_tour_id and tour_id == focus_tour_id:
                enriched["score"] = round(float(enriched.get("score") or 0.0) + 1.5, 4)
        rescored.append(enriched)

    rescored.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
    deduped = _pick_best_chunk_per_tour(rescored)

    # For non-similar queries: ensure focused tour is always present
    if not is_similar_query:
        focus_source = _find_focus_source(cache, focus_tour_id, deduped)
        if focus_source is not None and all(_safe_int(item.get("tour_id")) != focus_tour_id for item in deduped):
            focus_enriched = dict(focus_source)
            focus_enriched["score"] = round(float(focus_enriched.get("score") or 0.0) + 1.5, 4)
            deduped = [focus_enriched, *deduped]
            deduped.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)

    final_results = _filter_results_by_intent(deduped, query=query, top_k=top_k)
    logger.info(
        "RAG retrieve query=%r top_k=%s candidates=%s results=%s similar=%s focus=%s latency_ms=%.1f",
        query, top_k, len(candidates), len(final_results),
        bool(is_similar_query), focus_tour_id,
        (time.perf_counter() - started_at) * 1000,
    )
    rag_metrics.observe("retrieve", (time.perf_counter() - started_at) * 1000)
    return final_results


def _fallback_answer(query: str, segment: Optional[Dict[str, Any]], sources: List[Dict[str, Any]], focus_source: Optional[Dict[str, Any]] = None) -> str:
    focus_answer = _focus_question_answer(query, focus_source)
    if focus_answer:
        return focus_answer

    intents = extract_query_intents(query)
    has_hard_intent = any(intents.get(k) for k in _HARD_FILTER_INTENTS)

    if not sources:
        if has_hard_intent:
            intent_label_map = {
                "beach": "tour biển",
                "mountain": "tour núi",
                "international": "tour nước ngoài",
                "hot_weather": "tour tránh nóng",
            }
            matched_labels = [label for key, label in intent_label_map.items() if intents.get(key)]
            label_text = " / ".join(matched_labels) if matched_labels else "yêu cầu này"
            return f"Hiện chưa có tour phù hợp với {label_text} trong dữ liệu. Bạn có thể thử hỏi theo tiêu chí khác hoặc xem danh sách tour hiện có."
        if intents.get("similar"):
            focus_title = str(focus_source.get("title") or "tour này") if focus_source else "tour này"
            focus_cat = str(focus_source.get("category_name") or "") if focus_source else ""
            cat_hint = f" danh mục '{focus_cat}'" if focus_cat else ""
            return (
                f"Hiện mình chưa tìm thấy tour nào khác tương tự với {focus_title}"
                f"{cat_hint} trong dữ liệu. Bạn thử hỏi theo địa điểm hoặc ngân sách nhé."
            )
        return "Hiện tôi chưa tìm thấy tour phù hợp trong dữ liệu. Bạn hãy hỏi rõ hơn về ngân sách, địa điểm hoặc thời gian đi."

    segment_name = str((segment or {}).get("segment_name") or "Khách mới")
    if intents.get("budget"):
        intro = f"Tour giá rẻ nhất hiện có cho bạn ({segment_name}):"
    elif intents.get("premium"):
        intro = f"Tour cao cấp giá cao nhất hiện có cho bạn ({segment_name}):"
    elif intents.get("international"):
        intro = f"Gợi ý tour nước ngoài cho bạn ({segment_name}):"
    elif intents.get("hot_weather"):
        intro = f"Nếu đang nóng, bạn có thể cân nhắc các tour mát mẻ sau ({segment_name}):"
    elif intents.get("beach"):
        intro = f"Gợi ý tour biển cho bạn ({segment_name}):"
    elif intents.get("mountain"):
        intro = f"Gợi ý tour núi cho bạn ({segment_name}):"
    elif intents.get("similar"):
        focus_title = str(focus_source.get("title") or "tour này") if focus_source else "tour này"
        intro = f"Các tour tương tự với {focus_title} mà bạn có thể thích ({segment_name}):"
    else:
        intro = f"Gợi ý phù hợp cho bạn ({segment_name}):"

    lines = [intro]
    for source in sources[:3]:
        price = _safe_float(source.get("price"))
        match_text = source_match_text(source)
        reasons: List[str] = []
        if intents.get("beach") and any(term in match_text for term in BEACH_TERMS):
            reasons.append("hợp nhu cầu đi biển")
        if intents.get("mountain") and any(term in match_text for term in MOUNTAIN_TERMS):
            reasons.append("khí hậu mát")
        if intents.get("hot_weather") and any(term in match_text for term in BEACH_TERMS + MOUNTAIN_TERMS + RELAX_TERMS):
            reasons.append("phù hợp để tránh nóng")
        reason_text = f"; lý do: {', '.join(reasons)}" if reasons else ""
        lines.append(
            f"- {source.get('title')} ở {source.get('location')}, giá khoảng {price:,.0f} VND, danh mục {source.get('category_name')}{reason_text}."
        )
    return "\n".join(lines)


def _generate_answer(query: str, segment: Optional[Dict[str, Any]], sources: List[Dict[str, Any]], max_context_chars: int, focus_source: Optional[Dict[str, Any]] = None, focus_tour_id: Optional[int] = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_answer(query, segment, sources, focus_source=focus_source)

    context = build_context(sources, max_context_chars=max_context_chars)
    payload = {
        "model": DEFAULT_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": build_system_prompt(segment)},
            {"role": "user", "content": build_user_prompt(query, segment, context, focus_tour_id=focus_tour_id, focus_source=focus_source)},
        ],
        "temperature": settings.answer_temperature,
        "max_tokens": settings.answer_max_tokens,
    }

    try:
        response = _HTTP_SESSION.post(
            f"{DEFAULT_OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=settings.openai_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        rag_metrics.increment("openai_answer_fallback_total")
        logger.exception("OpenAI answer generation failed for query=%r", query)
        return _fallback_answer(query, segment, sources, focus_source=focus_source)


def answer_chat(query: str, user_id: Optional[int] = None, top_k: int = 4, max_context_chars: int = 3500, focus_tour_id: Optional[int] = None) -> Dict[str, Any]:
    cache = load_vector_store()
    started_at = time.perf_counter()
    rag_metrics.mark_request(query)
    segment = get_user_segment(user_id) if user_id else None
    response_cache_key = _response_cache_key(query, user_id, top_k, cache, segment, focus_tour_id=focus_tour_id)
    redis_cache = _get_redis_cache()

    if redis_cache is not None:
        cached_response = redis_cache.get_json(response_cache_key)
        if cached_response is not None:
            rag_metrics.increment("response_cache_hits_redis")
            logger.info("RAG response cache hit (redis) query=%r", query)
            return cached_response

    local_response = _LOCAL_RESPONSE_CACHE.get(response_cache_key)
    if local_response is not None:
        rag_metrics.increment("response_cache_hits_memory")
        logger.info("RAG response cache hit (memory) query=%r", query)
        return local_response

    sources = retrieve_documents(query, top_k=top_k, focus_tour_id=focus_tour_id)
    focus_source = _find_focus_source(cache, focus_tour_id, sources)
    answer = _generate_answer(query, segment, sources, max_context_chars=max_context_chars, focus_source=focus_source, focus_tour_id=focus_tour_id)
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info("RAG answer query=%r latency_ms=%.1f sources=%s", query, latency_ms, len(sources))
    rag_metrics.observe("answer", latency_ms)

    payload = {
        "answer": answer,
        "query": query,
        "top_k": top_k,
        "retriever": str((cache.get("state") or {}).get("retriever") or "hybrid-faiss-bm25"),
        "embedding_provider": str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf"),
        "segment": segment,
        "sources": sources,
    }
    _LOCAL_RESPONSE_CACHE.set(response_cache_key, payload, settings.response_cache_ttl_seconds)
    if redis_cache is not None:
        redis_cache.set_json(response_cache_key, payload, settings.response_cache_ttl_seconds)
    return payload