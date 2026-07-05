"""Private vector store / RAG endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.vectors import VectorStore
from ..models import QueryRequest, UpsertRequest
from . import deps

router = APIRouter(prefix="/v1/vectors", tags=["rag"])


@router.post("/upsert")
def upsert(req: UpsertRequest,
           store: VectorStore = Depends(deps.get_store),
           stats: dict = Depends(deps.get_stats)) -> dict:
    for it in req.items:
        store.upsert(it.id, it.text, it.metadata)
    stats["vectors"] += len(req.items)
    return {"upserted": len(req.items), "total": len(store)}


@router.post("/query")
def query(req: QueryRequest, store: VectorStore = Depends(deps.get_store)) -> dict:
    return {"matches": store.query(req.query, req.k or 5)}


@router.delete("/{doc_id}")
def delete(doc_id: str, store: VectorStore = Depends(deps.get_store)) -> dict:
    return {"deleted": store.delete(doc_id), "total": len(store)}
