from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class RAGSettings:
    base_dir: Path
    rag_dir: Path
    index_file: Path
    metadata_file: Path
    state_file: Path
    vectorizer_file: Path
    vectors_file: Path
    default_chat_model: str
    default_embedding_model: str
    openai_base_url: str
    openai_timeout_seconds: int
    chunk_size_words: int
    chunk_overlap_sentences: int
    review_chunk_size_words: int
    search_multiplier: int
    lexical_search_multiplier: int
    min_search_k: int
    max_search_k: int
    hybrid_dense_weight: float
    hybrid_lexical_weight: float
    query_cache_ttl_seconds: int
    query_cache_size: int
    response_cache_ttl_seconds: int
    embedding_batch_size: int
    answer_temperature: float
    answer_max_tokens: int
    redis_enabled: bool
    redis_url: str
    redis_key_prefix: str
    redis_timeout_seconds: int


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = str(os.getenv(name, str(default))).strip().lower()
    return value in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_rag_settings() -> RAGSettings:
    base_dir = Path(__file__).resolve().parents[3]
    rag_dir = base_dir / "rag_store"
    return RAGSettings(
        base_dir=base_dir,
        rag_dir=rag_dir,
        index_file=rag_dir / "tour_index.faiss",
        metadata_file=rag_dir / "chunks.json",
        state_file=rag_dir / "state.json",
        vectorizer_file=rag_dir / "tfidf_vectorizer.pkl",
        vectors_file=rag_dir / "vectors.npy",
        default_chat_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        default_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_timeout_seconds=_env_int("RAG_OPENAI_TIMEOUT_SECONDS", 40),
        chunk_size_words=_env_int("RAG_CHUNK_SIZE_WORDS", 90),
        chunk_overlap_sentences=_env_int("RAG_CHUNK_OVERLAP_SENTENCES", 1),
        review_chunk_size_words=_env_int("RAG_REVIEW_CHUNK_SIZE_WORDS", 60),
        search_multiplier=_env_int("RAG_SEARCH_MULTIPLIER", 8),
        lexical_search_multiplier=_env_int("RAG_LEXICAL_SEARCH_MULTIPLIER", 10),
        min_search_k=_env_int("RAG_MIN_SEARCH_K", 12),
        max_search_k=_env_int("RAG_MAX_SEARCH_K", 60),
        hybrid_dense_weight=_env_float("RAG_HYBRID_DENSE_WEIGHT", 0.68),
        hybrid_lexical_weight=_env_float("RAG_HYBRID_LEXICAL_WEIGHT", 0.32),
        query_cache_ttl_seconds=_env_int("RAG_QUERY_CACHE_TTL_SECONDS", 300),
        query_cache_size=_env_int("RAG_QUERY_CACHE_SIZE", 256),
        response_cache_ttl_seconds=_env_int("RAG_RESPONSE_CACHE_TTL_SECONDS", 180),
        embedding_batch_size=_env_int("RAG_EMBEDDING_BATCH_SIZE", 96),
        answer_temperature=_env_float("RAG_ANSWER_TEMPERATURE", 0.15),
        answer_max_tokens=_env_int("RAG_ANSWER_MAX_TOKENS", 320),
        redis_enabled=_env_bool("RAG_REDIS_ENABLED", False),
        redis_url=os.getenv("RAG_REDIS_URL", "redis://localhost:6379/0"),
        redis_key_prefix=os.getenv("RAG_REDIS_KEY_PREFIX", "rag"),
        redis_timeout_seconds=_env_int("RAG_REDIS_TIMEOUT_SECONDS", 2),
    )