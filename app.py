"""Ealna Node — OpenAI-compatible AI inference behind the Veil.

Serves chat (+ SSE streaming), legacy completions, embeddings, a private vector
store with RAG search, a smart model-router preview, guardrails, rate limiting,
signed Green Compute Certificates, an on-disk certificate ledger + explorer,
signature verification, and JSON / Prometheus metrics.
"""
from __future__ import annotations

import json
import time
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel

import backends
import config
import green
import router as router_mod
import veil
import vectors as vecmod
from ledger import Ledger
from ratelimit import TokenBucket

START = time.time()
app = FastAPI(title="Ealna Node", version="0.3")

LEDGER = Ledger(config.LEDGER_PATH)
STORE = vecmod.VectorStore()
BUCKET = TokenBucket(config.RATE_QPS, config.RATE_BURST)
_stats = {"chat": 0, "completions": 0, "embeddings": 0, "vectors": 0, "refused": 0}


# =====================================================
# Request models
# =====================================================
class Msg(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Msg]
    max_tokens: int | None = 256
    temperature: float | None = 0.7
    stream: bool | None = False


class CompletionRequest(BaseModel):
    model: str | None = None
    prompt: str
    max_tokens: int | None = 256


class EmbeddingRequest(BaseModel):
    model: str | None = None
    input: str | list[str]


class UpsertItem(BaseModel):
    id: str
    text: str
    metadata: dict | None = None


class UpsertRequest(BaseModel):
    items: list[UpsertItem]


class QueryRequest(BaseModel):
    query: str
    k: int | None = 5


class VerifyRequest(BaseModel):
    certificate: dict


# =====================================================
# Certificate minting
# =====================================================
def make_certificate(model: str, output_text: str, prompt_tokens: int,
                     completion_tokens: int, extra: dict | None = None) -> dict:
    econ = backends.MODELS.get(model, backends.MODELS[config.DEFAULT_MODEL])
    total = prompt_tokens + completion_tokens
    energy_kwh = round(total / 1000 * econ["kwh_per_1k"], 6)
    carbon = green.carbon_reading(energy_kwh)
    cert = {
        "job_id": "ea_" + uuid.uuid4().hex[:8],
        "node_id": config.NODE_ID,
        "model": model,
        "privacy": veil.privacy_attestation(output_text.encode()),
        "carbon": carbon,
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                  "total_tokens": total},
        "hour": time.strftime("%Y-%m-%dT%H:00Z", time.gmtime()),
        "serial": LEDGER.next_serial(),
        "status": "degraded" if carbon["energy_source"] == "unknown" else "verified",
        "settlement": {"rail": "x402", "asset": "EALNA",
                       "price_est": round(total / 1000 * econ["price_per_1k"], 6)},
    }
    if extra:
        cert.update(extra)
    cert["signature"] = veil.sign(cert)
    LEDGER.append(cert)
    return cert


def _rate_guard() -> None:
    if not BUCKET.allow():
        raise HTTPException(status_code=429, detail="rate limit exceeded")


# =====================================================
# Lifecycle
# =====================================================
@app.on_event("startup")
def _register() -> None:
    if not config.GATEWAY_URL:
        return
    try:
        c = green.carbon_reading(0.0)
        httpx.post(config.GATEWAY_URL.rstrip("/") + "/nodes/register", timeout=2.0, json={
            "node_id": config.NODE_ID, "url": config.NODE_URL,
            "energy_source": c["energy_source"], "grid_gco2_per_kwh": c["grid_gco2_per_kwh"],
            "price_per_1k": backends.MODELS[config.DEFAULT_MODEL]["price_per_1k"],
            "models": list(backends.MODELS),
        })
    except Exception:
        pass


# =====================================================
# Meta
# =====================================================
@app.get("/")
def root() -> dict:
    return {"service": "ealna-node", "node_id": config.NODE_ID,
            "model": config.DEFAULT_MODEL, "docs": "https://ealna.com/docs"}


@app.get("/health")
def health() -> dict:
    return {"node_id": config.NODE_ID, "model": config.DEFAULT_MODEL,
            "uptime_s": round(time.time() - START, 1), "ok": True}


@app.get("/v1/models")
def list_models() -> dict:
    return {"object": "list", "data": [
        {"id": m, "object": "model", "owned_by": "ealna", **meta}
        for m, meta in backends.MODELS.items()
    ]}


@app.get("/route")
def route(kind: str = "chat", target: str = "cheapest", tier: str | None = None) -> dict:
    m = router_mod.choose_model(kind, target, tier)
    if not m:
        raise HTTPException(status_code=404, detail="no model matches")
    return {"model": m, **backends.MODELS[m]}


# =====================================================
# Inference
# =====================================================
def _stream_chat(model: str, out: str) -> StreamingResponse:
    def gen():
        for word in out.split(" "):
            chunk = {"object": "chat.completion.chunk", "model": model,
                     "choices": [{"index": 0, "delta": {"content": word + " "}}]}
            yield f"data: {json.dumps(chunk)}\n\n"
        cert = make_certificate(model, out, 1, backends.tokens(out))
        yield f"data: {json.dumps({'ealna_certificate': cert})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    _rate_guard()
    model = req.model or config.DEFAULT_MODEL
    msgs = [m.model_dump() for m in req.messages]
    prompt_text = " ".join(m["content"] for m in msgs)

    allowed, hit = backends.guardrail(prompt_text)
    if not allowed:
        _stats["refused"] += 1
        out = f"[refused] request blocked by guardrail: {hit!r}"
        cert = make_certificate(model, out, backends.tokens(prompt_text), backends.tokens(out),
                                {"guardrail": {"blocked": True, "term": hit}})
        return {"id": cert["job_id"], "object": "chat.completion", "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": out},
                             "finish_reason": "content_filter"}],
                "usage": cert["usage"], "ealna_certificate": cert}

    out = backends.run_chat(model, msgs)
    _stats["chat"] += 1
    if req.stream:
        return _stream_chat(model, out)
    cert = make_certificate(model, out, backends.tokens(prompt_text), backends.tokens(out))
    return {"id": cert["job_id"], "object": "chat.completion", "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": out},
                         "finish_reason": "stop"}],
            "usage": cert["usage"], "ealna_certificate": cert}


@app.post("/v1/completions")
def completions(req: CompletionRequest):
    _rate_guard()
    model = req.model or config.DEFAULT_MODEL
    out = backends.run_chat(model, [{"role": "user", "content": req.prompt}])
    _stats["completions"] += 1
    cert = make_certificate(model, out, backends.tokens(req.prompt), backends.tokens(out))
    return {"id": cert["job_id"], "object": "text_completion", "model": model,
            "choices": [{"index": 0, "text": out, "finish_reason": "stop"}],
            "usage": cert["usage"], "ealna_certificate": cert}


@app.post("/v1/embeddings")
def embeddings(req: EmbeddingRequest):
    _rate_guard()
    model = req.model or "ealna-embed-1"
    inputs = [req.input] if isinstance(req.input, str) else req.input
    data = [{"object": "embedding", "index": i, "embedding": vecmod.embed(t)}
            for i, t in enumerate(inputs)]
    _stats["embeddings"] += len(inputs)
    joined = " ".join(inputs)
    cert = make_certificate(model, joined, backends.tokens(joined), 0)
    return {"object": "list", "model": model, "data": data,
            "usage": cert["usage"], "ealna_certificate": cert}


# =====================================================
# Private vector store / RAG
# =====================================================
@app.post("/v1/vectors/upsert")
def vectors_upsert(req: UpsertRequest) -> dict:
    for it in req.items:
        STORE.upsert(it.id, it.text, it.metadata)
    _stats["vectors"] += len(req.items)
    return {"upserted": len(req.items), "total": len(STORE)}


@app.post("/v1/vectors/query")
def vectors_query(req: QueryRequest) -> dict:
    return {"matches": STORE.query(req.query, req.k or 5)}


@app.delete("/v1/vectors/{doc_id}")
def vectors_delete(doc_id: str) -> dict:
    return {"deleted": STORE.delete(doc_id), "total": len(STORE)}


# =====================================================
# Certificate explorer + verification
# =====================================================
@app.get("/certificates")
def certificates(limit: int = 20) -> dict:
    return {"count": len(LEDGER), "certificates": LEDGER.recent(limit)}


@app.get("/certificates/{serial}")
def certificate_by_serial(serial: str) -> dict:
    cert = LEDGER.by_serial(serial)
    if cert is None:
        raise HTTPException(status_code=404, detail="certificate not found")
    return cert


@app.post("/verify")
def verify_cert(req: VerifyRequest) -> dict:
    return {"valid": veil.verify(req.certificate)}


# =====================================================
# Metrics
# =====================================================
def _metrics() -> dict:
    certs = LEDGER.all()
    clean = [c for c in certs if c["carbon"]["energy_source"] in config.CLEAN_SOURCES]
    return {
        "node_id": config.NODE_ID,
        "jobs": len(certs),
        "energy_kwh": round(sum(c["carbon"]["energy_kwh"] for c in certs), 6),
        "co2_g": round(sum(c["carbon"]["est_gco2"] for c in certs), 6),
        "clean_pct": round(100 * len(clean) / len(certs), 1) if certs else 0.0,
        "vectors": len(STORE),
        "refused": _stats["refused"],
        "uptime_s": round(time.time() - START, 1),
        **_stats,
    }


@app.get("/metrics")
def metrics() -> dict:
    return _metrics()


@app.get("/metrics/prom", response_class=PlainTextResponse)
def metrics_prom() -> str:
    m = _metrics()
    lines = [
        f'ealna_node_jobs_total{{node="{config.NODE_ID}"}} {m["jobs"]}',
        f'ealna_node_energy_kwh{{node="{config.NODE_ID}"}} {m["energy_kwh"]}',
        f'ealna_node_co2_grams{{node="{config.NODE_ID}"}} {m["co2_g"]}',
        f'ealna_node_clean_pct{{node="{config.NODE_ID}"}} {m["clean_pct"]}',
        f'ealna_node_refused_total{{node="{config.NODE_ID}"}} {m["refused"]}',
        f'ealna_node_vectors{{node="{config.NODE_ID}"}} {m["vectors"]}',
    ]
    return "\n".join(lines) + "\n"
