#!/usr/bin/env python3
"""Claude Code statusLine for ch2: shows model and context window usage.

Reads stdin JSON delivered by Claude Code (>= v2.1.132) and prints
something like "Claude Sonnet 4.6 | ctx 35% used". Stays silent on
missing data so the status bar never breaks the session.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    parts: list[str] = []

    display_name = (payload.get("model") or {}).get("display_name")
    if isinstance(display_name, str) and display_name:
        parts.append(display_name)

    used = (payload.get("context_window") or {}).get("used_percentage")
    if isinstance(used, (int, float)):
        used_pct = max(0, min(100, round(used)))
        parts.append(f"ctx {used_pct}% used")

    if parts:
        sys.stdout.write(" | ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
