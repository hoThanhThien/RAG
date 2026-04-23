"""
knowledge_base.py
-----------------
Loads Vietnam tourism knowledge from the two provided SQuAD-format JSON files:
  - archive/train_vietnam_tourism.json
  - archive/valid_vietnam_tourism.json

Each JSON has the structure:
  {"data": [{"title": "...", "paragraphs": [{"context": "...", "qas": [...]}]}]}

The context passages are extracted and split into overlapping text chunks.
These chunks are added to the main RAG index alongside tour data, providing
the LLM with rich background knowledge about Vietnam destinations, culture,
food, and travel tips — improving answer quality for general travel questions.

WHY THIS HELPS RETRIEVAL:
- Tour database chunks describe *specific tours* (price, dates, location).
- Knowledge chunks describe *destinations* in depth (what to see, culture,
  food, activities). This bridges the vocabulary gap between user queries like
  "có gì hay ở Hội An?" and tour records that only mention "Hội An" as a field.
- BM25 benefits most: knowledge chunks contain the exact Vietnamese terms users
  type, so lexical search recall improves significantly.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Try likely archive locations in order of preference.
# Current repo layout keeps the SQuAD files in backend/archive/.
_ARCHIVE_DIR_CANDIDATES = [
    Path(__file__).resolve().parents[3] / "archive",
    Path(__file__).resolve().parents[4] / "archive",
]


def _resolve_kb_files() -> List[Path]:
    for archive_dir in _ARCHIVE_DIR_CANDIDATES:
        valid_file = archive_dir / "valid_vietnam_tourism.json"
        train_file = archive_dir / "train_vietnam_tourism.json"
        if valid_file.exists() or train_file.exists():
            return [valid_file, train_file]
    # Fall back to the first candidate so warning logs still show a stable path.
    archive_dir = _ARCHIVE_DIR_CANDIDATES[0]
    return [
        archive_dir / "valid_vietnam_tourism.json",
        archive_dir / "train_vietnam_tourism.json",
    ]


_KB_FILES = _resolve_kb_files()

_CHUNK_SIZE_WORDS = 80   # words per knowledge chunk
_OVERLAP_WORDS = 15      # overlap between consecutive chunks (sliding window)


def _sliding_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping word-window chunks."""
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_size:
        return [text]
    step = max(chunk_size - overlap, 1)
    result: List[str] = []
    for start in range(0, len(words), step):
        piece = " ".join(words[start : start + chunk_size])
        if piece:
            result.append(piece)
        if start + chunk_size >= len(words):
            break
    return result


def _load_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        logger.warning("Knowledge base file not found: %s", path)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("data") or []
        chunks: List[Dict[str, Any]] = []
        for item in items:
            title = str(item.get("title") or "").strip()
            for paragraph in item.get("paragraphs") or []:
                context = str(paragraph.get("context") or "").strip()
                if len(context) < 40:
                    continue
                for piece in _sliding_chunks(context, _CHUNK_SIZE_WORDS, _OVERLAP_WORDS):
                    chunks.append(
                        {
                            "tour_id": 0,            # knowledge chunk sentinel
                            "title": title,
                            "location": "",
                            "category_name": "Kiến thức du lịch Việt Nam",
                            "price": 0.0,
                            "chunk_type": "knowledge",
                            "source_file": path.stem,
                            "text": f"{title}: {piece}",
                        }
                    )
        logger.info("Loaded %d knowledge chunks from %s", len(chunks), path.name)
        return chunks
    except Exception:
        logger.exception("Failed to load knowledge base from %s", path)
        return []


def load_knowledge_chunks(max_chunks: int = 0) -> List[Dict[str, Any]]:
    """
    Load and return knowledge base chunks from the Vietnam tourism JSON files.

    Parameters
    ----------
    max_chunks : int
        Maximum total chunks to return (0 = no limit).
        Valid set (~2 k chunks) is loaded first; train set supplements if
        more capacity remains.

    Returns
    -------
    List[Dict[str, Any]]
        Chunks compatible with the existing RAG chunk schema.
    """
    all_chunks: List[Dict[str, Any]] = []
    for path in _KB_FILES:
        file_chunks = _load_file(path)
        if max_chunks > 0:
            remaining = max_chunks - len(all_chunks)
            if remaining <= 0:
                break
            all_chunks.extend(file_chunks[:remaining])
        else:
            all_chunks.extend(file_chunks)
    logger.info("Total knowledge chunks loaded: %d", len(all_chunks))
    return all_chunks
