"""Request/response schemas (OpenAI-compatible where applicable)."""
from __future__ import annotations

from pydantic import BaseModel


class Msg(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Msg]
    max_tokens: int | None = 256
    temperature: float | None = 0.7
    stream: bool | None = False


class CompletionRequest(BaseModel):
    model: str | None = None
    prompt: str
    max_tokens: int | None = 256


class EmbeddingRequest(BaseModel):
    model: str | None = None
    input: str | list[str]


class UpsertItem(BaseModel):
    id: str
    text: str
    metadata: dict | None = None


class UpsertRequest(BaseModel):
    items: list[UpsertItem]


class QueryRequest(BaseModel):
    query: str
    k: int | None = 5


class VerifyRequest(BaseModel):
    certificate: dict
