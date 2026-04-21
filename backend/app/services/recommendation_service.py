from __future__ import annotations

import os
import time
import unicodedata
from typing import Any, Dict, List

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

from app.database import get_db_connection
from app.services.customer_segmentation_service import get_user_segment

try:
    import faiss  # type: ignore
except Exception:
    faiss = None


_RAG_CACHE: Dict[str, Any] = {
    "built_at": 0.0,
    "documents": [],
    "vectorizer": None,
    "vectors": None,
    "index": None,
}
_CACHE_TTL_SECONDS = 600

# Query-side intent keywords (normalized Vietnamese)
_BEACH_TERMS = ["bien", "beach", "island", "coast", "ha long", "nha trang", "phu quoc", "vung tau", "da nang", "quy nhon", "mui ne", "cat ba", "sam son", "con dao"]
_MOUNTAIN_TERMS = ["sa pa", "sapa", "lao cai", "phan xi pang", "da lat", "moc chau", "tam dao", "nui", "mountain"]
_FAMILY_TERMS = ["gia dinh", "family", "kids", "tre em"]
_RELAX_TERMS = ["nghi duong", "resort", "thu gian", "relax", "yen tinh"]
_HOT_WEATHER_TERMS = ["nong qua", "troi nong", "qua nong", "nang nong", "tranh nong", "mat me", "doi gio", "he nay", "summer", "cool"]
_INTERNATIONAL_TERMS = ["nuoc ngoai", "quoc te", "international", "thai lan", "singapore", "han quoc", "nhat ban", "chau au", "uc", "dubai", "uae"]
_PREMIUM_TERMS = ["cao cap", "luxury", "premium", "vip", "5 sao", "sang trong"]
_BUDGET_TERMS = ["gia re", "gia tot", "tiet kiem", "sale", "khuyen mai", "budget", "cheap", "affordable", "re nhat"]

# Document-side tag detection: deterministic location → tag mapping
# Keys use space-padded word matching, so keep them unambiguous (no single-letter words).
_LOCATION_TAG_MAP: Dict[str, List[str]] = {
    # Beach – domestic
    "ha long": ["beach"], "quang ninh": ["beach"],
    "nha trang": ["beach"], "khanh hoa": ["beach"],
    "phu quoc": ["beach"], "kien giang": ["beach"],
    "da nang": ["beach"], "vung tau": ["beach"],
    "ba ria": ["beach"], "quy nhon": ["beach"],
    "binh dinh": ["beach"], "mui ne": ["beach"],
    "binh thuan": ["beach"], "con dao": ["beach"],
    "cat ba": ["beach"], "hai phong": ["beach"],
    "sam son": ["beach"], "thanh hoa": ["beach"],
    "ly son": ["beach"], "quang ngai": ["beach"],
    # Mountain – domestic
    "sa pa": ["mountain"], "sapa": ["mountain"],
    "lao cai": ["mountain"], "da lat": ["mountain"],
    "lam dong": ["mountain"], "moc chau": ["mountain"],
    "son la": ["mountain"], "tam dao": ["mountain"],
    "vinh phuc": ["mountain"], "phan xi pang": ["mountain"],
    "ha giang": ["mountain"], "cao bang": ["mountain"],
    "ninh binh": ["mountain"],
    # International – use only unambiguous multi-word or long tokens
    "thai lan": ["international"], "bangkok": ["international"],
    "pattaya": ["international"], "singapore": ["international"],
    "han quoc": ["international"], "seoul": ["international"],
    "nhat ban": ["international"], "tokyo": ["international"],
    "osaka": ["international"], "chau au": ["international"],
    "paris": ["international"], "france": ["international"],
    "rome": ["international"], "sydney": ["international"],
    "australia": ["international"], "dubai": ["international"],
    "uae": ["international"], "trung quoc": ["international"],
    "bac kinh": ["international"], "new york": ["international"],
    "nuoc ngoai": ["international"], "ngoai nuoc": ["international"],
    "malaysia": ["international"], "kuala lumpur": ["international"],
    "indo": ["international"], "bali": ["international"],
}


def detect_tags(item: Dict[str, Any]) -> List[str]:
    """Assign semantic tags to a document. Uses word-boundary matching to
    prevent short keys like 'uc'/'my' from matching inside other words."""
    raw = " ".join([
        str(item.get("title") or ""),
        str(item.get("location") or ""),
        str(item.get("category_name") or ""),
        str(item.get("description") or "")[:300],
    ])
    text = " " + _normalize_text(raw) + " "  # pad for word-boundary checks
    tags: set = set()

    for key, key_tags in _LOCATION_TAG_MAP.items():
        # Match whole words / phrases only (surrounded by spaces or text boundaries)
        if (" " + key + " ") in text or text.startswith(key + " ") or text.endswith(" " + key):
            tags.update(key_tags)

    # Category explicitly says "ngoai nuoc" / "quoc te"
    if any((" " + t + " ") in text for t in ["ngoai nuoc", "quoc te", "international", "abroad"]):
        tags.add("international")

    # Domestic tag only when no international flag was detected
    if "international" not in tags:
        tags.add("domestic")

    # Soft tags
    if any((" " + t + " ") in text for t in ["gia dinh", "family", "tre em", "kids"]):
        tags.add("family")
    if any((" " + t + " ") in text for t in ["nghi duong", "resort", "thu gian", "relax"]):
        tags.add("relax")

    return sorted(tags)


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def _normalize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        doc: Dict[str, Any] = {
            "tour_id": int(row["tour_id"]),
            "title": row.get("title") or "Tour",
            "location": row.get("location") or "",
            "description": row.get("description") or "",
            "category_name": row.get("category_name") or "General",
            "price": float(row.get("price") or 0.0),
            "start_date": row.get("start_date").isoformat() if row.get("start_date") else None,
            "end_date": row.get("end_date").isoformat() if row.get("end_date") else None,
            "rating": float(row.get("rating") or 0.0),
            "review_snippets": row.get("review_snippets") or "",
        }
        doc["tags"] = detect_tags(doc)
        normalized.append(doc)
    return normalized


def _fetch_tour_documents() -> List[Dict[str, Any]]:
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
                    c.CategoryName AS category_name,
                    COALESCE(AVG(cm.Rating), 0) AS rating,
                    COALESCE(GROUP_CONCAT(DISTINCT LEFT(cm.Content, 120) SEPARATOR ' | '), '') AS review_snippets
                FROM tour t
                LEFT JOIN category c ON t.CategoryID = c.CategoryID
                LEFT JOIN comment cm ON cm.TourID = t.TourID
                WHERE (t.StartDate IS NULL OR DATE(t.StartDate) >= CURDATE())
                  AND (t.Status IS NULL OR t.Status = 'Available')
                GROUP BY t.TourID, t.Title, t.Location, t.Description, t.Price,
                         t.StartDate, t.EndDate, c.CategoryName
                ORDER BY t.StartDate ASC, t.TourID DESC
                """
            )
            return _normalize_rows(list(cur.fetchall() or []))
    finally:
        conn.close()


def refresh_knowledge_base(force: bool = False) -> Dict[str, Any]:
    cache_age = time.time() - float(_RAG_CACHE.get("built_at") or 0.0)
    if not force and _RAG_CACHE.get("documents") and cache_age < _CACHE_TTL_SECONDS:
        return {
            "message": "Knowledge base is already warm",
            "documents": len(_RAG_CACHE.get("documents") or []),
            "retriever": "faiss" if _RAG_CACHE.get("index") is not None else "tfidf-cosine",
        }

    documents = _fetch_tour_documents()
    corpus = [
        " ".join(
            [
                doc.get("title") or "",
                doc.get("location") or "",
                doc.get("category_name") or "",
                doc.get("description") or "",
                doc.get("review_snippets") or "",
            ]
        ).strip()
        for doc in documents
    ]

    if corpus:
        vectorizer = TfidfVectorizer(max_features=2048, ngram_range=(1, 2))
        dense_vectors = vectorizer.fit_transform(corpus).toarray().astype("float32")
        norms = np.linalg.norm(dense_vectors, axis=1, keepdims=True)
        dense_vectors = dense_vectors / np.clip(norms, 1e-12, None)
    else:
        vectorizer = None
        dense_vectors = np.zeros((0, 0), dtype="float32")

    index = None
    if faiss is not None and dense_vectors.size:
        index = faiss.IndexFlatIP(dense_vectors.shape[1])
        index.add(dense_vectors)

    _RAG_CACHE.update(
        {
            "built_at": time.time(),
            "documents": documents,
            "vectorizer": vectorizer,
            "vectors": dense_vectors,
            "index": index,
        }
    )

    return {
        "message": "Knowledge base refreshed successfully",
        "documents": len(documents),
        "retriever": "faiss" if index is not None else "tfidf-cosine",
    }


def _extract_preferences(prompt: str) -> Dict[str, bool]:
    text = _normalize_text(prompt)
    return {
        "beach": any(term in text for term in _BEACH_TERMS),
        "mountain": any(term in text for term in _MOUNTAIN_TERMS),
        "family": any(term in text for term in _FAMILY_TERMS),
        "relax": any(term in text for term in _RELAX_TERMS),
        "hot_weather": any(term in text for term in _HOT_WEATHER_TERMS),
        "international": any(term in text for term in _INTERNATIONAL_TERMS),
        "budget": any(term in text for term in _BUDGET_TERMS),
        "premium": any(term in text for term in _PREMIUM_TERMS),
    }


def _document_text(item: Dict[str, Any]) -> str:
    return _normalize_text(
        " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("location") or ""),
                str(item.get("category_name") or ""),
                str(item.get("description") or ""),
                str(item.get("review_snippets") or ""),
            ]
        )
    )


def _matches_preferences(item: Dict[str, Any], preferences: Dict[str, bool]) -> bool:
    """Hard-filter using pre-computed tags, not raw text keyword matching."""
    tags = set(item.get("tags") or [])

    # International intent: must have international tag
    if preferences.get("international"):
        return "international" in tags

    # Any domestic-specific intent → exclude international tours
    domestic_intent = preferences.get("beach") or preferences.get("mountain") or preferences.get("hot_weather")
    if domestic_intent and "international" in tags:
        return False

    # Hard filters: must have matching tag
    if preferences.get("beach") and "beach" not in tags:
        return False
    if preferences.get("mountain") and "mountain" not in tags:
        return False
    if preferences.get("hot_weather") and not ({"beach", "mountain", "relax"} & tags):
        return False

    # Soft filters: family and relax don't exclude if tag missing (just lower score)
    return True


def _rank_items(items: List[Dict[str, Any]], preferences: Dict[str, bool], top_k: int) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    for item in items:
        score = float(item.get("score") or 0.0)
        text = _document_text(item)

        if preferences.get("beach") and any(term in text for term in _BEACH_TERMS):
            score += 0.45
        if preferences.get("mountain") and any(term in text for term in _MOUNTAIN_TERMS):
            score += 0.45
        if preferences.get("family") and any(term in text for term in _FAMILY_TERMS):
            score += 0.25
        if preferences.get("relax") and any(term in text for term in _RELAX_TERMS):
            score += 0.25
        if preferences.get("hot_weather"):
            if any(term in text for term in _BEACH_TERMS):
                score += 0.35
            if any(term in text for term in _MOUNTAIN_TERMS):
                score += 0.35
            if any(term in text for term in _RELAX_TERMS):
                score += 0.2
            if not preferences.get("international") and any(term in text for term in _INTERNATIONAL_TERMS):
                score -= 0.35
        if preferences.get("international") and any(term in text for term in _INTERNATIONAL_TERMS):
            score += 0.6
        if preferences.get("budget") or preferences.get("hot_weather"):
            price = float(item.get("price") or 0.0)
            if price > 0:
                score += max(0.0, 0.35 - min(price / 10000000.0, 0.35))

        enriched = dict(item)
        enriched["score"] = round(score, 4)
        ranked.append(enriched)

    if preferences.get("budget"):
        # Price ASC: cheapest first
        ranked.sort(key=lambda x: (float(x.get("price") or float("inf")), -float(x.get("score") or 0.0)))
    elif preferences.get("premium"):
        # Price DESC: most expensive (premium) first
        ranked.sort(key=lambda x: (-(float(x.get("price") or 0.0)), -float(x.get("score") or 0.0)))
    else:
        ranked.sort(key=lambda x: (-float(x.get("score") or 0.0), -float(x.get("rating") or 0.0)))

    return ranked[:top_k]


def _build_query(prompt: str, profile: Dict[str, Any]) -> str:
    segment = str(profile.get("segment_name") or "Khách mới")
    favorite_category = str(profile.get("favorite_category") or "General")
    preferences = _extract_preferences(prompt)

    segment_hints = {
        "Khách mua nhiều": "premium luxury highly rated comfortable exclusive",
        "Khách săn sale": "budget good value affordable promotion deal discount",
        "Khách ít tương tác": "easy popular short relaxing beginner friendly",
        "Khách mới": "best seller beginner friendly highly rated safe",
        "Khách trung thành": "recommended returning traveler favorite experiences",
    }

    weather_hint = "cool weather beach mountain summer escape" if preferences.get("hot_weather") else ""
    hint = " ".join(part for part in [segment_hints.get(segment, "personalized travel experience"), weather_hint] if part)
    return f"{prompt}. Segment: {segment}. Preferred category: {favorite_category}. {hint}".strip()


def _retrieve(query: str, prompt: str, top_k: int = 5) -> List[Dict[str, Any]]:
    refresh_knowledge_base(force=False)
    documents = _RAG_CACHE.get("documents") or []
    vectorizer = _RAG_CACHE.get("vectorizer")
    if not documents or vectorizer is None:
        return []

    query_vector = vectorizer.transform([query]).toarray().astype("float32")
    if not query_vector.size:
        return documents[:top_k]

    query_norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
    query_vector = query_vector / np.clip(query_norm, 1e-12, None)

    search_k = min(max(top_k * 6, 12), len(documents))

    indices: List[int] = []
    scores: List[float] = []
    index = _RAG_CACHE.get("index")
    if faiss is not None and index is not None:
        score_matrix, idx_matrix = index.search(query_vector, search_k)
        indices = [int(i) for i in idx_matrix[0] if int(i) >= 0]
        scores = [float(s) for s in score_matrix[0][: len(indices)]]
    else:
        vectors = _RAG_CACHE.get("vectors")
        similarity = (vectors @ query_vector.T).reshape(-1)
        ranked = np.argsort(similarity)[::-1][:search_k]
        indices = [int(i) for i in ranked]
        scores = [float(similarity[i]) for i in ranked]

    results: List[Dict[str, Any]] = []
    for idx, score in zip(indices, scores):
        item = dict(documents[idx])
        item["score"] = round(score, 4)
        results.append(item)

    preferences = _extract_preferences(prompt)
    filtered = [item for item in results if _matches_preferences(item, preferences)]

    # Hard-intent: return empty so fallback gives honest "no match" message
    hard_intent = (
        preferences.get("international")
        or preferences.get("beach")
        or preferences.get("mountain")
        or preferences.get("hot_weather")
    )
    if hard_intent and not filtered:
        return []

    candidate_items = filtered if filtered else results
    return _rank_items(candidate_items, preferences, top_k)


def _fallback_generation(prompt: str, profile: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    preferences = _extract_preferences(prompt)
    if not items:
        if preferences.get("international"):
            return "Hiện chưa có tour nước ngoài phù hợp trong hệ thống. Bạn có thể để lại nhu cầu để nhân viên tư vấn thêm ngay."
        if preferences.get("beach"):
            return "Hiện chưa có tour biển phù hợp đúng nhu cầu của bạn. Bạn có thể thử thêm mức giá hoặc ngày đi mong muốn."
        if preferences.get("hot_weather"):
            return "Nếu trời đang nóng, bạn có thể thử hỏi tour biển hoặc tour nghỉ dưỡng mát mẻ để mình gợi ý sát hơn."
        return "Hiện chưa có tour phù hợp để gợi ý. Hãy thử thay đổi nhu cầu hoặc làm mới dữ liệu gợi ý."

    if preferences.get("hot_weather"):
        lines = ["Nếu trời đang nóng, bạn có thể ưu tiên các tour biển hoặc điểm đến mát mẻ sau:"]
    elif preferences.get("international"):
        lines = ["Nếu bạn muốn đi nước ngoài, đây là vài gợi ý phù hợp:"]
    else:
        segment = profile.get("segment_name") or "Khách mới"
        lines = [f"Gợi ý phù hợp cho bạn ({segment}):"]

    for item in items[:3]:
        price_text = f"{item.get('price', 0):,.0f} VND" if item.get("price") else "Liên hệ"
        lines.append(
            f"- {item.get('title')} tại {item.get('location')}: giá {price_text}, hạng mục {item.get('category_name')}, điểm đánh giá {item.get('rating', 0):.1f}."
        )
    lines.append(f"Truy vấn gốc: {prompt}")
    return "\n".join(lines)


def _llm_generate(prompt: str, profile: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_generation(prompt, profile, items)

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    context = "\n".join(
        [
            f"Tour: {item.get('title')} | Location: {item.get('location')} | Category: {item.get('category_name')} | Price: {item.get('price')} | Rating: {item.get('rating')} | Description: {item.get('description')}"
            for item in items[:5]
        ]
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a travel recommendation assistant. Use the retrieved context and the customer segment to produce concise personalized suggestions.",
            },
            {
                "role": "user",
                "content": f"Customer profile: {profile}\nUser request: {prompt}\nRetrieved tours:\n{context}",
            },
        ],
        "temperature": 0.4,
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return _fallback_generation(prompt, profile, items)


def recommend_for_user(user_id: int, prompt: str = "recommend a tour", top_k: int = 5) -> Dict[str, Any]:
    profile = get_user_segment(user_id)
    effective_query = _build_query(prompt, profile)
    items = _retrieve(effective_query, prompt=prompt, top_k=top_k)
    answer = _llm_generate(prompt, profile, items)

    return {
        "user_id": user_id,
        "segment": profile,
        "retriever_query": effective_query,
        "recommendations": items,
        "answer": answer,
        "retriever": "faiss" if _RAG_CACHE.get("index") is not None else "tfidf-cosine",
    }
