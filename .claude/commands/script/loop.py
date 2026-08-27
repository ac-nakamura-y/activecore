#!/usr/bin/env python3
"""Wait for the next scheduled slot, then print one tick line.

Scheduling (see constants and env below):
  - timezone: fixed (Asia/Tokyo)
  - active days: weekdays (Mon–Fri)
  - hour range: START_HOUR .. END_HOUR each active day
  - minute marks: MINUTES within each hour in that range

Each cycle: find the next slot after now → sleep → print TICK.
Run in a Cursor background shell; match stdout with notify_on_output.
"""
import os
import time
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tokyo")
TICK = 'AGENT_LOOP_TICK_COGSWORTH {"prompt":"CLAUDE.md の Cogsworth > 同期 手順を実行。"}'

START_HOUR = int(os.environ.get("COGSWORTH_START_HOUR", 10))
END_HOUR = int(os.environ.get("COGSWORTH_END_HOUR", 19))
MINUTES = (15, 45)  # minute-of-hour marks to fire within each hour in range

while True:
    now = datetime.now(TZ)
    d = now.date()
    target = None
    # Scan forward until the first slot strictly after `now`.
    while target is None:
        if d.weekday() < 5:  # weekday only
            for h in range(START_HOUR, END_HOUR + 1):
                for m in MINUTES:
                    t = datetime.combine(d, dt_time(h, m), tzinfo=TZ)
                    if t > now:
                        target = t
                        break
                if target:
                    break
        d += timedelta(days=1)

    # Sleep until the chosen slot, then emit tick (Agent notification trigger).
    time.sleep(max(1, int((target - now).total_seconds())))
    print(TICK, flush=True)
