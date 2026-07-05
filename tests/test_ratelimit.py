import time

from ealna_node.core.ratelimit import TokenBucket


def test_burst_then_empty():
    tb = TokenBucket(qps=0, burst=2)
    assert tb.allow() and tb.allow()
    assert not tb.allow()                                     # burst exhausted, no refill


def test_refills_over_time():
    tb = TokenBucket(qps=1000, burst=1)
    assert tb.allow()
    assert not tb.allow()
    time.sleep(0.01)                                          # ~10 tokens refill
    assert tb.allow()
