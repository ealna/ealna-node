"""Embeddings — normalized vectors + a Green Compute Certificate."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..core import backends, vectors
from ..core.certificates import CertificateService
from ..core.ratelimit import TokenBucket
from ..core.vectors import VectorStore
from ..models import EmbeddingRequest
from . import deps

router = APIRouter(tags=["inference"])


@router.post("/v1/embeddings")
def embeddings(req: EmbeddingRequest,
               certs: CertificateService = Depends(deps.get_certs),
               store: VectorStore = Depends(deps.get_store),
               bucket: TokenBucket = Depends(deps.get_bucket),
               stats: dict = Depends(deps.get_stats)):
    if not bucket.allow():
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    model = req.model or "ealna-embed-1"
    inputs = [req.input] if isinstance(req.input, str) else req.input
    data = [{"object": "embedding", "index": i, "embedding": vectors.embed(t, store.dim)}
            for i, t in enumerate(inputs)]
    stats["embeddings"] += len(inputs)
    joined = " ".join(inputs)
    cert = certs.mint(model, joined, backends.tokens(joined), 0)
    return {"object": "list", "model": model, "data": data,
            "usage": cert["usage"], "ealna_certificate": cert}
