"""The Watt (node side) — pull live energy + carbon from the solar connector."""
from __future__ import annotations

import httpx

import config


def carbon_score(gco2_per_kwh: float) -> int:
    """0..100, 100 = zero-carbon. ponytail: linear vs a 500 gCO2/kWh dirty baseline."""
    return int(max(0.0, min(100.0, 100.0 * (1 - gco2_per_kwh / 500.0))))


def carbon_reading(energy_kwh: float) -> dict:
    """Live energy source + grid intensity, fetched from the solar connector.

    Falls back to a conservative grid average (flagged 'unknown' so the
    certificate downgrades to 'degraded') when no connector is reachable.
    """
    if config.SOLAR_URL:
        try:
            r = httpx.get(config.SOLAR_URL, timeout=2.0)
            r.raise_for_status()
            d = r.json()
            gco2 = float(d.get("grid_gco2_per_kwh", 475))
            return {
                "energy_source": d.get("energy_source", "grid"),
                "grid_gco2_per_kwh": gco2,
                "energy_kwh": round(energy_kwh, 6),
                "est_gco2": round(gco2 * energy_kwh, 6),
                "carbon_score": carbon_score(gco2),
            }
        except Exception:
            pass  # honest degradation below
    return {
        "energy_source": "unknown",
        "grid_gco2_per_kwh": 475.0,
        "energy_kwh": round(energy_kwh, 6),
        "est_gco2": round(475.0 * energy_kwh, 6),
        "carbon_score": carbon_score(475.0),
    }
