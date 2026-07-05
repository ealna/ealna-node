from ealna_node.core import veil
from ealna_node.core.certificates import CertificateService
from ealna_node.core.green import CarbonClient
from ealna_node.core.ledger import Ledger


def _service(settings):
    return CertificateService(Ledger(), CarbonClient(""), settings)   # no solar -> degraded


def test_mint_produces_signed_certificate(settings):
    cert = _service(settings).mint("open-llm-8b", "hello", 3, 5)
    assert cert["serial"] == "GCC-000000001"
    assert cert["usage"]["total_tokens"] == 8
    assert cert["status"] == "degraded"                      # carbon source unknown offline
    assert cert["settlement"]["rail"] == "x402"
    assert veil.verify(cert, settings.signing_key)


def test_extra_fields_are_merged_before_signing(settings):
    cert = _service(settings).mint("open-llm-8b", "x", 1, 1, {"guardrail": {"blocked": True}})
    assert cert["guardrail"]["blocked"] is True
    assert veil.verify(cert, settings.signing_key)           # signature covers the extra
