#!/usr/bin/env python3
"""Lumiere: per-conversation Gemini meeting notes sync."""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "tmp" / "lumiere.json"
LOG = ROOT / "tmp" / "lumiere.log"
TZ = ZoneInfo("Asia/Tokyo")
FOLLOWUP = (
    "AGENT_LOOP_TICK_meeting_notes_sync: "
    "CLAUDE.md の Lumiere > 同期 手順を実行。"
)

LUMIERE_OFF = re.compile(r"^/lumiere\s+off\s*$", re.IGNORECASE)
LUMIERE_ON = re.compile(r"^/lumiere(?:\s+on)?\s*$", re.IGNORECASE)


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now(TZ).isoformat(timespec='seconds')} {message}\n")


def read_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def read_state() -> tuple[list[str], str | None]:
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        enabled = data.get("enabled", [])
        wake = data.get("wake")
        if not isinstance(enabled, list):
            enabled = []
        if wake is not None and not isinstance(wake, str):
            wake = None
        return enabled, wake
    except (OSError, json.JSONDecodeError):
        return [], None


def write_state(enabled: list[str], wake: str | None) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps({"enabled": enabled, "wake": wake}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2].strip()


def parse_command(prompt: str) -> bool | None:
    text = strip_frontmatter(prompt.strip())
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("---"):
            continue
        if LUMIERE_OFF.match(candidate):
            return False
        if LUMIERE_ON.match(candidate):
            return True
    if LUMIERE_OFF.match(text):
        return False
    if LUMIERE_ON.match(text):
        return True
    return None


def detect_command(payload: dict) -> bool | None:
    action = parse_command(payload.get("prompt", ""))
    if action is not None:
        return action
    for attachment in payload.get("attachments") or []:
        if attachment.get("type") != "file":
            continue
        path = Path(attachment.get("file_path", ""))
        if "lumiere" not in path.name.lower():
            continue
        try:
            action = parse_command(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if action is not None:
            return action
    return None


def next_tick(after: datetime) -> datetime:
    cursor = after
    for _ in range(400):
        day = cursor.date()
        if day.weekday() < 5:
            for hour in range(10, 20):
                for minute in (15, 45):
                    tick = datetime.combine(day, dt_time(hour, minute), tzinfo=TZ)
                    if dt_time(10, 0) <= tick.time() < dt_time(19, 30) and tick > after:
                        return tick
        cursor = datetime.combine(day + timedelta(days=1), dt_time(0, 0), tzinfo=TZ)
    raise RuntimeError("no tick found")


def followup() -> None:
    print(json.dumps({"followup_message": FOLLOWUP}, ensure_ascii=False))


def set_enabled(conversation_id: str, enabled: bool) -> str:
    enabled_ids, wake = read_state()
    if enabled:
        if conversation_id not in enabled_ids:
            enabled_ids.append(conversation_id)
        write_state(enabled_ids, conversation_id)
        log(f"ENABLED {conversation_id}")
        return "Lumiere を有効化しました。次の Agent 終了後に同期を開始します。"
    enabled_ids = [item for item in enabled_ids if item != conversation_id]
    write_state(enabled_ids, None if wake == conversation_id else wake)
    log(f"DISABLED {conversation_id}")
    return "Lumiere を無効化しました。"


def before_submit() -> int:
    payload = read_payload()
    conversation_id = payload.get("conversation_id", "")
    command = detect_command(payload)

    if command is None:
        if "lumiere" in payload.get("prompt", "").lower():
            log(f"UNMATCHED prompt={payload.get('prompt', '')[:200]!r}")
        print(json.dumps({"continue": True}))
        return 0

    if not conversation_id:
        log("BEFORE_SUBMIT missing conversation_id")
        print(json.dumps({"continue": True}))
        return 0

    message = set_enabled(conversation_id, command)
    print(json.dumps({"continue": False, "user_message": message}, ensure_ascii=False))
    return 0


def stop() -> int:
    payload = read_payload()
    conversation_id = payload.get("conversation_id", "")
    enabled, wake = read_state()
    log(f"STOP conv={conversation_id or '<missing>'} enabled={conversation_id in enabled} wake={wake}")

    if conversation_id not in enabled:
        return 0

    if wake == conversation_id:
        write_state(enabled, None)
        log(f"FOLLOWUP immediate {conversation_id}")
        followup()
        return 0

    now = datetime.now(TZ)
    target = next_tick(now)
    seconds = max(1, int((target - now).total_seconds()))
    log(f"SLEEP sec={seconds} next={target.isoformat()}")
    time.sleep(seconds)
    log(f"WAKE {conversation_id}")
    followup()
    return 0


def main() -> int:
    commands = {"before-submit": before_submit, "stop": stop}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print("usage: lumiere.py <before-submit|stop>", file=sys.stderr)
        return 2
    return commands[sys.argv[1]]()


if __name__ == "__main__":
    raise SystemExit(main())
