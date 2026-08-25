#!/usr/bin/env python3
"""Per-conversation opt-in state for meeting notes sync hooks."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = ROOT / "tmp" / "meeting-notes-sync-enabled.json"
LOG_FILE = ROOT / "tmp" / "meeting-notes-sync.log"

LUMIERE_OFF = re.compile(r"^/lumiere\s+off\s*$", re.IGNORECASE)
LUMIERE_ON = re.compile(r"^/lumiere(?:\s+on)?\s*$", re.IGNORECASE)


def log_line(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp} STATE {message}\n")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def is_enabled(conversation_id: str | None) -> bool:
    if not conversation_id:
        return False
    entry = load_state().get(conversation_id)
    return bool(entry and entry.get("enabled"))


def set_enabled(conversation_id: str, enabled: bool) -> None:
    data = load_state()
    if enabled:
        data[conversation_id] = {
            "enabled": True,
            "enabled_at": datetime.now().astimezone().isoformat(),
        }
        log_line(f"ENABLED conversation_id={conversation_id}")
    else:
        if conversation_id in data:
            log_line(f"DISABLED conversation_id={conversation_id}")
        data.pop(conversation_id, None)
    save_state(data)


def detect_action(prompt: str) -> str | None:
    stripped = prompt.strip()
    if LUMIERE_OFF.match(stripped):
        return "disable"
    if LUMIERE_ON.match(stripped):
        return "enable"
    return None


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: meeting-notes-sync-state.py <check|enable|disable> <conversation_id>", file=sys.stderr)
        return 2

    command = sys.argv[1]
    if command == "check":
        conversation_id = sys.argv[2] if len(sys.argv) > 2 else ""
        return 0 if is_enabled(conversation_id) else 1

    if command in {"enable", "disable"}:
        if len(sys.argv) < 3:
            print(f"usage: meeting-notes-sync-state.py {command} <conversation_id>", file=sys.stderr)
            return 2
        set_enabled(sys.argv[2], command == "enable")
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
