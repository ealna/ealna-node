from ealna_node.core import metrics, veil
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


def test_certificate_summary_aggregates_the_ledger(settings):
    certs = [
        {"carbon": {"energy_source": "solar", "energy_kwh": 0.01, "est_gco2": 0.4, "carbon_score": 90}},
        {"carbon": {"energy_source": "wind", "energy_kwh": 0.02, "est_gco2": 0.5, "carbon_score": 96}},
        {"carbon": {"energy_source": "unknown", "energy_kwh": 0.03, "est_gco2": 14.0, "carbon_score": 5}},
    ]
    s = metrics.certificate_summary(certs, settings.clean_sources)
    assert s["count"] == 3
    assert s["energy_kwh"] == 0.06
    assert s["by_source"] == {"solar": 1, "wind": 1, "unknown": 1}
    assert s["clean_pct"] == round(200 / 3, 1)               # 2 of 3 on clean sources
    assert s["avg_carbon_score"] == round((90 + 96 + 5) / 3, 1)


def test_certificate_summary_empty_ledger(settings):
    assert metrics.certificate_summary([], settings.clean_sources)["count"] == 0
