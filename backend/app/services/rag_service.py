from __future__ import annotations

import hashlib
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
from app.services.rag.knowledge_base import load_knowledge_chunks
from app.services.rag.intents import (
    BEACH_TERMS,
    DOMESTIC_TERMS,
    DOMESTIC_EXPLICIT_TERMS,
    FAMILY_TERMS,
    INTERNATIONAL_TERMS,
    MOUNTAIN_TERMS,
    RELAX_TERMS,
    SIMILAR_TERMS,
    extract_meaningful_tokens,
    extract_query_intents,
    is_followup_query,
    normalize_text,
    source_match_text,
)
from app.services.rag.metrics import rag_metrics
from app.services.rag.prompting import (
    build_context,
    build_out_of_scope_prompts,
    build_system_prompt,
    build_user_prompt,
)
from app.services.rag.runtime_config import apply_runtime_override, get_runtime_config

try:
    import faiss  # type: ignore
except Exception:
    faiss = None

# ---------------------------------------------------------------------------
# Optional sentence-transformers (local SBERT embedding + cross-encoder rerank)
# WHY SBERT > TF-IDF: SentenceTransformer encodes semantic meaning across 50+
# languages including Vietnamese. TF-IDF is a bag-of-words model with no
# understanding of synonyms, paraphrases, or multilingual equivalence.
# WHY cross-encoder reranker: bi-encoders (FAISS/BM25) score query and doc
# independently; a cross-encoder attends to both simultaneously giving far
# more accurate relevance judgements on the shortlisted candidates.
# ---------------------------------------------------------------------------
_DISABLE_SBERT = os.getenv("DISABLE_SBERT", "0").strip().lower() in ("1", "true", "yes")

try:
    if _DISABLE_SBERT:
        raise ImportError("SBERT disabled via DISABLE_SBERT env var")
    from sentence_transformers import SentenceTransformer as _SentenceTransformer  # type: ignore
    _SBERT_AVAILABLE = True
except ImportError:
    _SentenceTransformer = None  # type: ignore
    _SBERT_AVAILABLE = False

try:
    if _DISABLE_SBERT:
        raise ImportError("CrossEncoder disabled via DISABLE_SBERT env var")
    from sentence_transformers.cross_encoder import CrossEncoder as _CrossEncoder  # type: ignore
    _CROSS_ENCODER_AVAILABLE = True
except ImportError:
    _CrossEncoder = None  # type: ignore
    _CROSS_ENCODER_AVAILABLE = False

_SBERT_MODEL: Optional[Any] = None
_CROSS_ENCODER_MODEL: Optional[Any] = None


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


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Cắt text tại word boundary gần nhất, không cắt giữa từ."""
    if len(text) <= max_chars:
        return text.rstrip(" .,;:")
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        truncated = truncated[:last_space]
    return truncated.rstrip(" .,;:") + "..."


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    if vectors.size == 0:
        return vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def _get_sbert_model() -> Optional[Any]:
    """Lazy-load SentenceTransformer for local embedding.

    WHY: paraphrase-multilingual-MiniLM-L12-v2 (384-dim) understands Vietnamese
    semantics, while TF-IDF treats every word independently with no meaning.
    Upgrade path: set RAG_LOCAL_EMBEDDING_MODEL=intfloat/multilingual-e5-base
    for 768-dim vectors with even better Vietnamese coverage.
    """
    global _SBERT_MODEL
    if not _SBERT_AVAILABLE or _SentenceTransformer is None:
        return None
    if _SBERT_MODEL is not None:
        return _SBERT_MODEL
    try:
        _SBERT_MODEL = _SentenceTransformer(settings.local_embedding_model)
        logger.info("Loaded local SentenceTransformer: %s", settings.local_embedding_model)
        return _SBERT_MODEL
    except Exception:
        logger.warning("Failed to load SentenceTransformer, falling back to TF-IDF", exc_info=False)
        return None


def _get_cross_encoder(runtime_cfg: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """Lazy-load CrossEncoder for re-ranking.

    WHY: Cross-encoders process (query, document) pairs jointly, enabling
    fine-grained interaction signals that bi-encoders miss. Applied on the
    top-N candidates after hybrid retrieval it dramatically improves precision
    without hurting recall. BAAI/bge-reranker-base is multilingual and works
    well for Vietnamese.
    """
    global _CROSS_ENCODER_MODEL
    cfg = runtime_cfg or get_runtime_config()
    enabled = bool(cfg.get("reranker_enabled", settings.reranker_enabled))
    model_name = str(cfg.get("reranker_model") or settings.reranker_model).strip()
    if not enabled:
        return None
    if not _CROSS_ENCODER_AVAILABLE or _CrossEncoder is None:
        return None
    if _CROSS_ENCODER_MODEL is not None and getattr(_CROSS_ENCODER_MODEL, "_model_name_cached", model_name) == model_name:
        return _CROSS_ENCODER_MODEL
    try:
        model = _CrossEncoder(model_name)
        setattr(model, "_model_name_cached", model_name)
        _CROSS_ENCODER_MODEL = model
        logger.info("Loaded CrossEncoder reranker: %s", model_name)
        return _CROSS_ENCODER_MODEL
    except Exception:
        logger.warning("Failed to load CrossEncoder reranker, reranking disabled", exc_info=False)
        return None


def _call_local_sbert_embeddings(texts: List[str]) -> np.ndarray:
    """Encode texts with the local SentenceTransformer model."""
    model = _get_sbert_model()
    if model is None:
        raise RuntimeError("SentenceTransformer model not available")
    embeddings = model.encode(
        texts,
        batch_size=min(settings.embedding_batch_size, 64),
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return np.array(embeddings, dtype="float32")


def _fit_local_embeddings(texts: List[str]) -> Tuple[Optional[TfidfVectorizer], np.ndarray]:
    """Build local embeddings. Uses SBERT when available, falls back to TF-IDF.

    WHY the preference order:
    - SBERT (paraphrase-multilingual-MiniLM-L12-v2): semantic, multilingual,
      captures synonyms and paraphrases — massive improvement for Vietnamese.
    - TF-IDF: sparse bag-of-words fallback, zero dependencies but no semantics.
    """
    sbert = _get_sbert_model()
    if sbert is not None:
        vectors = _call_local_sbert_embeddings(texts)
        return None, vectors  # no vectorizer object needed
    # Fallback: TF-IDF
    vectorizer = TfidfVectorizer(max_features=4096, ngram_range=(1, 2), min_df=1)
    vectors = vectorizer.fit_transform(texts).toarray().astype("float32")
    return vectorizer, vectors


def _batched(items: List[str], batch_size: int) -> List[List[str]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def _call_openai_embeddings(texts: List[str], runtime_cfg: Optional[Dict[str, Any]] = None) -> np.ndarray:
    cfg = runtime_cfg or get_runtime_config()
    api_key = str(cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    base_url = str(cfg.get("openai_base_url") or DEFAULT_OPENAI_BASE_URL).rstrip("/")
    embedding_model = str(cfg.get("embedding_model") or DEFAULT_EMBEDDING_MODEL).strip()

    vectors: List[np.ndarray] = []
    for batch in _batched(texts, settings.embedding_batch_size):
        response = _HTTP_SESSION.post(
            f"{base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": embedding_model,
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


def _load_tour_rows_from_metadata() -> List[Dict[str, Any]]:
    """Fallback tour loader using existing rag_store/chunks.json when MySQL is unavailable."""
    if not METADATA_FILE.exists():
        return []
    try:
        chunks = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    by_tour: Dict[int, Dict[str, Any]] = {}
    desc_parts: Dict[int, List[str]] = {}
    review_parts: Dict[int, List[str]] = {}

    for chunk in chunks:
        tour_id = _safe_int(chunk.get("tour_id"))
        if tour_id <= 0:
            continue
        entry = by_tour.setdefault(
            tour_id,
            {
                "tour_id": tour_id,
                "title": chunk.get("title") or f"Tour {tour_id}",
                "location": chunk.get("location") or "",
                "description": "",
                "price": _safe_float(chunk.get("price")),
                "start_date": None,
                "end_date": None,
                "capacity": 0,
                "status": "Available",
                "category_name": chunk.get("category_name") or "General",
                "avg_rating": 0.0,
                "booking_count": 0,
                "review_snippets": "",
            },
        )
        chunk_type = str(chunk.get("chunk_type") or "")
        text = str(chunk.get("text") or "")
        title = str(chunk.get("title") or entry["title"])

        if chunk_type == "overview":
            raw_start = chunk.get("start_date") or _extract_text_field(text, "Khoi hanh")
            raw_end = chunk.get("end_date") or _extract_text_field(text, "Ket thuc")
            entry["start_date"] = None if not raw_start or str(raw_start).upper() == "N/A" else str(raw_start)
            entry["end_date"] = None if not raw_end or str(raw_end).upper() == "N/A" else str(raw_end)
            entry["capacity"] = _safe_int(chunk.get("capacity") or _extract_text_field(text, "Suc chua"))
            entry["status"] = str(chunk.get("status") or _extract_text_field(text, "Trang thai") or "Available")
            entry["booking_count"] = _safe_int(
                chunk.get("booking_count") or _extract_text_field(text, "So booking da xac nhan")
            )
            entry["avg_rating"] = _safe_float(_extract_text_field(text, "Danh gia trung binh"))
        elif chunk_type.startswith("description_"):
            prefix = f"Mo ta tour {title}: "
            clean = text[len(prefix) :] if text.startswith(prefix) else text
            if clean:
                desc_parts.setdefault(tour_id, []).append(clean)
        elif chunk_type.startswith("reviews_"):
            prefix = f"Nhan xet khach hang ve tour {title}: "
            clean = text[len(prefix) :] if text.startswith(prefix) else text
            if clean:
                review_parts.setdefault(tour_id, []).append(clean)

    for tour_id, entry in by_tour.items():
        entry["description"] = " ".join(desc_parts.get(tour_id, []))
        entry["review_snippets"] = " | ".join(review_parts.get(tour_id, []))

    return sorted(by_tour.values(), key=lambda row: row["tour_id"], reverse=True)


def _generate_enrichment_text(title: str, location: str, category_name: str, price: float, avg_rating: float, booking_count: int) -> str:
    """Generate a rich synthetic keyword chunk from tour metadata to improve RAG retrieval."""
    loc = normalize_text(location or "")
    cat = normalize_text(category_name or "")
    parts: List[str] = [f"Tour {title} tai {location}, danh muc {category_name}."]

    def has_any_phrase(text: str, phrases: List[str]) -> bool:
        normalized_text = re.sub(r"[^a-z0-9]+", " ", text).strip()
        padded_text = f" {normalized_text} "
        for phrase in phrases:
            normalized_phrase = re.sub(r"[^a-z0-9]+", " ", normalize_text(phrase)).strip()
            if normalized_phrase and f" {normalized_phrase} " in padded_text:
                return True
        return False

    # ---- Geography & destination type ----
    domestic_keywords = ["ha long", "sa pa", "fansipan", "ninh binh", "trang an", "tam coc", "viet nam",
                         "ha noi", "sai gon", "hcm", "da nang", "hoi an", "phu quoc", "nha trang",
                         "da lat", "mui ne", "quy nhon", "gia lai", "kon tum", "vinh long"]
    sea_keywords = ["ha long", "phu quoc", "nha trang", "da nang", "mui ne", "quy nhon", "con dao", "vung tau"]
    mountain_keywords = ["sa pa", "fansipan", "da lat", "sapa", "nui", "everland", "blue mountains"]
    intl_asean_keywords = ["bangkok", "pattaya", "thai lan", "singapore", "kuala lumpur", "malaysia",
                           "bali", "indonesia", "philippines", "myanmar", "campuchia", "cambodia"]
    intl_east_asia = ["tokyo", "nhat ban", "japan", "seoul", "han quoc", "korea", "hong kong",
                      "ma cao", "macau", "dai bac", "cao hung", "taiwan", "dai loan"]
    intl_europe = ["paris", "versailles", "phap", "france", "anh quoc", "italy", "duc", "tay ban nha", "bac au",
                   "ha lan", "thuy si", "bi", "ao", "chau au", "europa"]
    intl_oceania = ["sydney", "uc", "australia", "new zealand", "blue mountains"]
    intl_middle_east = ["dubai", "abu dhabi", "uae", "saudi", "trung dong"]

    geo_tags: List[str] = []
    if has_any_phrase(loc, domestic_keywords) or "du lich trong nuoc" in cat:
        geo_tags += ["du lich trong nuoc", "viet nam", "noi dia"]
    else:
        geo_tags += ["du lich nuoc ngoai", "quoc te", "international"]
    if has_any_phrase(loc, intl_asean_keywords):
        geo_tags += ["dong nam a", "asean", "chau a"]
    if has_any_phrase(loc, intl_east_asia):
        geo_tags += ["dong a", "chau a"]
    if has_any_phrase(loc, intl_europe):
        geo_tags += ["chau au", "europe", "nuoc ngoai"]
    if has_any_phrase(loc, intl_oceania):
        geo_tags += ["chau dai duong", "uc", "australia"]
    if has_any_phrase(loc, intl_middle_east):
        geo_tags += ["trung dong", "chau phi", "nuoc ngoai"]
    if has_any_phrase(loc, sea_keywords):
        geo_tags += ["tour bien", "bien ca", "bai bien", "resort bien", "tam bien"]
    if has_any_phrase(loc, mountain_keywords):
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
        raw_start = row.get("start_date")
        raw_end = row.get("end_date")
        start_date = raw_start.isoformat() if hasattr(raw_start, "isoformat") else (str(raw_start) if raw_start else "N/A")
        end_date = raw_end.isoformat() if hasattr(raw_end, "isoformat") else (str(raw_end) if raw_end else "N/A")

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
    runtime_cfg = get_runtime_config()
    try:
        rows = _fetch_tour_rows()
        data_source = "mysql"
    except Exception as exc:
        logger.warning("Database unavailable during RAG index build (%s); falling back to metadata", exc)
        rows = _load_tour_rows_from_metadata()
        data_source = "metadata-fallback"
    chunks = _build_chunks(rows)

    # --- Integrate Vietnam tourism knowledge base ---
    # WHY: Knowledge chunks from train/valid_vietnam_tourism.json describe
    # destinations in depth. They bridge the vocabulary gap between natural
    # user queries ("Hội An có gì hay?") and sparse tour metadata fields.
    # BM25 benefits most: knowledge chunks contain the exact Vietnamese terms.
    kb_enabled = bool(runtime_cfg.get("knowledge_base_enabled", settings.knowledge_base_enabled))
    if kb_enabled:
        kb_chunks = load_knowledge_chunks(max_chunks=settings.knowledge_base_max_chunks)
        if kb_chunks:
            chunks.extend(kb_chunks)
            logger.info("Added %d knowledge base chunks to RAG index", len(kb_chunks))

    texts = [chunk["text"] for chunk in chunks]
    if not texts:
        raise RuntimeError("No tour data found to build the RAG index")

    vectorizer = None
    _openai_key = str(runtime_cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY") or "").strip()
    _openai_base = str(runtime_cfg.get("openai_base_url") or os.getenv("OPENAI_BASE_URL") or "").strip()
    _provider = str(runtime_cfg.get("llm_provider") or "openai").lower()
    _use_openai_embeddings = (
        bool(_openai_key)
        and _provider not in ("groq", "gemini", "openrouter", "local_fallback")
        and "groq.com" not in _openai_base
        and "generativelanguage.googleapis.com" not in _openai_base
    )
    embedding_provider = ""
    if _use_openai_embeddings:
        try:
            vectors = _call_openai_embeddings(texts, runtime_cfg=runtime_cfg)
            embedding_provider = "openai"
        except Exception as exc:
            logger.warning("OpenAI embedding build failed (%s), falling back to local embeddings", exc)

    if not embedding_provider:
        if _get_sbert_model() is not None:
            # WHY: SBERT produces 384-dim dense vectors that capture semantic
            # meaning in Vietnamese, far superior to TF-IDF for this use-case.
            # Set OPENAI_API_KEY to use text-embedding-3-large for best quality.
            _, vectors = _fit_local_embeddings(texts)
            embedding_provider = "local-sbert"
        else:
            vectorizer, vectors = _fit_local_embeddings(texts)
            embedding_provider = "local-tfidf"

    vectors = _normalize_vectors(vectors.astype("float32"))
    index = None
    if faiss is not None and vectors.size:
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        faiss.write_index(index, str(INDEX_FILE))

    np.save(VECTORS_FILE, vectors)
    METADATA_FILE.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    dense_w = float(runtime_cfg.get("hybrid_dense_weight", settings.hybrid_dense_weight))
    lexical_w = float(runtime_cfg.get("hybrid_lexical_weight", settings.hybrid_lexical_weight))
    emb_model_name = str(runtime_cfg.get("embedding_model") or DEFAULT_EMBEDDING_MODEL)

    state = {
        "built_at": int(time.time()),
        "document_count": len(chunks),
        "tour_count": len(rows),
        "data_source": data_source,
        "embedding_provider": embedding_provider,
        "embedding_model": (
            emb_model_name if embedding_provider == "openai"
            else settings.local_embedding_model if embedding_provider == "local-sbert"
            else "tfidf"
        ),
        "retriever": "hybrid-faiss-bm25" if faiss is not None else "hybrid-numpy-bm25",
        "chunking": {
            "description_chunk_size_words": settings.chunk_size_words,
            "review_chunk_size_words": settings.review_chunk_size_words,
            "overlap_sentences": settings.chunk_overlap_sentences,
        },
        "weights": {
            "dense": dense_w,
            "lexical": lexical_w,
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
    logger.info("RAG index built in %.2fs with %s chunks across %s tours (%s)", time.perf_counter() - started_at, len(chunks), len(rows), data_source)

    return {
        "message": "RAG index built successfully",
        "documents": len(chunks),
        "tour_count": len(rows),
        "data_source": data_source,
        "embedding_provider": embedding_provider,
        "path": str(RAG_DIR),
        "knowledge_base_enabled": kb_enabled,
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
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    state = cache_state.get("state") or {}
    built_at = state.get("built_at") or "0"
    embedding_provider = state.get("embedding_provider") or "local-tfidf"
    epoch = _get_response_cache_epoch()
    if history:
        trimmed = [
            {"role": str(t.get("role") or ""), "content": str(t.get("content") or "")[:200]}
            for t in history[-4:]
        ]
        history_sig = hashlib.md5(json.dumps(trimmed, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
    else:
        history_sig = "nohist"
    return (
        f"response:{embedding_provider}:{built_at}:{epoch}:{top_k}:{user_id or 0}:"
        f"{focus_tour_id or 0}:{history_sig}:{_segment_cache_signature(segment)}:{normalize_text(query)}"
    )


def _embed_query(query: str, cache: Dict[str, Any], runtime_cfg: Optional[Dict[str, Any]] = None) -> np.ndarray:
    provider = str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf")
    built_at = str((cache.get("state") or {}).get("built_at") or "0")
    cache_key = f"{provider}:{built_at}:{normalize_text(query)}"
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
        vectors = _call_openai_embeddings([query], runtime_cfg=runtime_cfg)
    elif provider == "local-sbert":
        # WHY: SBERT query embedding must match the SBERT document embeddings
        # stored in the index. Using TF-IDF transform here would give wrong dims.
        vectors = _call_local_sbert_embeddings([query])
    else:  # local-tfidf (legacy fallback)
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
    travel_hint_terms = ("tour", "du lich", "di", "nghi", "chuyen", "ve", "dat", "kham pha", "choi")
    if (
        len(normalized_query.split()) <= 3
        and not any(intents.values())
        and any(term in normalized_query for term in travel_hint_terms)
    ):
        expansions.append("tour du lich pho bien de di")

    return " ".join(dict.fromkeys(expansions))


def _contextualize_query_with_history(query: str, history: Optional[List[Dict[str, str]]]) -> str:
    if not history or not is_followup_query(query):
        return query

    prev_users: List[str] = []
    prev_assistant = ""
    for turn in reversed(history):
        role = str(turn.get("role") or "").strip().lower()
        content = _normalize_whitespace(turn.get("content"))
        if not content:
            continue
        if role == "assistant" and not prev_assistant:
            prev_assistant = content[:200]
        elif role == "user":
            prev_users.append(content)
            if len(prev_users) >= 2:
                break

    if not prev_users and not prev_assistant:
        return query

    deictic_terms = ("tour do", "tour nay", "tour dau", "tour thu", "cai dau", "cai thu", "cai do", "cai nay")
    norm_q = normalize_text(query)
    parts: List[str] = []
    for user_msg in prev_users:
        if extract_meaningful_tokens(user_msg) or any(extract_query_intents(user_msg).values()):
            parts.append(user_msg)
            break
    if not parts and prev_users:
        parts.append(prev_users[0])
    if prev_assistant and any(term in norm_q for term in deictic_terms):
        parts.append(prev_assistant)
    parts.append(query)
    return " ".join(parts)


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


def _rerank_candidates(query: str, items: List[Dict[str, Any]], runtime_cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Re-rank items using a cross-encoder model.

    WHY: The first-stage hybrid retriever scores query and document independently.
    A cross-encoder attends to the full (query, document) pair simultaneously,
    capturing subtle relevance signals — especially useful for Vietnamese where
    short queries can be highly ambiguous ("tour đẹp", "đi biển mùa hè").
    Falls back gracefully to original order if the model is not available.
    """
    cross_encoder = _get_cross_encoder(runtime_cfg=runtime_cfg)
    if cross_encoder is None or not items:
        return items
    try:
        texts = [str(item.get("text") or "")[:512] for item in items]
        pairs = [[query, text] for text in texts]
        scores = cross_encoder.predict(pairs)
        for item, score in zip(items, scores):
            item["rerank_score"] = round(float(score), 4)
        reranked = sorted(items, key=lambda x: float(x.get("rerank_score") or 0.0), reverse=True)
        rag_metrics.increment("reranker_calls_total")
        return reranked
    except Exception:
        logger.warning("Cross-encoder reranking failed, using original ordering", exc_info=False)
        rag_metrics.increment("reranker_fallback_total")
        return items


def _collect_hybrid_candidates(
    query: str,
    cache: Dict[str, Any],
    top_k: int,
    runtime_cfg: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    chunks = cache.get("chunks") or []
    if not chunks:
        return []

    cfg = runtime_cfg or get_runtime_config()
    dense_w = float(cfg.get("hybrid_dense_weight", settings.hybrid_dense_weight))
    lexical_w = float(cfg.get("hybrid_lexical_weight", settings.hybrid_lexical_weight))
    total_w = dense_w + lexical_w
    if total_w > 0:
        dense_w /= total_w
        lexical_w /= total_w
    else:
        dense_w, lexical_w = 0.68, 0.32

    expanded_query = _expand_query_for_retrieval(query)
    dense_k, lexical_k = _adaptive_search_k(query, top_k, len(chunks))
    query_vector = _embed_query(expanded_query, cache, runtime_cfg=cfg)

    dense = _dense_candidates(query_vector, cache, dense_k)
    lexical = _lexical_candidates(expanded_query, cache, lexical_k)
    raw_dense_map = {index: float(score) for index, score in dense}
    raw_lexical_map = {index: float(score) for index, score in lexical}

    max_raw_dense = max(raw_dense_map.values()) if raw_dense_map else 0.0
    max_raw_lexical = max(raw_lexical_map.values()) if raw_lexical_map else 0.0
    dense_confidence = min(1.0, max(0.0, max_raw_dense) / 0.30)
    lexical_confidence = min(1.0, max(0.0, max_raw_lexical) / 4.5)

    dense_scores = _normalize_score_map(dense)
    lexical_scores = _normalize_score_map(lexical)

    candidate_indices = set(dense_scores) | set(lexical_scores)
    combined: List[Dict[str, Any]] = []
    for index in candidate_indices:
        item = dict(chunks[index])
        raw_dense = raw_dense_map.get(index, 0.0)
        raw_lexical = raw_lexical_map.get(index, 0.0)
        dense_score = dense_scores.get(index, 0.0) * dense_confidence
        lexical_score = lexical_scores.get(index, 0.0) * lexical_confidence
        item["raw_dense_score"] = round(raw_dense, 4)
        item["raw_lexical_score"] = round(raw_lexical, 4)
        item["dense_score"] = round(dense_score, 4)
        item["lexical_score"] = round(lexical_score, 4)
        item["score"] = round(dense_score * dense_w + lexical_score * lexical_w, 4)
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
    """Deduplicate tour chunks (keep best per tour_id).

    Knowledge chunks (tour_id == 0) are kept separately — up to 2 are
    retained so the LLM receives background context without crowding out
    actual tour recommendations.
    """
    knowledge_items: List[Dict[str, Any]] = []
    best_by_tour: Dict[int, Dict[str, Any]] = {}
    for item in items:
        tour_id = _safe_int(item.get("tour_id"))
        if tour_id <= 0:
            # Knowledge chunk — collect separately, do NOT deduplicate
            knowledge_items.append(item)
            continue
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

    # Keep top-2 knowledge chunks sorted by score (enough context, not too many)
    knowledge_items.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    ranked = list(best_by_tour.values()) + knowledge_items[:2]
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


def retrieve_documents(
    query: str,
    top_k: int = 4,
    focus_tour_id: Optional[int] = None,
    history: Optional[List[Dict[str, str]]] = None,
    runtime_cfg: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    cache = load_vector_store()
    cfg = runtime_cfg or get_runtime_config()
    started_at = time.perf_counter()
    retrieval_query = _contextualize_query_with_history(query, history)
    intents = extract_query_intents(retrieval_query)
    is_similar_query = intents.get("similar") and focus_tour_id

    # Resolve focused tour metadata for context-aware filtering
    focus_category: Optional[str] = None
    focus_location: Optional[str] = None
    if focus_tour_id:
        focus_src = _find_focus_source(cache, focus_tour_id)
        if focus_src:
            focus_category = normalize_text(str(focus_src.get("category_name") or ""))
            focus_location = normalize_text(str(focus_src.get("location") or ""))

    candidates = _collect_hybrid_candidates(retrieval_query, cache, top_k=top_k, runtime_cfg=cfg)
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
            enriched["score"] = _intent_score_adjustment(retrieval_query, enriched)
            enriched["retrieval_score"] = enriched["score"]
            if focus_category and focus_category in item_text:
                enriched["score"] = round(float(enriched.get("score") or 0.0) + 0.80, 4)
            if focus_location and focus_location in item_location:
                enriched["score"] = round(float(enriched.get("score") or 0.0) + 0.50, 4)
        else:
            enriched["score"] = _intent_score_adjustment(retrieval_query, enriched)
            enriched["retrieval_score"] = enriched["score"]
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
            base_focus_score = float(focus_enriched.get("score") or 0.0)
            focus_enriched["retrieval_score"] = base_focus_score
            focus_enriched["score"] = round(base_focus_score + 1.5, 4)
            deduped = [focus_enriched, *deduped]
            deduped.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)

    reranker_enabled = bool(cfg.get("reranker_enabled", settings.reranker_enabled))
    filter_limit = max(top_k, settings.reranker_top_k) if reranker_enabled else top_k
    final_results = _filter_results_by_intent(deduped, query=retrieval_query, top_k=filter_limit)

    # --- Cross-encoder reranking (optional, enabled via Admin UI or RAG_RERANKER_ENABLED=true) ---
    # Re-ranks the broader candidate pool (reranker_top_k) BEFORE slicing to final top_k.
    if reranker_enabled and final_results:
        final_results = _rerank_candidates(query, final_results, runtime_cfg=cfg)
        final_results = final_results[:top_k]

    logger.info(
        "RAG retrieve query=%r top_k=%s candidates=%s results=%s similar=%s focus=%s reranker=%s latency_ms=%.1f",
        query, top_k, len(candidates), len(final_results),
        bool(is_similar_query), focus_tour_id,
        reranker_enabled,
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

    tour_sources = [source for source in sources if _safe_int(source.get("tour_id")) > 0]
    knowledge_sources = [source for source in sources if _safe_int(source.get("tour_id")) <= 0]

    top_source_is_knowledge = bool(sources) and _safe_int((sources[0] or {}).get("tour_id")) <= 0

    if knowledge_sources and (not tour_sources or top_source_is_knowledge):
        lines = [f"Thông tin tham khảo cho bạn ({segment_name}):"]
        for source in knowledge_sources[:3]:
            title = _normalize_whitespace(source.get("title") or "Thông tin du lịch")
            text = _normalize_whitespace(source.get("text") or "")
            if text.lower().startswith(f"{title.lower()}:"):
                text = text[len(title) + 1 :].strip()
            snippet = _truncate_at_word(text, 280)
            lines.append(f"- {title}: {snippet}")
        return "\n".join(lines)

    lines = [intro]
    for source in tour_sources[:3]:
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

    if knowledge_sources:
        tip = knowledge_sources[0]
        tip_title = _normalize_whitespace(tip.get("title") or "Thông tin du lịch")
        tip_text = _normalize_whitespace(tip.get("text") or "")
        if tip_text.lower().startswith(f"{tip_title.lower()}:"):
            tip_text = tip_text[len(tip_title) + 1 :].strip()
        tip_snippet = _truncate_at_word(tip_text, 260)
        lines.append(f"- Thông tin thêm: {tip_title} - {tip_snippet}")

    return "\n".join(lines)


def _sanitize_history(history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    if not history:
        return []
    cleaned: List[Dict[str, str]] = []
    for turn in history[-6:]:
        role = str(turn.get("role") or "").strip().lower()
        content = _normalize_whitespace(turn.get("content"))
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content[:600]})
    return cleaned


def _get_popular_tour_suggestions(cache: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    chunks = cache.get("chunks") or []
    best_by_tour: Dict[int, Dict[str, Any]] = {}
    for chunk in chunks:
        tour_id = _safe_int(chunk.get("tour_id"))
        if tour_id <= 0 or chunk.get("chunk_type") != "overview":
            continue
        status = str(chunk.get("status") or "Available").lower()
        if status == "unavailable" or status == "deleted":
            continue
        if tour_id not in best_by_tour:
            item = dict(chunk)
            item["score"] = 0.0
            best_by_tour[tour_id] = item
    ranked = sorted(
        best_by_tour.values(),
        key=lambda item: (_safe_int(item.get("booking_count")), _safe_float(item.get("price"))),
        reverse=True,
    )
    return ranked[:limit]


def _detect_out_of_scope(
    query: str,
    sources: List[Dict[str, Any]],
    similarity_threshold: float,
    focus_tour_id: Optional[int] = None,
    focus_source: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Tuple[bool, str, float]:
    """Check whether the query falls outside the indexed tour/knowledge catalog."""
    if not sources:
        return True, "no_matching_sources", 0.0

    max_score = max(float(s.get("retrieval_score", s.get("score")) or 0.0) for s in sources)
    max_raw_dense = max(float(s.get("raw_dense_score") or 0.0) for s in sources)
    max_raw_lexical = max(float(s.get("raw_lexical_score") or 0.0) for s in sources)
    intents = extract_query_intents(query)

    if focus_tour_id and focus_source is not None:
        if _focus_question_answer(query, focus_source) is not None or intents.get("similar"):
            return False, "in_scope_focus", round(max_score, 4)

    if history and is_followup_query(query):
        return False, "in_scope_followup", round(max_score, 4)

    if max_score < similarity_threshold:
        return True, "below_similarity_threshold", round(max_score, 4)

    norm_q = normalize_text(query)
    browsing_phrases = ("cac tour", "nhung tour", "tour nao", "goi y tour", "danh sach tour", "tu van tour", "co tour gi")
    tokens = extract_meaningful_tokens(query)
    if any(phrase in norm_q for phrase in browsing_phrases) and len(tokens) <= 1:
        return False, "in_scope_browsing", round(max_score, 4)

    if tokens and not any(intents.values()):
        top_text = " ".join(source_match_text(item) for item in sources[:3])
        top_words = set(re.findall(r"[a-z0-9]+", top_text))
        matched_tokens = [token for token in tokens if token in top_words]
        coverage = len(matched_tokens) / max(len(tokens), 1)
        if not matched_tokens:
            return True, "unmatched_topic_or_destination", round(max_score, 4)
        if coverage < 0.5 and max_raw_dense < max(similarity_threshold, 0.28) and max_raw_lexical < 5.0:
            return True, "unmatched_topic_or_destination", round(max_score, 4)

    return False, "in_scope", round(max_score, 4)


def _call_llm_chat(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    runtime_cfg: Dict[str, Any],
) -> str:
    provider = str(runtime_cfg.get("llm_provider") or "openai").strip().lower()
    api_key = str(runtime_cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY") or "").strip()
    base_url = str(runtime_cfg.get("openai_base_url") or DEFAULT_OPENAI_BASE_URL).strip().rstrip("/")

    if provider == "local_fallback" or not api_key or not base_url:
        raise RuntimeError("External LLM provider is disabled or missing API key")

    response = _HTTP_SESSION.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=settings.openai_timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    return str(data["choices"][0]["message"]["content"]).strip()


def _format_popular_tours_text(popular_tours: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for idx, item in enumerate(popular_tours[:3], start=1):
        price = _safe_float(item.get("price"))
        price_str = f"{price:,.0f} VND" if price > 0 else "Liên hệ"
        lines.append(
            f"{idx}. {item.get('title')} — {item.get('location')} "
            f"({item.get('category_name')}), giá khoảng {price_str}"
        )
    return "\n".join(lines)


def _generate_out_of_scope_answer(
    query: str,
    segment: Optional[Dict[str, Any]],
    popular_tours: List[Dict[str, Any]],
    runtime_cfg: Dict[str, Any],
    history: Optional[List[Dict[str, str]]] = None,
) -> Tuple[str, str]:
    oos_mode = str(runtime_cfg.get("out_of_scope_mode") or "general_travel").strip().lower()
    oos_model = str(runtime_cfg.get("out_of_scope_model") or runtime_cfg.get("chat_model") or DEFAULT_CHAT_MODEL).strip()
    oos_temp = float(runtime_cfg.get("out_of_scope_temperature", 0.5))
    oos_max_tokens = int(runtime_cfg.get("out_of_scope_max_tokens", 400))
    fallback_msg = str(runtime_cfg.get("out_of_scope_fallback_message") or "").strip() or (
        "Hiện tại hệ thống chưa có tour hoặc thông tin chi tiết khớp trực tiếp với yêu cầu này trong danh mục."
    )
    suggest_popular = bool(runtime_cfg.get("suggest_popular_tours_on_oos", True))
    popular_text = _format_popular_tours_text(popular_tours) if (suggest_popular and popular_tours) else ""

    if oos_mode == "strict":
        if popular_text:
            return f"{fallback_msg}\n\nMột số tour nổi bật hiện có để bạn tham khảo:\n{popular_text}", "strict-policy"
        return fallback_msg, "strict-policy"

    system_prompt, user_prompt = build_out_of_scope_prompts(
        query=query,
        segment=segment,
        mode=oos_mode,
        custom_system_prompt=str(runtime_cfg.get("out_of_scope_system_prompt") or ""),
        popular_tours_context=popular_text,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        *_sanitize_history(history),
        {"role": "user", "content": user_prompt},
    ]

    provider = str(runtime_cfg.get("llm_provider") or "openai").strip().lower()
    api_key = str(runtime_cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY") or "").strip()
    if provider != "local_fallback" and api_key:
        try:
            content = _call_llm_chat(
                messages=messages,
                model=oos_model,
                temperature=oos_temp,
                max_tokens=oos_max_tokens,
                runtime_cfg=runtime_cfg,
            )
            return content, oos_model
        except Exception:
            rag_metrics.increment("openai_answer_fallback_total")
            logger.exception("Out-of-scope LLM generation failed for query=%r model=%s", query, oos_model)

    if popular_text:
        return f"{fallback_msg}\n\nMột số tour nổi bật hiện có để bạn tham khảo:\n{popular_text}", "local-fallback"
    return fallback_msg, "local-fallback"


def _generate_answer(
    query: str,
    segment: Optional[Dict[str, Any]],
    sources: List[Dict[str, Any]],
    max_context_chars: int,
    focus_source: Optional[Dict[str, Any]] = None,
    focus_tour_id: Optional[int] = None,
    history: Optional[List[Dict[str, str]]] = None,
    runtime_cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    cfg = runtime_cfg or get_runtime_config()
    provider = str(cfg.get("llm_provider") or "openai").strip().lower()
    api_key = str(cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY") or "").strip()
    if provider == "local_fallback" or not api_key:
        return _fallback_answer(query, segment, sources, focus_source=focus_source), "local-fallback"

    chat_model = str(cfg.get("chat_model") or DEFAULT_CHAT_MODEL).strip()
    temperature = float(cfg.get("temperature", settings.answer_temperature))
    max_tokens = int(cfg.get("max_tokens", settings.answer_max_tokens))
    custom_addon = str(cfg.get("custom_system_prompt_addon") or "")

    context = build_context(sources, max_context_chars=max_context_chars)
    messages = [
        {"role": "system", "content": build_system_prompt(segment, custom_addon=custom_addon)},
        *_sanitize_history(history),
        {"role": "user", "content": build_user_prompt(query, segment, context, focus_tour_id=focus_tour_id, focus_source=focus_source)},
    ]

    try:
        content = _call_llm_chat(
            messages=messages,
            model=chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
            runtime_cfg=cfg,
        )
        return content, chat_model
    except Exception:
        rag_metrics.increment("openai_answer_fallback_total")
        logger.exception("OpenAI answer generation failed for query=%r", query)
        return _fallback_answer(query, segment, sources, focus_source=focus_source), "local-fallback"


def answer_chat(
    query: str,
    user_id: Optional[int] = None,
    top_k: Optional[int] = None,
    max_context_chars: int = 3500,
    focus_tour_id: Optional[int] = None,
    history: Optional[List[Dict[str, str]]] = None,
    config_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cache = load_vector_store()
    cfg = apply_runtime_override(get_runtime_config(), config_override)
    effective_top_k = int(top_k if top_k is not None else cfg.get("top_k_default", 4))
    started_at = time.perf_counter()
    rag_metrics.mark_request(query)

    segment = None
    if user_id:
        try:
            segment = get_user_segment(user_id)
        except Exception:
            segment = None

    use_cache = config_override is None
    response_cache_key = _response_cache_key(
        query,
        user_id,
        effective_top_k,
        cache,
        segment,
        focus_tour_id=focus_tour_id,
        history=history,
    )
    redis_cache = _get_redis_cache() if use_cache else None

    if use_cache and redis_cache is not None:
        cached_response = redis_cache.get_json(response_cache_key)
        if cached_response is not None:
            rag_metrics.increment("response_cache_hits_redis")
            logger.info("RAG response cache hit (redis) query=%r", query)
            return cached_response

    if use_cache:
        local_response = _LOCAL_RESPONSE_CACHE.get(response_cache_key)
        if local_response is not None:
            rag_metrics.increment("response_cache_hits_memory")
            logger.info("RAG response cache hit (memory) query=%r", query)
            return local_response

    sources = retrieve_documents(
        query,
        top_k=effective_top_k,
        focus_tour_id=focus_tour_id,
        history=history,
        runtime_cfg=cfg,
    )
    focus_source = _find_focus_source(cache, focus_tour_id, sources)
    similarity_threshold = float(cfg.get("similarity_threshold", 0.22))
    is_oos, oos_reason, max_score = _detect_out_of_scope(
        query,
        sources,
        similarity_threshold=similarity_threshold,
        focus_tour_id=focus_tour_id,
        focus_source=focus_source,
        history=history,
    )

    if is_oos:
        rag_metrics.increment("out_of_scope_total")
        suggest_popular = bool(cfg.get("suggest_popular_tours_on_oos", True))
        popular_tours = _get_popular_tour_suggestions(cache, limit=min(effective_top_k, 3)) if suggest_popular else []
        answer, model_used = _generate_out_of_scope_answer(
            query=query,
            segment=segment,
            popular_tours=popular_tours,
            runtime_cfg=cfg,
            history=history,
        )
        returned_sources = popular_tours if suggest_popular else []
        oos_mode_used: Optional[str] = str(cfg.get("out_of_scope_mode") or "general_travel")
    else:
        answer, model_used = _generate_answer(
            query,
            segment,
            sources,
            max_context_chars=max_context_chars,
            focus_source=focus_source,
            focus_tour_id=focus_tour_id,
            history=history,
            runtime_cfg=cfg,
        )
        returned_sources = sources
        oos_mode_used = None

    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "RAG answer query=%r oos=%s reason=%s model=%s latency_ms=%.1f sources=%s",
        query, is_oos, oos_reason, model_used, latency_ms, len(returned_sources),
    )
    rag_metrics.observe("answer", latency_ms)

    payload = {
        "answer": answer,
        "query": query,
        "top_k": effective_top_k,
        "retriever": str((cache.get("state") or {}).get("retriever") or "hybrid-faiss-bm25"),
        "embedding_provider": str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf"),
        "segment": segment,
        "sources": returned_sources,
        "is_out_of_scope": is_oos,
        "out_of_scope_reason": oos_reason if is_oos else None,
        "out_of_scope_mode": oos_mode_used,
        "model_used": model_used,
        "max_score": max_score,
        "latency_ms": latency_ms,
    }
    if use_cache:
        _LOCAL_RESPONSE_CACHE.set(response_cache_key, payload, settings.response_cache_ttl_seconds)
        if redis_cache is not None:
            redis_cache.set_json(response_cache_key, payload, settings.response_cache_ttl_seconds)
    return payload