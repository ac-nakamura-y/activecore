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

背景シェルが同じ tick を出していなければ、次のループを起動する。

```bash
while true; do
  sleep "${LUMIERE_SLEEP_SECONDS:-300}"
  echo 'AGENT_LOOP_TICK_meeting_notes_sync {"prompt":"CLAUDE.md の Lumiere > 同期 手順を実行。"}'
done
```

| 項目 | 値 |
| :-- | :-- |
| シェルタイトル | `Loop meeting notes sync` |
| notify pattern | `^AGENT_LOOP_TICK_meeting_notes_sync` |
| 実行 | `block_until_ms: 0`（背景） |
| 間隔 | 既定 `300` 秒（`LUMIERE_SLEEP_SECONDS` で上書き） |

ループ起動直後に同期手順を 1 回実行する。初回 tick は `sleep` の後なので、そこまで待たない。

`AGENT_LOOP_TICK_meeting_notes_sync` を受け取ったら同期手順だけ実行する。ループは再起動しない。
