from __future__ import annotations

import re
from typing import List


def _split_sentences(text: str) -> List[str]:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return []
    sentences = re.split(r"(?<=[\.!?;:])\s+|\s+\|\s+", normalized)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def build_semantic_chunks(text: str, max_words: int = 90, overlap_sentences: int = 1) -> List[str]:
    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_words = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if current and current_words + word_count > max_words:
            chunks.append(" ".join(current).strip())
            carry = current[-overlap_sentences:] if overlap_sentences > 0 else []
            current = list(carry)
            current_words = sum(len(item.split()) for item in current)

        current.append(sentence)
        current_words += word_count

    if current:
        chunks.append(" ".join(current).strip())

    return [chunk for chunk in chunks if chunk]