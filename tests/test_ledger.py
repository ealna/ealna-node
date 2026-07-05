from ealna_node.core.ledger import Ledger


def test_serial_increments_and_lookup():
    led = Ledger()
    s1, s2 = led.next_serial(), led.next_serial()
    assert (s1, s2) == ("GCC-000000001", "GCC-000000002")
    led.append({"serial": s1, "x": 1})
    assert led.by_serial(s1)["x"] == 1
    assert led.by_serial("GCC-nope") is None


def test_recent_is_newest_first():
    led = Ledger()
    for i in range(3):
        led.append({"serial": led.next_serial(), "i": i})
    assert [c["i"] for c in led.recent(2)] == [2, 1]


def test_persistence_roundtrip(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    s = led.next_serial()
    led.append({"serial": s, "v": 42})
    reloaded = Ledger(path)                                   # re-read from disk
    assert len(reloaded) == 1
    assert reloaded.by_serial(s)["v"] == 42
    assert reloaded.next_serial() == "GCC-000000002"         # continues the count
