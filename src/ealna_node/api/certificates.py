"""Certificate explorer + signature verification."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings
from ..core import veil
from ..core.ledger import Ledger
from ..models import VerifyRequest
from . import deps

router = APIRouter(tags=["certificates"])


@router.get("/certificates")
def certificates(limit: int = 20, ledger: Ledger = Depends(deps.get_ledger)) -> dict:
    return {"count": len(ledger), "certificates": ledger.recent(limit)}


@router.get("/certificates/{serial}")
def certificate_by_serial(serial: str, ledger: Ledger = Depends(deps.get_ledger)) -> dict:
    cert = ledger.by_serial(serial)
    if cert is None:
        raise HTTPException(status_code=404, detail="certificate not found")
    return cert


@router.post("/verify")
def verify(req: VerifyRequest, settings: Settings = Depends(deps.get_settings)) -> dict:
    return {"valid": veil.verify(req.certificate, settings.signing_key)}
