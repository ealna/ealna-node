"""Guardrails — a configurable blocklist that refuses unsafe prompts.

ponytail: substring blocklist. Swap for a real safety classifier / moderation
model; keep the (allowed, term) return shape.
"""
from __future__ import annotations

from collections.abc import Iterable


def check(text: str, blocklist: Iterable[str]) -> tuple[bool, str | None]:
    """Return (allowed, first blocked term)."""
    low = text.lower()
    hit = next((w for w in blocklist if w in low), None)
    return (hit is None, hit)
