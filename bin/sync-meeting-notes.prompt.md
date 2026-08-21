# Meeting notes sync → activecore

終了済みカレンダーイベントに添付された Gemini 議事録を、ローカルの activecore DB に登録する。
運用ルールの正本はリポジトリ内 CLAUDE.md の「Meeting notes sync」セクション。

## 前提

- CLI: ~/activecore/bin/activecore
- DB: ~/activecore/db/refs.sqlite
- カレンダー: y.nakamura@activecore.jp
- タグ推定ルール: schema.sql の tag_rules
- ログ追記先: ~/activecore/tmp/meeting-notes-sync.log

## 手順

### 1. カレンダー取得

MCP サーバーは **user plugin** を使う（project の `.cursor/mcp.json` は使わない）:
- Calendar: `plugin-google-calendar-google-calendar`
- Drive: `plugin-google-drive-google-drive`

Google Calendar MCP list_events:
- calendarId: y.nakamura@activecore.jp
- startTime: 過去 7 日
- endTime: 現在時刻 − 30 分（終了済みのみ）
- orderBy: startTime

### 2. Gemini 添付の抽出

各イベントの attachments から:
- title が「Gemini によるメモ」のものだけ対象
- fileUrl から doc ID を抽出（/document/d/{docId}/）
- Meet 録画のみ（Gemini 添付なし）はスキップ

### 3. 未登録判定

doc ID が refs.source に既にあるか sqlite3 で確認:

  SELECT id FROM refs WHERE source LIKE '%/document/d/{docId}/%'

ヒットしたらスキップ。

### 4. 本文取得

`plugin-google-drive-google-drive` の `read_file_content` で doc ID から本文取得。

品質チェック（必須）:
- 本文が <!DOCTYPE html> で始まる、または Sign in / Cookie / accounts.google.com を含む → save しない
- 本文が空、または 500 文字未満 → 失敗として記録

### 5. save

本文を /tmp/activecore-meeting-{docId}.md に書き出し:

  ~/activecore/bin/activecore save \
    --title "{イベント summary}" \
    --source "https://docs.google.com/document/d/{docId}/edit" \
    --content-file /tmp/activecore-meeting-{docId}.md \
    --require-tag

- タイトルはイベントの summary をそのまま使う
- 複数タグが推定された場合は --tag をタグごとに分けて渡す

タグ確認:

  ~/activecore/bin/activecore tag infer "会議タイトル"

### 6. タグ推定失敗時

--require-tag で失敗した場合:
- タグを推測で付けない
- doc ID・タイトルを ~/activecore/tmp/meeting-notes-pending-tags.json に追記
- 他の会議の処理は続行

### 7. ログ

各件を ~/activecore/tmp/meeting-notes-sync.log に追記:
- OK {docId} {title}
- SKIP {docId} {title}
- FAIL {docId} {title} {reason}
- PENDING_TAG {docId} {title}

最後に1行で REPORT events=N gemini=N saved=N skipped=N failed=N pending_tags=N

## 定期実行

Cursor IDE 上の Agent ループで動かす（launchd / cron 不可 — Google MCP は IDE plugin 必須）。

- ループ: `~/activecore/bin/meeting-notes-sync-loop watchdog`（平日 10:00–18:30、毎時 :15 / :45、5分ごと自動再起動）
- 停止: `~/activecore/bin/meeting-notes-sync-loop stop`
- ティック受信時のみこの手順を実行する

## 禁止事項

- 推測でタグを付けない
- 登録済み doc の再 save（本文更新が必要な場合を除く）
- gog / gogcli の使用
- Chrome / playwright / fetch-gdoc 等のフォールバック（MCP 失敗時は処理を中断し、エラーを報告）

## MCP 認証エラー時

Google Calendar / Drive user plugin が失敗した場合:
- save しない
- フォールバックしない
- エラー内容を ~/activecore/tmp/meeting-notes-sync.log に記録し、非ゼロ exit で終了
- Cursor IDE → Settings → Plugins で Google Calendar / Google Drive を Install し、Google サインインを完了する
