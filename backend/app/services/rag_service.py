from __future__ import annotations

import json
import logging
import os
import pickle
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

from app.database import get_db_connection
from app.services.customer_segmentation_service import get_user_segment
from app.services.rag.bm25 import BM25Index
from app.services.rag.chunking import build_semantic_chunks
from app.services.rag.config import get_rag_settings
from app.services.rag.intents import (
    BEACH_TERMS,
    DOMESTIC_TERMS,
    FAMILY_TERMS,
    INTERNATIONAL_TERMS,
    MOUNTAIN_TERMS,
    RELAX_TERMS,
    extract_query_intents,
    normalize_text,
    source_match_text,
)
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
_QUERY_EMBED_CACHE: "OrderedDict[str, Tuple[float, np.ndarray]]" = OrderedDict()


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
                "chunk_type": "overview",
                "text": overview,
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
    _QUERY_EMBED_CACHE.clear()
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


def _prune_query_cache() -> None:
    now = time.time()
    expired_keys = [key for key, (expires_at, _) in _QUERY_EMBED_CACHE.items() if expires_at <= now]
    for key in expired_keys:
        _QUERY_EMBED_CACHE.pop(key, None)
    while len(_QUERY_EMBED_CACHE) > settings.query_cache_size:
        _QUERY_EMBED_CACHE.popitem(last=False)


def _embed_query(query: str, cache: Dict[str, Any]) -> np.ndarray:
    provider = str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf")
    cache_key = f"{provider}:{normalize_text(query)}"
    _prune_query_cache()
    cached = _QUERY_EMBED_CACHE.get(cache_key)
    if cached and cached[0] > time.time():
        _QUERY_EMBED_CACHE.move_to_end(cache_key)
        return cached[1]

    if provider == "openai":
        vectors = _call_openai_embeddings([query])
    else:
        vectorizer = cache.get("vectorizer")
        if vectorizer is None:
            raise RuntimeError("Local vectorizer is not loaded")
        vectors = vectorizer.transform([query]).toarray().astype("float32")

    normalized = _normalize_vectors(vectors.astype("float32"))
    _QUERY_EMBED_CACHE[cache_key] = (time.time() + settings.query_cache_ttl_seconds, normalized)
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


def _filter_results_by_intent(items: List[Dict[str, Any]], query: str, top_k: int) -> List[Dict[str, Any]]:
    intents = extract_query_intents(query)

    def has_any(text: str, terms: List[str]) -> bool:
        return any(term in text for term in terms)

    strict_matches: List[Dict[str, Any]] = []
    for item in items:
        text = source_match_text(item)
        match = True
        if intents.get("international"):
            match = match and has_any(text, INTERNATIONAL_TERMS)
        if intents.get("beach"):
            match = match and has_any(text, BEACH_TERMS)
        if intents.get("mountain"):
            match = match and has_any(text, MOUNTAIN_TERMS)
        if intents.get("hot_weather"):
            match = match and (has_any(text, BEACH_TERMS) or has_any(text, MOUNTAIN_TERMS) or has_any(text, RELAX_TERMS))
            if not intents.get("international"):
                match = match and not has_any(text, INTERNATIONAL_TERMS)
        if match:
            strict_matches.append(item)

    return (strict_matches or items)[:top_k]


def retrieve_documents(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    cache = load_vector_store()
    started_at = time.perf_counter()
    candidates = _collect_hybrid_candidates(query, cache, top_k=top_k)
    rescored: List[Dict[str, Any]] = []
    for item in candidates:
        enriched = dict(item)
        enriched["score"] = _intent_score_adjustment(query, enriched)
        rescored.append(enriched)

    rescored.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
    deduped = _pick_best_chunk_per_tour(rescored)
    final_results = _filter_results_by_intent(deduped, query=query, top_k=top_k)
    logger.info(
        "RAG retrieve query=%r top_k=%s candidates=%s results=%s latency_ms=%.1f",
        query,
        top_k,
        len(candidates),
        len(final_results),
        (time.perf_counter() - started_at) * 1000,
    )
    return final_results


def _fallback_answer(query: str, segment: Optional[Dict[str, Any]], sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "Hiện tôi chưa tìm thấy tour phù hợp trong dữ liệu. Bạn hãy hỏi rõ hơn về ngân sách, địa điểm hoặc thời gian đi."

    segment_name = str((segment or {}).get("segment_name") or "Khách mới")
    intents = extract_query_intents(query)
    if intents.get("international"):
        intro = f"Gợi ý tour nước ngoài cho bạn ({segment_name}):"
    elif intents.get("hot_weather"):
        intro = f"Nếu đang nóng, bạn có thể cân nhắc các tour mát mẻ sau ({segment_name}):"
    elif intents.get("beach"):
        intro = f"Gợi ý tour biển cho bạn ({segment_name}):"
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


def _generate_answer(query: str, segment: Optional[Dict[str, Any]], sources: List[Dict[str, Any]], max_context_chars: int) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_answer(query, segment, sources)

    context = build_context(sources, max_context_chars=max_context_chars)
    payload = {
        "model": DEFAULT_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": build_system_prompt(segment)},
            {"role": "user", "content": build_user_prompt(query, segment, context)},
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
        logger.exception("OpenAI answer generation failed for query=%r", query)
        return _fallback_answer(query, segment, sources)


def answer_chat(query: str, user_id: Optional[int] = None, top_k: int = 4, max_context_chars: int = 3500) -> Dict[str, Any]:
    cache = load_vector_store()
    started_at = time.perf_counter()
    segment = get_user_segment(user_id) if user_id else None
    sources = retrieve_documents(query, top_k=top_k)
    answer = _generate_answer(query, segment, sources, max_context_chars=max_context_chars)
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info("RAG answer query=%r latency_ms=%.1f sources=%s", query, latency_ms, len(sources))

    return {
        "answer": answer,
        "query": query,
        "top_k": top_k,
        "retriever": str((cache.get("state") or {}).get("retriever") or "hybrid-faiss-bm25"),
        "embedding_provider": str((cache.get("state") or {}).get("embedding_provider") or "local-tfidf"),
        "segment": segment,
        "sources": sources,
    }