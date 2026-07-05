from ealna_node.core import veil


def test_attestation_shape():
    att = veil.privacy_attestation(b"payload", "FHE")
    assert att["mode"] == "FHE"
    assert att["attestation"].startswith("0x") and att["data_exposed"] is False


def test_sign_and_verify_roundtrip():
    key = b"k"
    cert = {"serial": "GCC-1", "model": "m"}
    cert["signature"] = veil.sign(cert, key)
    assert veil.verify(cert, key) is True


def test_verify_rejects_tamper_and_wrong_key():
    key = b"k"
    cert = {"serial": "GCC-1", "model": "m"}
    cert["signature"] = veil.sign(cert, key)
    assert veil.verify({**cert, "model": "evil"}, key) is False
    assert veil.verify(cert, b"other-key") is False
    assert veil.verify({"serial": "GCC-1"}, key) is False          # unsigned
