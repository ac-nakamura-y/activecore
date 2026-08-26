---
description: Sync Gemini meeting notes to refs (on / off)
argument-hint: on | off
---

# Cogsworth

/cogsworth $ARGUMENTS

`$1` が `off` なら無効化する。未指定または `on` なら有効化する。

## 手順

### off

タイトル `Cogsworth` のバックグランドシェルを停止する。見つからなければその旨を伝える。

### on

同期とスケジュールは `CLAUDE.md` の Cogsworth。ループ起動後に同期を 1 回実行し、以降は tick ごとに同期する。

同じ tick を出すループがなければ、バックグランドシェルで `script/loop.sh` を起動する。

```bash
~/activecore/.claude/commands/script/loop.sh
```

| 項目 | 値 |
| :-- | :-- |
| タイトル | `Cogsworth` |
| pattern | `^AGENT_LOOP_TICK_COGSWORTH` |
| 実行 | `block_until_ms: 0`（バックグランド） |

`AGENT_LOOP_TICK_COGSWORTH` を受け取ったら同期手順だけ実行する。ループは再起動しない。
