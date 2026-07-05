"""Application factory — wires config, services, and routers into a FastAPI app."""
from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from . import __version__
from .api import (
    certificates as certificates_api,
    chat as chat_api,
    completions as completions_api,
    embeddings as embeddings_api,
    meta as meta_api,
    metrics as metrics_api,
    vectors as vectors_api,
)
from .config import Settings, get_settings
from .core import backends
from .core.certificates import CertificateService
from .core.green import CarbonClient
from .core.ledger import Ledger
from .core.ratelimit import TokenBucket
from .core.vectors import VectorStore

ROUTERS = (meta_api, chat_api, completions_api, embeddings_api,
           vectors_api, certificates_api, metrics_api)


def _register_with_gateway(settings: Settings, carbon: CarbonClient) -> None:
    if not settings.gateway_url:
        return
    try:
        c = carbon.reading(0.0)
        httpx.post(settings.gateway_url.rstrip("/") + "/nodes/register", timeout=2.0, json={
            "node_id": settings.node_id, "url": settings.node_url,
            "energy_source": c["energy_source"], "grid_gco2_per_kwh": c["grid_gco2_per_kwh"],
            "price_per_1k": backends.economics(settings.default_model)["price_per_1k"],
            "models": list(backends.MODELS),
        })
    except Exception:
        pass  # gateway offline is not fatal for a standalone node


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _register_with_gateway(settings, app.state.carbon)   # announce on startup
        yield

    app = FastAPI(title="Ealna Node", version=__version__, lifespan=lifespan)

    # Shared services live on app.state and are injected via api.deps.
    app.state.settings = settings
    app.state.ledger = Ledger(settings.ledger_path)
    app.state.store = VectorStore(settings.embed_dim)
    app.state.bucket = TokenBucket(settings.rate_qps, settings.rate_burst)
    app.state.carbon = CarbonClient(settings.solar_url)
    app.state.certs = CertificateService(app.state.ledger, app.state.carbon, settings)
    app.state.stats = {"chat": 0, "completions": 0, "embeddings": 0, "vectors": 0, "refused": 0}

    for module in ROUTERS:
        app.include_router(module.router)

    return app


app = create_app()
