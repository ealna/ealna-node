"""Model backends, catalog economics, and token counting.

ponytail: the backends are deterministic text transforms so the node runs with no
GPU or model download, yet each model produces a genuinely different, testable
output. Replace `run_chat` with a real backend (vLLM / llama.cpp / transformers),
keeping the MODELS economics and the same signature.
"""
from __future__ import annotations

FALLBACK = "open-llm-8b"

# label -> {kind, energy (kWh/1k tok), price (EALNA/1k tok), tier}
MODELS: dict[str, dict] = {
    "open-llm-8b":   {"kind": "chat",      "kwh_per_1k": 0.0009, "price_per_1k": 0.0006, "tier": "fast"},
    "open-llm-70b":  {"kind": "chat",      "kwh_per_1k": 0.0061, "price_per_1k": 0.0040, "tier": "quality"},
    "ealna-code-1":  {"kind": "chat",      "kwh_per_1k": 0.0018, "price_per_1k": 0.0012, "tier": "code"},
    "ealna-embed-1": {"kind": "embedding", "kwh_per_1k": 0.0002, "price_per_1k": 0.0001, "tier": "fast"},
}


def economics(model: str) -> dict:
    return MODELS.get(model, MODELS[FALLBACK])


def tokens(text: str) -> int:
    """~4 chars/token heuristic. ponytail: swap for a real tokenizer for billing."""
    return max(1, len(text) // 4)


def _reply(model: str, user: str) -> str:
    """Deterministic per-tier 'personality' so models differ observably."""
    tier = economics(model).get("tier")
    if tier == "code":
        return f"```python\n# {model} via Ealna Veil\ndef solve():\n    return {user!r}\n```"
    if tier == "quality":
        return (f"[{model}] Reasoning about your request step by step, then answering: "
                f"{user} — here is a thorough, considered response.")
    return f"[{model} via Ealna Veil] {user}"


def run_chat(model: str, messages: list[dict]) -> str:
    """Produce a chat completion string from OpenAI-style messages."""
    user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    return _reply(model, user)
