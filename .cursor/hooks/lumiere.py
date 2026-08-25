#!/usr/bin/env python3
"""Lumiere: per-conversation Gemini meeting notes sync."""

from __future__ import annotations

import json
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
    "CLAUDE.md の Gemini 議事録登録手順を実行。"
)


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


def parse_command(prompt: str) -> bool | None:
    text = prompt.strip().lower()
    if text == "/lumiere off":
        return False
    if text in ("/lumiere", "/lumiere on"):
        return True
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


def before_submit() -> int:
    payload = read_payload()
    command = parse_command(payload.get("prompt", ""))
    conversation_id = payload.get("conversation_id", "")
    if command is None or not conversation_id:
        print(json.dumps({"continue": True}))
        return 0

    enabled, wake = read_state()
    if command:
        if conversation_id not in enabled:
            enabled.append(conversation_id)
        write_state(enabled, conversation_id)
        log(f"ENABLED {conversation_id}")
        message = "Lumiere を有効化しました。"
    else:
        enabled = [item for item in enabled if item != conversation_id]
        write_state(enabled, None if wake == conversation_id else wake)
        log(f"DISABLED {conversation_id}")
        message = "Lumiere を無効化しました。"

    print(json.dumps({"continue": False, "user_message": message}, ensure_ascii=False))
    return 0


def stop() -> int:
    conversation_id = read_payload().get("conversation_id", "")
    enabled, wake = read_state()
    if conversation_id not in enabled:
        log(f"SKIP {conversation_id or '<missing>'}")
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
