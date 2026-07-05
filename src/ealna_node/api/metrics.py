"""Metrics endpoints — JSON and Prometheus text."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from ..config import Settings
from ..core import metrics as metrics_core
from ..core.ledger import Ledger
from ..core.vectors import VectorStore
from . import deps
from .meta import _START

router = APIRouter(tags=["metrics"])


def _snapshot(ledger: Ledger, store: VectorStore, stats: dict, settings: Settings) -> dict:
    return metrics_core.snapshot(ledger, store, stats, settings, time.time() - _START)


@router.get("/metrics")
def metrics(settings: Settings = Depends(deps.get_settings),
            ledger: Ledger = Depends(deps.get_ledger),
            store: VectorStore = Depends(deps.get_store),
            stats: dict = Depends(deps.get_stats)) -> dict:
    return _snapshot(ledger, store, stats, settings)


@router.get("/metrics/prom", response_class=PlainTextResponse)
def metrics_prom(settings: Settings = Depends(deps.get_settings),
                 ledger: Ledger = Depends(deps.get_ledger),
                 store: VectorStore = Depends(deps.get_store),
                 stats: dict = Depends(deps.get_stats)) -> str:
    return metrics_core.prometheus(_snapshot(ledger, store, stats, settings), settings.node_id)
