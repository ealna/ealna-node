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


def certificate_summary(certs: list[dict], clean_sources) -> dict:
    """Aggregate a certificate ledger into counts, energy, carbon, and source mix."""
    if not certs:
        return {"count": 0, "energy_kwh": 0.0, "est_gco2": 0.0,
                "avg_carbon_score": 0.0, "clean_pct": 0.0, "by_source": {}}
    by_source: dict[str, int] = {}
    for c in certs:
        src = c["carbon"]["energy_source"]
        by_source[src] = by_source.get(src, 0) + 1
    clean = sum(n for s, n in by_source.items() if s in clean_sources)
    return {
        "count": len(certs),
        "energy_kwh": round(sum(c["carbon"]["energy_kwh"] for c in certs), 6),
        "est_gco2": round(sum(c["carbon"]["est_gco2"] for c in certs), 6),
        "avg_carbon_score": round(sum(c["carbon"]["carbon_score"] for c in certs) / len(certs), 1),
        "clean_pct": round(100 * clean / len(certs), 1),
        "by_source": by_source,
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
