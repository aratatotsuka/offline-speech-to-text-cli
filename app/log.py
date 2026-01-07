from __future__ import annotations

import sys
from datetime import datetime, timezone


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_info(*parts: str) -> None:
    print(_ts(), "INFO", *parts, file=sys.stderr)


def log_error(*parts: str) -> None:
    print(_ts(), "ERROR", *parts, file=sys.stderr)

