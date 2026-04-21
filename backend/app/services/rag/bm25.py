from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Tuple


class BM25Index:
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.tokenized_docs = [doc.split() for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.tokenized_docs]
        self.avg_doc_length = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.term_frequencies = [Counter(tokens) for tokens in self.tokenized_docs]
        self.document_frequencies: Dict[str, int] = {}
        for tokens in self.tokenized_docs:
            for token in set(tokens):
                self.document_frequencies[token] = self.document_frequencies.get(token, 0) + 1

    def score(self, query: str) -> List[float]:
        query_terms = query.split()
        total_docs = max(len(self.documents), 1)
        scores = [0.0] * len(self.documents)
        for term in query_terms:
            doc_freq = self.document_frequencies.get(term, 0)
            if doc_freq == 0:
                continue
            idf = math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
            for index, frequencies in enumerate(self.term_frequencies):
                term_freq = frequencies.get(term, 0)
                if term_freq == 0:
                    continue
                doc_length = self.doc_lengths[index]
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (1 - self.b + self.b * (doc_length / max(self.avg_doc_length, 1e-9)))
                scores[index] += idf * numerator / max(denominator, 1e-9)
        return scores

    def search(self, query: str, top_n: int) -> List[Tuple[int, float]]:
        scores = self.score(query)
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        return [(index, score) for index, score in ranked[:top_n] if score > 0]