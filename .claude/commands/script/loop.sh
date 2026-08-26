#!/usr/bin/env bash
set -euo pipefail

while true; do
  sleep "$(python3 <<'PY'
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

tz = ZoneInfo("Asia/Tokyo")
now = datetime.now(tz)
d = now.date()

for _ in range(14):
    if d.weekday() < 5:
        for h in range(10, 20):
            for m in (15, 45):
                if h * 60 + m > 19 * 60 + 30:
                    continue
                t = datetime.combine(d, time(h, m), tzinfo=tz)
                if t > now:
                    print(max(1, int((t - now).total_seconds())))
                    raise SystemExit
    d += timedelta(days=1)

raise SystemExit("no slot found")
PY
)"
  echo 'AGENT_LOOP_TICK_COGSWORTH {"prompt":"CLAUDE.md の Cogsworth > 同期 手順を実行。"}'
done
