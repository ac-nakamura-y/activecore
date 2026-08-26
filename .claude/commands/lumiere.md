---
description: Gemini 議事録の定期同期（on / off）
argument-hint: on | off
---

/lumiere $ARGUMENTS

引数 `$1` が `off` なら無効化、未指定・`on` なら有効化する。

## off

`Loop meeting notes sync` の背景シェルループを停止する。動いていなければその旨を伝える。

## on

未登録の Gemini 議事録を `refs` に定期登録する。同期手順は `CLAUDE.md` の Lumiere > 同期。

### 1. ループ起動

既存ターミナルに `AGENT_LOOP_TICK_meeting_notes_sync` を出力するループがなければ、背景シェルで起動する。

```bash
while true; do
  sleep "${LUMIERE_SLEEP_SECONDS:-300}"
  echo 'AGENT_LOOP_TICK_meeting_notes_sync {"prompt":"CLAUDE.md の Lumiere > 同期 手順を実行。"}'
done
```

- シェルタイトル: `Loop meeting notes sync`
- `notify_on_output` の pattern: `^AGENT_LOOP_TICK_meeting_notes_sync`
- `block_until_ms: 0` で背景実行
- 間隔の既定は 5 分（`LUMIERE_SLEEP_SECONDS` で上書き可）

### 2. 初回同期

ループ起動後、**今すぐ**同期手順を 1 回実行する。初回 tick は sleep 後なので、tick 通知は待たない。

### 3. 定期 tick

`AGENT_LOOP_TICK_meeting_notes_sync` を受け取ったら同期手順のみ実行する（ループの再起動はしない）。
