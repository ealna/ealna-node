import math

from ealna_node.core import vectors
from ealna_node.core.vectors import VectorStore


def test_embed_is_deterministic_and_unit_length():
    a, b = vectors.embed("solar", 64), vectors.embed("solar", 64)
    assert a == b
    assert len(a) == 64
    assert abs(math.sqrt(sum(x * x for x in a)) - 1.0) < 1e-6


def test_rag_ranks_lexically_closest_first():
    store = VectorStore(64)
    store.upsert("d1", "solar energy powers the clean grid")
    store.upsert("d2", "the cat sat on the mat")
    matches = store.query("solar energy clean grid power", k=2)
    assert matches[0]["id"] == "d1"
    assert matches[0]["score"] > matches[1]["score"]


def test_upsert_and_delete():
    store = VectorStore(32)
    store.upsert("d1", "hello")
    assert len(store) == 1
    assert store.delete("d1") is True
    assert store.delete("d1") is False and len(store) == 0
