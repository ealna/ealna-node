from ealna_node.core import backends


def test_economics_fallback():
    assert backends.economics("open-llm-8b")["tier"] == "fast"
    assert backends.economics("nonexistent") == backends.MODELS[backends.FALLBACK]


def test_tokens_never_zero():
    assert backends.tokens("") == 1
    assert backends.tokens("a" * 40) == 10


def test_model_personalities_differ():
    msgs = [{"role": "user", "content": "add two numbers"}]
    assert "```python" in backends.run_chat("ealna-code-1", msgs)      # code tier
    assert "Reasoning" in backends.run_chat("open-llm-70b", msgs)      # quality tier
    assert "```" not in backends.run_chat("open-llm-8b", msgs)         # fast tier
