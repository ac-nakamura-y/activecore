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


def sleep_until_next():
    now = datetime.now(TZ)
    d = now.date()
    for _ in range(14):
        if d.weekday() < 5:
            for h in range(START_HOUR, END_HOUR + 1):
                for m in MINUTES:
                    t = datetime.combine(d, dt_time(h, m), tzinfo=TZ)
                    if t > now:
                        time.sleep(max(1, int((t - now).total_seconds())))
                        return
        d += timedelta(days=1)
    raise SystemExit("no slot found")


while True:
    sleep_until_next()
    print(TICK, flush=True)
