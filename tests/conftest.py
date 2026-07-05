"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ealna_node.app import create_app
from ealna_node.config import Settings


def make_settings(**overrides) -> Settings:
    base = dict(
        node_id="node-test", node_url="http://localhost:8000", solar_url="",
        gateway_url="", default_model="open-llm-8b", signing_key=b"test-key",
        tee_mode="TEE", embed_dim=64, ledger_path="", rate_qps=50, rate_burst=100,
        blocklist=("forbidden", "malware"),
    )
    base.update(overrides)
    return Settings(**base)


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))
