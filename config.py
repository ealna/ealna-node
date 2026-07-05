"""Ealna Node configuration — all env-driven, with sane defaults."""
from __future__ import annotations

import os
import uuid

NODE_ID = os.getenv("EALNA_NODE_ID", "node-" + uuid.uuid4().hex[:6])
NODE_URL = os.getenv("EALNA_NODE_URL", "http://localhost:8000")
SOLAR_URL = os.getenv("EALNA_SOLAR_URL", "")        # e.g. http://localhost:8100/energy
GATEWAY_URL = os.getenv("EALNA_GATEWAY_URL", "")    # optional self-registration
DEFAULT_MODEL = os.getenv("EALNA_MODEL", "open-llm-8b")
SIGNING_KEY = os.getenv("EALNA_SIGNING_KEY", NODE_ID).encode()  # ponytail: HMAC demo key
TEE_MODE = os.getenv("EALNA_TEE_MODE", "TEE")       # TEE | FHE | MPC
EMBED_DIM = int(os.getenv("EALNA_EMBED_DIM", "64"))
LEDGER_PATH = os.getenv("EALNA_LEDGER_PATH", "")    # empty = in-memory only
RATE_QPS = float(os.getenv("EALNA_RATE_QPS", "50"))
RATE_BURST = int(os.getenv("EALNA_RATE_BURST", "100"))
BLOCKLIST = [w.strip().lower() for w in os.getenv("EALNA_BLOCKLIST", "forbidden,malware").split(",") if w.strip()]

# Sources considered zero-/low-carbon for "clean %" accounting.
CLEAN_SOURCES = {"solar", "battery", "wind", "hydro"}
