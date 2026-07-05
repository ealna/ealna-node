"""The Veil — privacy attestation and certificate signing.

ponytail: attestation is a SHA-256 commit and the signature is HMAC — demo
stand-ins. Swap the attestation for a real TEE quote (SGX/SEV-SNP/TDX) and the
HMAC for node ed25519; the shapes stay identical so certificates stay comparable.
"""
from __future__ import annotations

import hashlib
import hmac
import json


def privacy_attestation(payload: bytes, mode: str = "TEE") -> dict:
    """A signed statement that the job ran inside a confidential enclave."""
    return {
        "mode": mode,
        "attestation": "0x" + hashlib.sha256(payload).hexdigest(),
        "data_exposed": False,
    }


def canonical(obj: dict) -> bytes:
    """Deterministic JSON encoding so signatures are reproducible."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sign(cert: dict, key: bytes) -> str:
    """HMAC-SHA256 over the certificate, excluding any existing signature field."""
    unsigned = {k: v for k, v in cert.items() if k != "signature"}
    return "0x" + hmac.new(key, canonical(unsigned), hashlib.sha256).hexdigest()


def verify(cert: dict, key: bytes) -> bool:
    """True iff the certificate's signature matches its contents."""
    sig = cert.get("signature")
    return bool(sig) and hmac.compare_digest(sig, sign(cert, key))
