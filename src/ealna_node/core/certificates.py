"""Green Compute Certificate minting — binds privacy + carbon proofs, signs, ledgers."""
from __future__ import annotations

import time
import uuid

from ..config import Settings
from . import backends, veil
from .green import CarbonClient
from .ledger import Ledger


class CertificateService:
    def __init__(self, ledger: Ledger, carbon: CarbonClient, settings: Settings) -> None:
        self.ledger = ledger
        self.carbon = carbon
        self.settings = settings

    def mint(self, model: str, output_text: str, prompt_tokens: int,
             completion_tokens: int, extra: dict | None = None) -> dict:
        econ = backends.economics(model)
        total = prompt_tokens + completion_tokens
        energy_kwh = round(total / 1000 * econ["kwh_per_1k"], 6)
        carbon = self.carbon.reading(energy_kwh)
        cert = {
            "job_id": "ea_" + uuid.uuid4().hex[:8],
            "node_id": self.settings.node_id,
            "model": model,
            "privacy": veil.privacy_attestation(output_text.encode(), self.settings.tee_mode),
            "carbon": carbon,
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                      "total_tokens": total},
            "hour": time.strftime("%Y-%m-%dT%H:00Z", time.gmtime()),
            "serial": self.ledger.next_serial(),
            "status": "degraded" if carbon["energy_source"] == "unknown" else "verified",
            "settlement": {"rail": "x402", "asset": "EALNA",
                           "price_est": round(total / 1000 * econ["price_per_1k"], 6)},
        }
        if extra:
            cert.update(extra)
        cert["signature"] = veil.sign(cert, self.settings.signing_key)
        self.ledger.append(cert)
        return cert
