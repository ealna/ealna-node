"""Chat completions — OpenAI-compatible, with guardrails and optional SSE streaming."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..config import Settings
from ..core import backends, guardrails
from ..core.certificates import CertificateService
from ..core.ratelimit import TokenBucket
from ..models import ChatRequest
from . import deps

router = APIRouter(tags=["inference"])


def _stream(certs: CertificateService, model: str, out: str) -> StreamingResponse:
    def gen():
        for word in out.split(" "):
            chunk = {"object": "chat.completion.chunk", "model": model,
                     "choices": [{"index": 0, "delta": {"content": word + " "}}]}
            yield f"data: {json.dumps(chunk)}\n\n"
        cert = certs.mint(model, out, 1, backends.tokens(out))
        yield f"data: {json.dumps({'ealna_certificate': cert})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/v1/chat/completions")
def chat(req: ChatRequest,
         settings: Settings = Depends(deps.get_settings),
         certs: CertificateService = Depends(deps.get_certs),
         bucket: TokenBucket = Depends(deps.get_bucket),
         stats: dict = Depends(deps.get_stats)):
    if not bucket.allow():
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    model = req.model or settings.default_model
    msgs = [m.model_dump() for m in req.messages]
    prompt_text = " ".join(m["content"] for m in msgs)

    allowed, hit = guardrails.check(prompt_text, settings.blocklist)
    if not allowed:
        stats["refused"] += 1
        out = f"[refused] request blocked by guardrail: {hit!r}"
        cert = certs.mint(model, out, backends.tokens(prompt_text), backends.tokens(out),
                          {"guardrail": {"blocked": True, "term": hit}})
        return {"id": cert["job_id"], "object": "chat.completion", "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": out},
                             "finish_reason": "content_filter"}],
                "usage": cert["usage"], "ealna_certificate": cert}

    out = backends.run_chat(model, msgs)
    stats["chat"] += 1
    if req.stream:
        return _stream(certs, model, out)
    cert = certs.mint(model, out, backends.tokens(prompt_text), backends.tokens(out))
    return {"id": cert["job_id"], "object": "chat.completion", "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": out},
                         "finish_reason": "stop"}],
            "usage": cert["usage"], "ealna_certificate": cert}
