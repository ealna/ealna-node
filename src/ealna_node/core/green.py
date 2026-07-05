"""The Watt (node side) — pull live energy + carbon from the solar connector."""
from __future__ import annotations

import httpx


def carbon_score(gco2_per_kwh: float) -> int:
    """0..100, 100 = zero-carbon. ponytail: linear vs a 500 gCO2/kWh dirty baseline."""
    return int(max(0.0, min(100.0, 100.0 * (1 - gco2_per_kwh / 500.0))))


class CarbonClient:
    """Reads the solar connector; degrades honestly to a grid average if unreachable."""

    def __init__(self, solar_url: str = "") -> None:
        self.solar_url = solar_url

    def reading(self, energy_kwh: float) -> dict:
        if self.solar_url:
            try:
                r = httpx.get(self.solar_url, timeout=2.0)
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
