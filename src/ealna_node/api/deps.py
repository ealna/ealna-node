"""FastAPI dependencies — pull shared services off `app.state`."""
from __future__ import annotations

from fastapi import Request

from ..config import Settings
from ..core.certificates import CertificateService
from ..core.ledger import Ledger
from ..core.ratelimit import TokenBucket
from ..core.vectors import VectorStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_certs(request: Request) -> CertificateService:
    return request.app.state.certs


def get_ledger(request: Request) -> Ledger:
    return request.app.state.ledger


def get_store(request: Request) -> VectorStore:
    return request.app.state.store


def get_bucket(request: Request) -> TokenBucket:
    return request.app.state.bucket


def get_stats(request: Request) -> dict:
    return request.app.state.stats
