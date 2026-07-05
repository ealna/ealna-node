"""Legacy text completions — OpenAI-compatible `/v1/completions`."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings
from ..core import backends
from ..core.certificates import CertificateService
from ..core.ratelimit import TokenBucket
from ..models import CompletionRequest
from . import deps

router = APIRouter(tags=["inference"])


@router.post("/v1/completions")
def completions(req: CompletionRequest,
                settings: Settings = Depends(deps.get_settings),
                certs: CertificateService = Depends(deps.get_certs),
                bucket: TokenBucket = Depends(deps.get_bucket),
                stats: dict = Depends(deps.get_stats)):
    if not bucket.allow():
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    model = req.model or settings.default_model
    out = backends.run_chat(model, [{"role": "user", "content": req.prompt}])
    stats["completions"] += 1
    cert = certs.mint(model, out, backends.tokens(req.prompt), backends.tokens(out))
    return {"id": cert["job_id"], "object": "text_completion", "model": model,
            "choices": [{"index": 0, "text": out, "finish_reason": "stop"}],
            "usage": cert["usage"], "ealna_certificate": cert}
