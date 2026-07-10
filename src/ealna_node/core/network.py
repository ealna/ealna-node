"""Network client — announces this node to the Ealna orchestrator and heartbeats.

The node authenticates with EALNA_NODE_KEY (the credential you get when you
register the node in the dApp). It dials OUT to the orchestrator, so no public IP
or open ports are needed — the node initiates the connection.

ponytail: this is the announce + heartbeat handshake. The job-dispatch pull loop
is Phase 1 — the orchestrator that pushes real user jobs isn't live yet, so
`announce`/`heartbeat` degrade to a no-op unless EALNA_ORCHESTRATOR_URL is set.
"""
from __future__ import annotations

import json
import urllib.request

from ..config import Settings


def build_announce(s: Settings) -> dict:
    """The payload a node advertises to the orchestrator on connect."""
    return {
        "node_id": s.node_id,
        "url": s.node_url,
        "models": [s.default_model],
        "tee_mode": s.tee_mode,
        "clean_sources": sorted(s.clean_sources),
    }


def _post(url: str, key: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310 (trusted orchestrator URL)
        return json.loads(r.read() or b"{}")


def announce(s: Settings) -> dict:
    """Register this node with the orchestrator using its node key."""
    if not s.node_key or not s.orchestrator_url:
        return {"connected": False, "reason": "set EALNA_NODE_KEY and EALNA_ORCHESTRATOR_URL"}
    try:
        return {"connected": True, **_post(s.orchestrator_url.rstrip("/") + "/announce", s.node_key, build_announce(s))}
    except Exception as e:  # noqa: BLE001 — surface a reason, never crash the node
        return {"connected": False, "reason": str(e)}


def heartbeat(s: Settings) -> dict:
    """Keep the node marked live. ponytail: call on a timer once dispatch lands."""
    if not s.node_key or not s.orchestrator_url:
        return {"ok": False}
    try:
        return {"ok": True, **_post(s.orchestrator_url.rstrip("/") + "/heartbeat", s.node_key, {"node_id": s.node_id})}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": str(e)}


if __name__ == "__main__":
    # Self-check: the announce payload is well-formed and carries what the
    # orchestrator needs to route to this node.
    from ..config import get_settings

    a = build_announce(get_settings())
    assert a["node_id"] and a["models"] and a["tee_mode"], a
    assert "solar" in a["clean_sources"], a
    # No key/url configured in a bare env → announce is a safe no-op, not a crash.
    off = announce(get_settings())
    assert off["connected"] is False, off
    print("network self-check ok:", a["node_id"], a["models"])
