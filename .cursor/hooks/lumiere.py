#!/usr/bin/env python3
"""Lumiere: per-conversation Gemini meeting notes sync."""

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
STATE_FILE = ROOT / "tmp" / "lumiere.json"
LOG_FILE = ROOT / "tmp" / "lumiere.log"

WINDOW_START = os.environ.get("LUMIERE_WINDOW_START", "10:00")
WINDOW_END = os.environ.get("LUMIERE_WINDOW_END", "19:30")
SCHEDULE_MINUTES = os.environ.get("LUMIERE_SCHEDULE_MINUTES", "15,45")
TZ_NAME = os.environ.get("LUMIERE_TZ", "Asia/Tokyo")
WEEKDAYS_ONLY = os.environ.get("LUMIERE_WEEKDAYS_ONLY", "1") == "1"

LUMIERE_OFF = re.compile(r"^/lumiere\s+off\s*$", re.IGNORECASE)
LUMIERE_ON = re.compile(r"^/lumiere(?:\s+on)?\s*$", re.IGNORECASE)

FOLLOWUP_PROMPT = (
    "AGENT_LOOP_TICK_meeting_notes_sync: "
    "CLAUDE.md の Gemini 議事録登録手順を実行。"
)


def log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {message}\n")


def empty_state() -> dict:
    return {"enabled": [], "wake": None}


def load_state() -> dict:
    if not STATE_FILE.exists():
        return empty_state()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_state()
    if not isinstance(data, dict):
        return empty_state()
    enabled = data.get("enabled")
    if not isinstance(enabled, list):
        enabled = []
    wake = data.get("wake")
    if wake is not None and not isinstance(wake, str):
        wake = None
    return {"enabled": enabled, "wake": wake}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def is_enabled(conversation_id: str) -> bool:
    return bool(conversation_id) and conversation_id in load_state()["enabled"]


def set_enabled(conversation_id: str, enabled: bool) -> None:
    state = load_state()
    enabled_ids = state["enabled"]
    if enabled:
        if conversation_id not in enabled_ids:
            enabled_ids.append(conversation_id)
        state["wake"] = conversation_id
        log(f"ENABLED {conversation_id}")
    else:
        if conversation_id in enabled_ids:
            enabled_ids.remove(conversation_id)
        if state["wake"] == conversation_id:
            state["wake"] = None
        log(f"DISABLED {conversation_id}")
    save_state(state)


def detect_action(prompt: str) -> str | None:
    stripped = prompt.strip()
    if LUMIERE_OFF.match(stripped):
        return "disable"
    if LUMIERE_ON.match(stripped):
        return "enable"
    return None


def parse_clock(value: str) -> dt_time:
    hour, minute = (int(part) for part in value.split(":", 1))
    return dt_time(hour, minute)


def next_tick(after: datetime) -> datetime:
    tz = after.tzinfo or ZoneInfo(TZ_NAME)
    start_t = parse_clock(WINDOW_START)
    end_t = parse_clock(WINDOW_END)
    tick_minutes = [int(part) for part in SCHEDULE_MINUTES.split(",") if part.strip()]

    def active_day(day) -> bool:
        return day.weekday() < 5 if WEEKDAYS_ONLY else True

    def ticks_for_day(day):
        if not active_day(day):
            return []
        start = datetime.combine(day, start_t, tzinfo=tz)
        end = datetime.combine(day, end_t, tzinfo=tz)
        out = []
        for hour in range(24):
            for minute in tick_minutes:
                tick = datetime.combine(day, dt_time(hour, minute), tzinfo=tz)
                if start <= tick < end:
                    out.append(tick)
        return sorted(out)

    day = after.date()
    for _ in range(370):
        for tick in ticks_for_day(day):
            if tick > after:
                return tick
        day += timedelta(days=1)
    raise RuntimeError("no tick found")


def emit_followup() -> None:
    print(json.dumps({"followup_message": FOLLOWUP_PROMPT}, ensure_ascii=False))


def before_submit() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    prompt = payload.get("prompt") or ""
    conversation_id = payload.get("conversation_id") or ""
    action = detect_action(prompt)
    if not action or not conversation_id:
        print(json.dumps({"continue": True}))
        return 0

    set_enabled(conversation_id, action == "enable")
    message = (
        "Lumiere を有効化しました。"
        if action == "enable"
        else "Lumiere を無効化しました。"
    )
    print(json.dumps({"continue": False, "user_message": message}, ensure_ascii=False))
    return 0


def stop() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    conversation_id = payload.get("conversation_id") or ""
    if not is_enabled(conversation_id):
        log(f"SKIP {conversation_id or '<missing>'}")
        return 0

    state = load_state()
    if state.get("wake") == conversation_id:
        state["wake"] = None
        save_state(state)
        log(f"FOLLOWUP immediate {conversation_id}")
        emit_followup()
        return 0

    now = datetime.now(ZoneInfo(TZ_NAME))
    target = next_tick(now)
    sleep_sec = max(1, int((target - now).total_seconds()))
    log(f"SLEEP sec={sleep_sec} next={target.isoformat()} conv={conversation_id}")
    time.sleep(sleep_sec)
    log(f"WAKE {conversation_id}")
    emit_followup()
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"before-submit", "stop"}:
        print("usage: lumiere.py <before-submit|stop>", file=sys.stderr)
        return 2
    if sys.argv[1] == "before-submit":
        return before_submit()
    return stop()


if __name__ == "__main__":
    raise SystemExit(main())
