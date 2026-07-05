"""Metrics — aggregate the ledger + vector store into JSON and Prometheus text."""
from __future__ import annotations

from ..config import Settings
from .ledger import Ledger
from .vectors import VectorStore


def snapshot(ledger: Ledger, store: VectorStore, stats: dict,
             settings: Settings, uptime_s: float) -> dict:
    certs = ledger.all()
    clean = [c for c in certs if c["carbon"]["energy_source"] in settings.clean_sources]
    return {
        "node_id": settings.node_id,
        "jobs": len(certs),
        "energy_kwh": round(sum(c["carbon"]["energy_kwh"] for c in certs), 6),
        "co2_g": round(sum(c["carbon"]["est_gco2"] for c in certs), 6),
        "clean_pct": round(100 * len(clean) / len(certs), 1) if certs else 0.0,
        "vectors": len(store),
        "uptime_s": round(uptime_s, 1),
        **stats,
    }


def prometheus(m: dict, node_id: str) -> str:
    lines = [
        f'ealna_node_jobs_total{{node="{node_id}"}} {m["jobs"]}',
        f'ealna_node_energy_kwh{{node="{node_id}"}} {m["energy_kwh"]}',
        f'ealna_node_co2_grams{{node="{node_id}"}} {m["co2_g"]}',
        f'ealna_node_clean_pct{{node="{node_id}"}} {m["clean_pct"]}',
        f'ealna_node_refused_total{{node="{node_id}"}} {m.get("refused", 0)}',
        f'ealna_node_vectors{{node="{node_id}"}} {m["vectors"]}',
    ]
    return "\n".join(lines) + "\n"
