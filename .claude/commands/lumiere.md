---
description: Periodic sync of Gemini meeting notes (on / off)
argument-hint: on | off
---

# Lumiere

/lumiere $ARGUMENTS

`$1` が `off` なら無効化する。未指定または `on` なら有効化する。

## 手順

### off

タイトル `Loop meeting notes sync` の背景シェルループを停止する。見つからなければその旨を伝える。

### on

同期手順は `CLAUDE.md` の Lumiere > 同期。有効化時はループ起動、初回同期、定期 tick の順で動く。

背景シェルが同じ tick を出していなければ、次のループを起動する。次の実行時刻まで sleep し、tick を出力する。

```bash
while true; do
  sleep "$(python3 <<'PY'
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

tz = ZoneInfo("Asia/Tokyo")
now = datetime.now(tz)

def iter_slots(from_date):
    d = from_date
    for _ in range(14):
        if d.weekday() < 5:
            for h in range(10, 20):
                for m in (15, 45):
                    t = datetime.combine(d, time(h, m), tzinfo=tz)
                    if h * 60 + m > 19 * 60 + 30:
                        continue
                    yield t
        d += timedelta(days=1)

target = next(t for t in iter_slots(now.date()) if t > now)
print(max(1, int((target - now).total_seconds())))
PY
)"
  echo 'AGENT_LOOP_TICK_meeting_notes_sync {"prompt":"CLAUDE.md の Lumiere > 同期 手順を実行。"}'
done
```

| 項目 | 値 |
| :-- | :-- |
| シェルタイトル | `Loop meeting notes sync` |
| notify pattern | `^AGENT_LOOP_TICK_meeting_notes_sync` |
| 実行 | `block_until_ms: 0`（背景） |
| スケジュール | 平日 `10:00`〜`19:30`、各時 `15` 分・`45` 分（`Asia/Tokyo`） |

ループ起動直後に同期手順を 1 回実行する。初回 tick は次のスケジュール時刻まで待つ。

`AGENT_LOOP_TICK_meeting_notes_sync` を受け取ったら同期手順だけ実行する。ループは再起動しない。
