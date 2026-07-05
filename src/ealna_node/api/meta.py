"""Meta endpoints — root, health, model catalog, and the model router preview."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings
from ..core import backends, router as model_router
from . import deps

router = APIRouter(tags=["meta"])
_START = time.time()


@router.get("/")
def root(settings: Settings = Depends(deps.get_settings)) -> dict:
    return {"service": "ealna-node", "node_id": settings.node_id,
            "model": settings.default_model, "docs": "https://ealna.com/docs"}


@router.get("/health")
def health(settings: Settings = Depends(deps.get_settings)) -> dict:
    return {"node_id": settings.node_id, "model": settings.default_model,
            "uptime_s": round(time.time() - _START, 1), "ok": True}


@router.get("/v1/models")
def list_models() -> dict:
    return {"object": "list", "data": [
        {"id": m, "object": "model", "owned_by": "ealna", **meta}
        for m, meta in backends.MODELS.items()
    ]}


@router.get("/route")
def route(kind: str = "chat", target: str = "cheapest", tier: str | None = None) -> dict:
    m = model_router.choose_model(kind, target, tier)
    if not m:
        raise HTTPException(status_code=404, detail="no model matches")
    return {"model": m, **backends.MODELS[m]}
