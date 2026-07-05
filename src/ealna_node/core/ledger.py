"""Certificate ledger — serial allocation + optional JSONL persistence.

ponytail: append-only JSONL on local disk. Swap for a database or an on-chain
registry for a real, tamper-evident certificate explorer.
"""
from __future__ import annotations

import json
import os
import threading


def _serial_num(cert: dict) -> int:
    try:
        return int(cert["serial"].split("-")[1])
    except Exception:
        return 0


class Ledger:
    def __init__(self, path: str = "") -> None:
        self.path = path
        self._items: list[dict] = []
        self._serial = 0
        self._lock = threading.Lock()
        if path and os.path.exists(path):
            with open(path) as f:                       # reload prior certificates
                for line in f:
                    line = line.strip()
                    if line:
                        cert = json.loads(line)
                        self._items.append(cert)
                        self._serial = max(self._serial, _serial_num(cert))

    def next_serial(self) -> str:
        with self._lock:
            self._serial += 1
            return f"GCC-{self._serial:09d}"

    def append(self, cert: dict) -> None:
        self._items.append(cert)
        if self.path:
            with open(self.path, "a") as f:
                f.write(json.dumps(cert) + "\n")

    def recent(self, limit: int) -> list[dict]:
        return self._items[-limit:][::-1]

    def by_serial(self, serial: str) -> dict | None:
        return next((c for c in self._items if c["serial"] == serial), None)

    def all(self) -> list[dict]:
        return self._items

    def __len__(self) -> int:
        return len(self._items)
