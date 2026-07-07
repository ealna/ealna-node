# ealna-node

An Ealna worker node: runs AI **behind the Veil** and returns an OpenAI-compatible
response **plus a signed Green Compute Certificate** on every call.

## Features

- **Chat** (`/v1/chat/completions`) with guardrails and optional **SSE streaming**
- **Legacy completions** (`/v1/completions`) and **embeddings** (`/v1/embeddings`)
- **Private vector store + RAG** — real char-trigram embeddings + cosine search
- **Smart model router** (`/route`) — cheapest / greenest / by tier
- **Rate limiting** (token bucket), **signed certificates** + on-disk ledger + `/verify`
- **Metrics** as JSON (`/metrics`) and Prometheus (`/metrics/prom`)

## Install & run

```bash
pip install -e ".[dev]"     # editable install with test deps
ealna-node                  # console script -> uvicorn on :8000
# alternatives:
python -m ealna_node
PYTHONPATH=src uvicorn ealna_node.app:app --port 8000   # dev, no install

curl localhost:8000/v1/chat/completions -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"hi"}]}'
```

## The Green Compute Certificate

Every call returns a signed certificate binding a **privacy** proof to a **carbon**
proof — the artifact that makes "private and green" auditable instead of a claim:

```json
{
  "job_id": "ea_9f3a1c7b",
  "node_id": "node-7f3a",
  "model": "open-llm-8b",
  "privacy":    { "mode": "TEE", "attestation": "0x8f14e45f…", "data_exposed": false },
  "carbon":     { "energy_source": "solar", "grid_gco2_per_kwh": 41.0,
                  "energy_kwh": 0.0123, "est_gco2": 0.5043, "carbon_score": 91 },
  "usage":      { "prompt_tokens": 12, "completion_tokens": 48, "total_tokens": 60 },
  "hour": "2026-07-08T14:00Z",
  "serial": "GCC-000128401",
  "status": "verified",
  "settlement": { "rail": "x402", "asset": "EALNA", "price_est": 0.00012 },
  "signature": "0x5e884898…"
}
```

`carbon_score` is `100 * (1 - gCO₂·kWh⁻¹ / 500)`, clamped to 0–100. `status` is
`verified` when the carbon reading is live and `degraded` when the solar connector is
unreachable (source `unknown`). Re-check any certificate's signature with `POST /verify`
— a forged proof won't match the HMAC.

## Layout

```
src/ealna_node/
├── app.py              # create_app() factory + app instance
├── __main__.py         # `python -m ealna_node`
├── config.py           # env -> immutable Settings
├── core/               # domain logic (framework-free, unit-tested)
│   ├── veil.py           attestation + HMAC sign/verify
│   ├── green.py          carbon reading from the solar connector
│   ├── backends.py       model catalog, inference, token counting
│   ├── guardrails.py     blocklist checks
│   ├── router.py         smart model router
│   ├── vectors.py        embeddings + vector store (RAG)
│   ├── ledger.py         serial + JSONL persistence
│   ├── ratelimit.py      token bucket
│   ├── certificates.py   CertificateService (mint + sign + ledger)
│   └── metrics.py        JSON / Prometheus snapshots
├── models/schemas.py   # pydantic request models
└── api/                # one router per surface (chat, embeddings, vectors, …)
tests/                  # pytest: one module per core unit + test_api.py
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/chat/completions` | chat (+ `stream`, guardrails) + certificate |
| `POST` | `/v1/completions` · `/v1/embeddings` | legacy completion / embeddings |
| `POST` | `/v1/vectors/upsert` · `/v1/vectors/query` | private RAG store + search |
| `GET`  | `/v1/models` · `/route` | catalog / model router |
| `GET`  | `/certificates[/{serial}]` · `POST /verify` | explorer / signature check |
| `GET`  | `/metrics` · `/metrics/prom` | JSON / Prometheus metrics |

## Test

```bash
pytest            # 27 tests: core units + API
```

## What's stubbed (marked `ponytail:`)

Inference (deterministic per-tier text), embeddings (lexical, not neural), TEE attestation
(SHA-256 commit), signature (HMAC → swap for ed25519). Swap each for the real thing; shapes stay stable.

---
[ealna.com](https://ealna.com) · [Docs](https://ealna.com/docs) · [dApp](https://ealna.com/dapp) · [GitHub](https://github.com/ealna)
