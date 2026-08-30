from __future__ import annotations
import json
import re
from typing import Any

from rank_bm25 import BM25Okapi

_ARCHIVE_PENALTY = 0.5

def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())

class KBRetriever:
    def __init__(self, kb_path: str) -> None:
        self._docs: list[dict[str, Any]] = []
        with open(kb_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._docs.append(json.loads(line))

        corpus = [_tokenize(f"{d['title']} {d['body']}") for d in self._docs]
        self._bm25 = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        tokens = _tokenize(query)
        raw_scores = self._bm25.get_scores(tokens)

        scored = []
        for doc, raw_score in zip(self._docs, raw_scores):
            penalty = _ARCHIVE_PENALTY if "archive" in doc.get("tags", []) else 1.0
            scored.append((raw_score * penalty, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scored[:top_k]:
            results.append({**doc, "score": round(float(score), 4)})
        return results

    def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        return next((d for d in self._docs if d["id"] == doc_id), None)