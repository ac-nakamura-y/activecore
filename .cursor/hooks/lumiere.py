#!/usr/bin/env python3
"""Lumiere: enabled conversations sleep until the next tick, then notify the agent."""

from __future__ import annotations

import json
import os
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


def read_enabled() -> list[str]:
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        enabled = data.get("enabled", [])
        return enabled if isinstance(enabled, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def write_enabled(enabled: list[str]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps({"enabled": enabled}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_command(prompt: str) -> bool | None:
    text = prompt.strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()
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


def next_tick(after: datetime) -> datetime:
    test_minutes = int(os.environ.get("LUMIERE_TEST_INTERVAL_MINUTES", "0"))
    if test_minutes > 0:
        return after + timedelta(minutes=test_minutes)

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


def set_enabled(conversation_id: str, enabled: bool) -> str:
    ids = read_enabled()
    if enabled:
        if conversation_id not in ids:
            ids.append(conversation_id)
        write_enabled(ids)
        log(f"ENABLED {conversation_id}")
        return "Lumiere を有効化しました。"
    ids = [item for item in ids if item != conversation_id]
    write_enabled(ids)
    log(f"DISABLED {conversation_id}")
    return "Lumiere を無効化しました。"


def before_submit() -> int:
    payload = read_payload()
    conversation_id = payload.get("conversation_id", "")
    command = parse_command(payload.get("prompt", ""))

    if command is None or not conversation_id:
        print(json.dumps({"continue": True}))
        return 0

    if command:
        set_enabled(conversation_id, True)
        print(
            json.dumps(
                {
                    "continue": True,
                    "user_message": "Lumiere を有効化しました。",
                    "agent_message": (
                        "Lumiere が有効化されました。"
                        "『有効化しました』とだけ返答して終了してください。"
                        "ツールは使わず、同期もまだ行わないでください。"
                    ),
                },
                ensure_ascii=False,
            )
        )
        return 0

    message = set_enabled(conversation_id, False)
    print(json.dumps({"continue": False, "user_message": message}, ensure_ascii=False))
    return 0


def stop() -> int:
    payload = read_payload()
    conversation_id = payload.get("conversation_id", "")
    enabled = read_enabled()
    log(f"STOP conv={conversation_id or '<missing>'} enabled={conversation_id in enabled}")

    if conversation_id not in enabled:
        return 0

    now = datetime.now(TZ)
    target = next_tick(now)
    seconds = max(1, int((target - now).total_seconds()))
    test_minutes = int(os.environ.get("LUMIERE_TEST_INTERVAL_MINUTES", "0"))
    mode = f"test={test_minutes}m" if test_minutes > 0 else "prod"
    log(f"SLEEP sec={seconds} next={target.isoformat()} mode={mode}")
    time.sleep(seconds)
    log(f"FOLLOWUP {conversation_id}")
    print(json.dumps({"followup_message": FOLLOWUP}, ensure_ascii=False))
    return 0


def main() -> int:
    commands = {"before-submit": before_submit, "stop": stop}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print("usage: lumiere.py <before-submit|stop>", file=sys.stderr)
        return 2
    return commands[sys.argv[1]]()


if __name__ == "__main__":
    raise SystemExit(main())
