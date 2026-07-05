# ealna-node

An Ealna worker node: runs AI **behind the Veil** and returns an OpenAI-compatible
response **plus a signed Green Compute Certificate** on every call.

## Features

- **Chat** (`/v1/chat/completions`) with optional **SSE streaming** (`"stream": true`)
- **Legacy completions** (`/v1/completions`) and **embeddings** (`/v1/embeddings`)
- **Private vector store + RAG** — real char-trigram embeddings + cosine search
- **Guardrails** — configurable blocklist refuses unsafe prompts (`EALNA_BLOCKLIST`)
- **Smart model router** (`/route`) — cheapest / greenest / by-quality-tier
- **Rate limiting** — token bucket (`EALNA_RATE_QPS`, `EALNA_RATE_BURST`)
- **Signed certificates** (HMAC) + **on-disk ledger** (`EALNA_LEDGER_PATH`) + `/verify`
- **Metrics** as JSON (`/metrics`) and Prometheus text (`/metrics/prom`)

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app:app --port 8000

curl localhost:8000/v1/chat/completions -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"hi"}]}'
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/chat/completions` | chat (+ `stream`, guardrails) + certificate |
| `POST` | `/v1/completions` | legacy text completion |
| `POST` | `/v1/embeddings` | normalized embeddings + certificate |
| `POST` | `/v1/vectors/upsert` · `/v1/vectors/query` | private RAG store + search |
| `DELETE` | `/v1/vectors/{id}` | delete a vector |
| `GET`  | `/v1/models` · `/route` | catalog / model router preview |
| `GET`  | `/certificates[/{serial}]` | explorer feed / lookup |
| `POST` | `/verify` | verify a certificate signature |
| `GET`  | `/metrics` · `/metrics/prom` | JSON / Prometheus metrics |

## Package layout

```
app.py        FastAPI wiring + certificate minting     ledger.py     serial + JSONL persistence
config.py     env config                               ratelimit.py  token bucket
veil.py       attestation + HMAC sign/verify           backends.py   models, guardrails, inference
green.py      carbon reading from the solar connector  router.py     smart model router
vectors.py    embeddings + vector store (RAG)
```

## Config (env)

`EALNA_NODE_ID`, `EALNA_MODEL`, `EALNA_TEE_MODE`, `EALNA_SIGNING_KEY`, `EALNA_EMBED_DIM`,
`EALNA_LEDGER_PATH`, `EALNA_RATE_QPS`, `EALNA_RATE_BURST`, `EALNA_BLOCKLIST`,
`EALNA_SOLAR_URL`, `EALNA_GATEWAY_URL`, `EALNA_NODE_URL`.

## What's stubbed (marked `ponytail:`)

Inference (deterministic per-tier text), embeddings (lexical, not neural), TEE attestation
(SHA-256 commit), signature (HMAC → swap for ed25519). Swap each for the real thing; shapes stay stable.

## Test

```bash
python test_node.py   # or: pytest
```

---
[ealna.com](https://ealna.com) · [Docs](https://ealna.com/docs) · [dApp](https://ealna.com/dapp) · [GitHub](https://github.com/ealna)
