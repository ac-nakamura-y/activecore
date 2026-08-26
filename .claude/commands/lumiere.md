---
description: Gemini 議事録の定期同期（on / off）
argument-hint: on | off
---

/lumiere $ARGUMENTS

`$1` が `off` なら無効化、未指定または `on` なら有効化する。

## off

`Loop meeting notes sync` というタイトルの背景シェルループを停止する。動いていなければその旨を伝える。

## on

同期手順は `CLAUDE.md` の Lumiere > 同期。

### ループ起動

同じ出力を出すループがなければ、背景シェルで起動する。

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

### 初回同期

ループ起動後、同期手順を直ちに 1 回実行する。初回 tick は sleep 後のため、tick を待たない。

### 定期 tick

`AGENT_LOOP_TICK_meeting_notes_sync` を受け取ったら同期手順のみ実行する。ループは再起動しない。
