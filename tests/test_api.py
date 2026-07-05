import dataclasses

from fastapi.testclient import TestClient

from ealna_node.app import create_app


def test_chat_returns_signed_certificate(client):
    body = client.post("/v1/chat/completions",
                       json={"messages": [{"role": "user", "content": "hello"}]}).json()
    assert body["choices"][0]["message"]["content"]
    cert = body["ealna_certificate"]
    assert cert["serial"].startswith("GCC-")
    assert client.post("/verify", json={"certificate": cert}).json()["valid"] is True
    assert client.post("/verify", json={"certificate": {**cert, "model": "x"}}).json()["valid"] is False


def test_streaming(client):
    r = client.post("/v1/chat/completions",
                    json={"messages": [{"role": "user", "content": "hi"}], "stream": True})
    assert "data:" in r.text and "[DONE]" in r.text and "ealna_certificate" in r.text


def test_guardrail_blocks(client):
    body = client.post("/v1/chat/completions",
                       json={"messages": [{"role": "user", "content": "do forbidden thing"}]}).json()
    assert body["choices"][0]["finish_reason"] == "content_filter"
    assert body["ealna_certificate"]["guardrail"]["blocked"] is True


def test_completions_and_embeddings_and_rag(client):
    assert "```python" in client.post(
        "/v1/completions", json={"model": "ealna-code-1", "prompt": "hi"}).json()["choices"][0]["text"]
    e = client.post("/v1/embeddings", json={"input": ["a", "b"]}).json()
    assert len(e["data"]) == 2
    client.post("/v1/vectors/upsert", json={"items": [
        {"id": "d1", "text": "solar energy clean grid"},
        {"id": "d2", "text": "the cat sat on the mat"}]})
    m = client.post("/v1/vectors/query", json={"query": "solar energy clean grid", "k": 2}).json()["matches"]
    assert m[0]["id"] == "d1"


def test_models_route_and_metrics(client):
    assert any(x["id"] == "ealna-code-1" for x in client.get("/v1/models").json()["data"])
    assert client.get("/route?target=greenest").json()["model"] == "open-llm-8b"
    client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "x"}]})
    assert client.get("/metrics").json()["jobs"] >= 1
    assert "ealna_node_jobs_total" in client.get("/metrics/prom").text


def test_certificate_explorer(client):
    client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "x"}]})
    listing = client.get("/certificates").json()
    serial = listing["certificates"][0]["serial"]
    assert client.get(f"/certificates/{serial}").json()["serial"] == serial
    assert client.get("/certificates/GCC-nope").status_code == 404


def test_rate_limit_returns_429(settings):
    throttled = dataclasses.replace(settings, rate_qps=0, rate_burst=1)
    c = TestClient(create_app(throttled))
    assert c.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "1"}]}).status_code == 200
    assert c.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "2"}]}).status_code == 429
