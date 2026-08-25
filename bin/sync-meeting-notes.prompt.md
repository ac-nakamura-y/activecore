# Meeting notes sync → activecore

終了済みカレンダーイベントに添付された Gemini 議事録を activecore に登録する。

## 前提

- CLI: ~/activecore/bin/activecore
- カレンダー: y.nakamura@activecore.jp
- MCP: `plugin-google-calendar-google-calendar`, `plugin-google-drive-google-drive`

## 手順

1. Calendar `list_events`（過去7日、終了30分以上前）
2. 添付 `title` が「Gemini によるメモ」の doc ID を抽出
3. `refs.source` に未登録のものだけ `read_file_content` → `save --require-tag`
4. ログ: `~/activecore/tmp/meeting-notes-sync.log` に `OK` / `SKIP` / `FAIL` / `REPORT`

## 品質チェック

- 本文が空、または 500 文字未満 → 失敗として記録
- HTML / サインイン画面 → save しない
- タグ推定失敗時は推測で付けない（ユーザー確認）
