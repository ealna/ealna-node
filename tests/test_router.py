from ealna_node.core.router import choose_model


def test_cheapest_and_quality_and_greenest():
    assert choose_model("chat", "cheapest") == "open-llm-8b"
    assert choose_model("chat", "quality") == "open-llm-70b"
    assert choose_model("chat", "greenest") == "open-llm-8b"


def test_tier_filter_and_no_match():
    assert choose_model("chat", "cheapest", tier="code") == "ealna-code-1"
    assert choose_model("embedding", "cheapest") == "ealna-embed-1"
    assert choose_model("chat", "cheapest", tier="does-not-exist") is None
