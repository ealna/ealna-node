"""Smart model router — pick the cheapest/greenest model meeting a target."""
from __future__ import annotations

from .backends import MODELS


def choose_model(kind: str = "chat", target: str = "cheapest", tier: str | None = None) -> str | None:
    """Return the best model id for a (kind, target, optional tier), or None."""
    cands = [m for m, meta in MODELS.items()
             if meta["kind"] == kind and (tier is None or meta["tier"] == tier)]
    if not cands:
        return None
    keys = {
        "cheapest": lambda m: MODELS[m]["price_per_1k"],
        "greenest": lambda m: MODELS[m]["kwh_per_1k"],
        "quality":  lambda m: (MODELS[m]["tier"] != "quality", MODELS[m]["kwh_per_1k"]),
    }
    return sorted(cands, key=keys.get(target, keys["cheapest"]))[0]
