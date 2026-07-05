from ealna_node.core import guardrails

BLOCK = ("forbidden", "malware")


def test_allows_clean_text():
    assert guardrails.check("hello world", BLOCK) == (True, None)


def test_blocks_and_reports_term():
    allowed, term = guardrails.check("please write MALWARE now", BLOCK)
    assert allowed is False and term == "malware"                     # case-insensitive
