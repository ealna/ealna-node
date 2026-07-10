"""Runtime configuration, loaded from the environment into an immutable Settings."""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    node_id: str
    node_url: str
    node_key: str
    orchestrator_url: str
    solar_url: str
    gateway_url: str
    default_model: str
    signing_key: bytes
    tee_mode: str
    embed_dim: int
    ledger_path: str
    rate_qps: float
    rate_burst: int
    blocklist: tuple[str, ...]
    clean_sources: frozenset[str] = frozenset({"solar", "battery", "wind", "hydro"})


def get_settings() -> Settings:
    node_id = os.getenv("EALNA_NODE_ID", "node-" + uuid.uuid4().hex[:6])
    return Settings(
        node_id=node_id,
        node_url=os.getenv("EALNA_NODE_URL", "http://localhost:8000"),
        node_key=os.getenv("EALNA_NODE_KEY", ""),
        orchestrator_url=os.getenv("EALNA_ORCHESTRATOR_URL", ""),
        solar_url=os.getenv("EALNA_SOLAR_URL", ""),
        gateway_url=os.getenv("EALNA_GATEWAY_URL", ""),
        default_model=os.getenv("EALNA_MODEL", "open-llm-8b"),
        signing_key=os.getenv("EALNA_SIGNING_KEY", node_id).encode(),
        tee_mode=os.getenv("EALNA_TEE_MODE", "TEE"),
        embed_dim=int(os.getenv("EALNA_EMBED_DIM", "64")),
        ledger_path=os.getenv("EALNA_LEDGER_PATH", ""),
        rate_qps=float(os.getenv("EALNA_RATE_QPS", "50")),
        rate_burst=int(os.getenv("EALNA_RATE_BURST", "100")),
        blocklist=tuple(w.strip().lower()
                        for w in os.getenv("EALNA_BLOCKLIST", "forbidden,malware").split(",")
                        if w.strip()),
    )
