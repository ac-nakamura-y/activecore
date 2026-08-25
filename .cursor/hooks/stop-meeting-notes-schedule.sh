#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_PY="$ROOT/.cursor/hooks/meeting_notes_sync_state.py"
LOG="$ROOT/tmp/meeting-notes-sync.log"
PENDING="$ROOT/tmp/meeting-notes-sync-tick.pending"

WINDOW_START="${ACTIVECORE_SYNC_WINDOW_START:-10:00}"
WINDOW_END="${ACTIVECORE_SYNC_WINDOW_END:-19:30}"
SCHEDULE_MINUTES="${ACTIVECORE_SYNC_SCHEDULE_MINUTES:-15,45}"
TZ_NAME="${ACTIVECORE_SYNC_TZ:-Asia/Tokyo}"
WEEKDAYS_ONLY="${ACTIVECORE_SYNC_WEEKDAYS_ONLY:-1}"

PROMPT='Meeting notes sync: 終了済みカレンダーイベントの Gemini 議事録を activecore に登録。手順は ~/activecore/bin/sync-meeting-notes.prompt.md に従う。'

log_line() {
  mkdir -p "$ROOT/tmp"
  echo "$(TZ="$TZ_NAME" date +"%Y-%m-%dT%H:%M:%S%z") HOOK $*" >>"$LOG"
}

compute_sleep() {
  python3 - "$WINDOW_START" "$WINDOW_END" "$SCHEDULE_MINUTES" "$TZ_NAME" "$WEEKDAYS_ONLY" <<'PY'
import sys
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

start_parts = [int(x) for x in sys.argv[1].split(":")]
end_parts = [int(x) for x in sys.argv[2].split(":")]
tick_minutes = [int(x) for x in sys.argv[3].split(",") if x.strip()]
tz = ZoneInfo(sys.argv[4])
weekdays_only = sys.argv[5] == "1"

start_t = time(start_parts[0], start_parts[1])
end_t = time(end_parts[0], end_parts[1])

def is_active_day(d):
    return d.weekday() < 5 if weekdays_only else True

def window_for(d):
    if not is_active_day(d):
        return None
    s = datetime.combine(d, start_t, tzinfo=tz)
    e = datetime.combine(d, end_t, tzinfo=tz)
    return s, e

def tick_times_for_day(d):
    w = window_for(d)
    if not w:
        return []
    start, end = w
    out = []
    for hour in range(24):
        for minute in tick_minutes:
            t = datetime.combine(d, time(hour, minute), tzinfo=tz)
            if start <= t < end:
                out.append(t)
    return sorted(out)

def next_tick(after):
    d = after.date()
    for _ in range(370):
        for t in tick_times_for_day(d):
            if t > after:
                return t
        d += timedelta(days=1)
    raise RuntimeError("no tick found")

now = datetime.now(tz)
nxt = next_tick(now)
sleep_sec = max(1, int((nxt - now).total_seconds()))
print(sleep_sec)
print(nxt.isoformat())
PY
}

emit_followup() {
  local reason="$1"
  python3 - "$reason" "$PROMPT" <<'PY'
import json
import sys

reason, prompt = sys.argv[1], sys.argv[2]
message = f"AGENT_LOOP_TICK_meeting_notes_sync ({reason}): {prompt}"
print(json.dumps({"followup_message": message}, ensure_ascii=False))
PY
}

read_conversation_id() {
  python3 - "$1" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except json.JSONDecodeError:
    payload = {}
print(payload.get("conversation_id") or "")
PY
}

HOOK_INPUT="$(cat)"
CONVERSATION_ID="$(read_conversation_id "$HOOK_INPUT")"

if ! python3 "$STATE_PY" check "$CONVERSATION_ID"; then
  log_line "SKIP not enabled conversation_id=${CONVERSATION_ID:-<missing>}"
  exit 0
fi

reason="scheduled"
if [[ -f "$PENDING" ]]; then
  reason="$(cat "$PENDING")"
  rm -f "$PENDING"
  log_line "FOLLOWUP immediate reason=$reason"
  emit_followup "$reason"
  exit 0
fi

plan="$(compute_sleep)"
sleep_sec="$(printf '%s\n' "$plan" | sed -n '1p')"
next_tick="$(printf '%s\n' "$plan" | sed -n '2p')"

log_line "SLEEP sec=$sleep_sec next_tick=$next_tick"
sleep "$sleep_sec"
log_line "WAKE followup reason=$reason"
emit_followup "$reason"
