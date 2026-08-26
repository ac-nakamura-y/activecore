#!/usr/bin/env python3
"""Lumiere: enable/disable and sleep duration for in-chat agent loop."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "tmp" / "lumiere.json"
LOG = ROOT / "tmp" / "lumiere.log"
TZ = ZoneInfo("Asia/Tokyo")

LUMIERE_OFF = re.compile(r"^/lumiere\s+off\s*$", re.IGNORECASE)
LUMIERE_ON = re.compile(r"^/lumiere(?:\s+on)?\s*$", re.IGNORECASE)

LOOP_INSTRUCTION = (
    "Lumiere が有効化されました。この会話で Lumiere ループを開始してください。"
    "会話を終了せず、以下を `tmp/lumiere.json` の enabled が true の間、繰り返します。"
    "1. Shell で `sleep $(python3 .cursor/hooks/lumiere.py sleep-seconds)` を実行し、完了まで待つ"
    "2. CLAUDE.md の Lumiere > 同期 手順を実行"
    "3. 1 に戻る"
    "今すぐ 1 から開始してください。"
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


def read_state() -> bool:
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        return bool(data.get("enabled"))
    except (OSError, json.JSONDecodeError):
        return False


def write_state(enabled: bool) -> None:
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


def sleep_seconds() -> int:
    if value := os.environ.get("LUMIERE_SLEEP_SECONDS"):
        return max(1, int(value))
    now = datetime.now(TZ)
    target = next_tick(now)
    return max(1, int((target - now).total_seconds()))


def before_submit() -> int:
    payload = read_payload()
    command = parse_command(payload.get("prompt", ""))

    if command is None:
        print(json.dumps({"continue": True}))
        return 0

    if command:
        write_state(True)
        log("ENABLED")
        print(
            json.dumps(
                {
                    "continue": True,
                    "user_message": "Lumiere を有効化しました。",
                    "agent_message": LOOP_INSTRUCTION,
                },
                ensure_ascii=False,
            )
        )
        return 0

    write_state(False)
    log("DISABLED")
    print(
        json.dumps(
            {"continue": False, "user_message": "Lumiere を無効化しました。"},
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: lumiere.py <before-submit|sleep-seconds>", file=sys.stderr)
        return 2

    if sys.argv[1] == "before-submit":
        return before_submit()
    if sys.argv[1] == "sleep-seconds":
        print(sleep_seconds())
        return 0

    print("usage: lumiere.py <before-submit|sleep-seconds>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
