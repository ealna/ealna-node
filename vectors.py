"""Private vector store + RAG — real lexical embeddings and cosine search.

`embed` is a char-trigram feature-hashing vectorizer (the standard "hashing
trick" with signed buckets), so overlapping words *and* subwords ("sun" in
"sunlight") pull texts together — retrieval genuinely works with no model.
ponytail: lexical, not neural. Swap `embed` for a real embedding model; keep the
L2 normalization and EMBED_DIM stable so stored vectors remain comparable.
"""
from __future__ import annotations

import hashlib
import math

import config


def _trigrams(text: str) -> list[str]:
    s = "  " + " ".join(text.lower().split()) + "  "
    return [s[i:i + 3] for i in range(len(s) - 2)] or [s]


def embed(text: str) -> list[float]:
    """Deterministic, L2-normalized char-trigram feature-hash of `text`."""
    vec = [0.0] * config.EMBED_DIM
    for g in _trigrams(text):
        h = int.from_bytes(hashlib.md5(g.encode()).digest()[:4], "big")
        vec[h % config.EMBED_DIM] += 1.0 if (h >> 31) & 1 else -1.0   # signed hashing
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Inputs are unit vectors, so this is just the dot product."""
    return sum(x * y for x, y in zip(a, b))


class VectorStore:
    """In-memory vector store. ponytail: swap for a real ANN index (FAISS/pgvector)."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[list[float], dict, str | None]] = {}

    def upsert(self, id: str, text: str, meta: dict | None = None) -> list[float]:
        v = embed(text)
        self._items[id] = (v, meta or {}, text)
        return v

    def upsert_vector(self, id: str, vec: list[float], meta: dict | None = None) -> None:
        self._items[id] = (vec, meta or {}, None)

    def delete(self, id: str) -> bool:
        return self._items.pop(id, None) is not None

    def query(self, text: str, k: int = 5) -> list[dict]:
        q = embed(text)
        scored = [(id, round(cosine(q, v), 6), meta, txt)
                  for id, (v, meta, txt) in self._items.items()]
        scored.sort(key=lambda t: t[1], reverse=True)
        return [{"id": id, "score": s, "metadata": meta, "text": txt}
                for id, s, meta, txt in scored[:k]]

    def __len__(self) -> int:
        return len(self._items)
