#!/usr/bin/env python3
import os
import time
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tokyo")
TICK = 'AGENT_LOOP_TICK_COGSWORTH {"prompt":"CLAUDE.md の Cogsworth > 同期 手順を実行。"}'

START_HOUR = int(os.environ.get("COGSWORTH_START_HOUR", 10))
END_HOUR = int(os.environ.get("COGSWORTH_END_HOUR", 19))
MINUTES = (15, 45)

while True:
    now = datetime.now(TZ)
    d = now.date()
    target = None
    while target is None:
        if d.weekday() < 5:
            for h in range(START_HOUR, END_HOUR + 1):
                for m in MINUTES:
                    t = datetime.combine(d, dt_time(h, m), tzinfo=TZ)
                    if t > now:
                        target = t
                        break
                if target:
                    break
        d += timedelta(days=1)

    time.sleep(max(1, int((target - now).total_seconds())))
    print(TICK, flush=True)
