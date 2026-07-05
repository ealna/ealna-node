"""Self-check for the node package. Run with `python test_node.py` or `pytest`."""
import os
import tempfile

from fastapi.testclient import TestClient

import backends
import veil
import vectors as vecmod
from app import app
from ledger import Ledger
from ratelimit import TokenBucket
from router import choose_model

client = TestClient(app)


def test_chat_signed_certificate_and_usage():
    r = client.post("/v1/chat/completions",
                    json={"messages": [{"role": "user", "content": "hello"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["choices"][0]["message"]["content"]
    assert body["usage"]["total_tokens"] > 0
    cert = body["ealna_certificate"]
    assert cert["privacy"]["data_exposed"] is False
    assert cert["serial"].startswith("GCC-")
    assert 0 <= cert["carbon"]["carbon_score"] <= 100
    # signature verifies over everything but itself
    assert veil.verify(cert)
    assert client.post("/verify", json={"certificate": cert}).json()["valid"] is True
    # tamper -> invalid
    bad = dict(cert, model="totally-different")
    assert client.post("/verify", json={"certificate": bad}).json()["valid"] is False


def test_completions_and_model_personalities():
    code = client.post("/v1/completions",
                       json={"model": "ealna-code-1", "prompt": "add two numbers"}).json()
    assert "```python" in code["choices"][0]["text"]          # code tier differs
    fast = client.post("/v1/completions",
                       json={"model": "open-llm-8b", "prompt": "hi"}).json()
    assert "```" not in fast["choices"][0]["text"]


def test_streaming_chat():
    r = client.post("/v1/chat/completions",
                    json={"messages": [{"role": "user", "content": "stream me"}], "stream": True})
    assert r.status_code == 200
    assert "data:" in r.text and "[DONE]" in r.text
    assert "ealna_certificate" in r.text


def test_guardrail_blocks():
    r = client.post("/v1/chat/completions",
                    json={"messages": [{"role": "user", "content": "please do forbidden thing"}]})
    body = r.json()
    assert body["choices"][0]["finish_reason"] == "content_filter"
    assert body["ealna_certificate"]["guardrail"]["blocked"] is True


def test_embeddings_and_vector_rag():
    e = client.post("/v1/embeddings", json={"input": ["a", "b"]}).json()
    assert len(e["data"]) == 2 and len(e["data"][0]["embedding"]) == vecmod.embed("a").__len__()
    client.post("/v1/vectors/upsert", json={"items": [
        {"id": "d1", "text": "solar energy powers the clean grid"},
        {"id": "d2", "text": "the cat sat on the mat"},
    ]})
    matches = client.post("/v1/vectors/query",
                          json={"query": "solar energy clean grid power", "k": 2}).json()["matches"]
    assert matches[0]["id"] == "d1"                           # lexically closest wins
    assert matches[0]["score"] > matches[1]["score"]


def test_router_and_catalog():
    assert choose_model("chat", "cheapest") == "open-llm-8b"
    assert choose_model("chat", "quality") == "open-llm-70b"
    assert client.get("/route?target=greenest").json()["model"] in backends.MODELS
    assert any(m["id"] == "ealna-code-1" for m in client.get("/v1/models").json()["data"])


def test_metrics_and_explorer():
    serial = client.get("/certificates").json()["certificates"][0]["serial"]
    assert client.get(f"/certificates/{serial}").json()["serial"] == serial
    assert client.get("/certificates/GCC-nope").status_code == 404
    assert client.get("/metrics").json()["jobs"] >= 1
    assert "ealna_node_jobs_total" in client.get("/metrics/prom").text


def test_ledger_persistence_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "led.jsonl")
        led = Ledger(path)
        s = led.next_serial()
        led.append({"serial": s, "x": 1})
        assert len(Ledger(path)) == 1                          # reloaded from disk
        assert Ledger(path).by_serial(s)["x"] == 1


def test_rate_limiter():
    tb = TokenBucket(qps=0, burst=2)
    assert tb.allow() and tb.allow() and not tb.allow()        # burst then empty


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} ok")
    print("ok")
