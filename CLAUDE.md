# activecore

会議・チャット・ドキュメントなどの文脈を AI エージェントに渡し、日々の作業を速く正確に進めるためのワークスペース。SQLite 上の参照資料インデックス `refs` が中核。各レコードはタイトル・要約・本文キャッシュ・取得元 URL（またはローカルパス）・タグを保持する。本文は `save` 時に DB へキャッシュし、以後は `get` で即読する。正本は `source` 側。要約は保存時にバックグラウンドで Cursor CLI が生成するため、保存 Agent は要約完了を待たない。

## Agent behavior

Agent は次の 2 点を必ず守る。

### Query first

タスク着手前、または判断・実装・回答の前に、関連資料を検索してコンテキストに載せる。

```bash
~/activecore/bin/activecore query <タスクに関連するキーワード>
~/activecore/bin/activecore query --tag トリプルエス
~/activecore/bin/activecore query --limit 10   # 直近の資料
```

キーワードはクライアント名・プロジェクト名・機能名・課題キーなど、文脈から推定する。ヒットした候補のうち関連度が高いものは `activecore get <id>` で本文を取る。`content` が無い旧レコードだけ `source` から fetch し、再 save する。新しい情報が出たら save して次回以降の検索に備える。

### Save automatically

ユーザーが「保存して」と言わなくても、後の作業で参照しうる資料はすべて保存対象とする。Backlog 課題・Slack スレッド、Google Doc / Slide、Notion ページ、ローカル PDF / HTML、会議メモや仕様・決定事項などが該当する。保存 Agent の役割はメタデータ登録・本文キャッシュ・タグ付与・要約ジョブの起動までで、要約の生成自体は行わない。

タグ enum と推定ルール（`tag_rules`）の正本は `schema.sql`。クライアント・プロジェクト・チームが分かる場合は `--tag` を付ける。新規 save で `--tag` 未指定時は title から推定する（`tag infer "会議タイトル"` で確認可）。

Google Meet の Gemini 議事録は [Meeting notes sync](#meeting-notes-sync) の手順で自動保存する。`--require-tag` 付き save でタグが推定できない会議は、保存前にユーザーにタグを確認する。

## Layout

```
activecore/
  CLAUDE.md                        # 運用ルール・使い方
  schema.sql                       # DB テーブル定義・タグ seed・推定ルール
  bin/activecore                   # CLI（ディレクトリではなく実行ファイル 1 本）
  bin/meeting-notes-sync-loop      # 議事録同期ループ（平日 10:00–18:30、毎時 :15 / :45）
  bin/sync-meeting-notes.prompt.md # 同期 Agent 向け手順
  db/refs.sqlite                   # 実データ（実行時に自動生成、Git 管理外）
  tmp/                             # 要約処理の一時置き場（tmp/summarize.log にログ）
```

`schema.sql` は DB ファイル `refs.sqlite` とは別物。初回は `init_db` が適用する。seed 更新は `sqlite3 db/refs.sqlite < schema.sql`。要約処理: `save` 時に `--content-file` のコピーを `tmp/{id}.md` に置き、バックグラウンドの `summarize` が Cursor CLI（`agent -p`）に渡す。完了後 `tmp/{id}.md` は削除する。

## CLI

サブコマンド一覧は `activecore --help` を参照。`list` は `query` の alias。`save` 時に `--tag` を付けるとタグは置換される。タグだけ変えるときは `tag add` / `remove` / `set`。

## Save workflow

保存は source の正規化、本文取得、CLI 実行の 3 段階で行う。

### Source format

dedup のため `--source` は次の形式に統一する。

| 種別 | source 形式 |
| :-- | :-- |
| Backlog | `https://{space}.backlog.com/view/{ISSUE_KEY}` |
| Slack | permalink URL |
| Google Doc / Slide | `https://docs.google.com/.../d/{id}/edit`（`save` 時に正規化） |
| Notion | `https://www.notion.so/{pageId}` |
| ローカルファイル | 絶対パス（`save` 時に正規化） |

### Content fetch

| 種別 | 取得方法 |
| :-- | :-- |
| Backlog 課題 | `get_issue` , `get_issue_comments` |
| Slack | `slack_read_thread` / `slack_read_channel` |
| Google Doc / Slide | `read_file_content` |
| Notion | Notion MCP |
| ローカル PDF / HTML | ファイル read |

初回 save または鮮度更新のときだけ fetch する。以降の参照は `get`。本文を一時ファイルに書き `save` を実行する。戻り値は uuid（`id`）。要約はバックグラウンドで自動起動される。保存 Agent の作業はここで終了する。

## Meeting notes sync

終了済みカレンダーイベントに添付された Gemini 議事録を、Google Calendar MCP + Google Drive MCP 経由で SQLite に登録する。

### 手順

1. Google Calendar MCP `list_events`
   - `calendarId`: `y.nakamura@activecore.jp`（primary でも可）
   - `startTime`: 過去 7 日（初回・取りこぼしは 365 日）
   - `endTime`: 現在時刻 − 30 分（終了済みのみ）
   - `orderBy`: `startTime`

2. 各イベントの `attachments` を確認
   - `title` が `Gemini によるメモ` の `fileUrl` から doc ID を抽出
   - Meet 録画のみで Gemini 添付が無いイベントはスキップ

3. 未登録のみ処理
   - `source`: `https://docs.google.com/document/d/{docId}/edit`
   - 同一 doc ID が `refs.source` にあればスキップ（`LIKE '%/document/d/{docId}/%'`）

4. Google Drive MCP `read_file_content` で本文取得 → 一時ファイルへ書き出し

5. `activecore save --require-tag`（タイトルはイベント `summary`。title からタグ推定）

```bash
~/activecore/bin/activecore save \
  --title "$summary" \
  --source "https://docs.google.com/document/d/{docId}/edit" \
  --content-file /tmp/activecore-meeting-{docId}.md \
  --require-tag
```

`--require-tag` でタグ推定に失敗した場合、Agent はユーザーにタグを確認してから `--tag` を付けて save する。推測でタグを付けない。

### 定期実行（平日 10:00–18:30、毎時 :15 / :45）

Google MCP は Cursor IDE の user plugin 経由のみ動作するため、launchd / cron は使わない。Cursor Agent セッション内で次を起動する。

```bash
~/activecore/bin/meeting-notes-sync-loop watchdog  # 推奨: 自動再起動付き（平日 10:00–18:30、毎時15分・45分）
~/activecore/bin/meeting-notes-sync-loop stop       # 停止
~/activecore/bin/meeting-notes-sync-loop status
```

`watchdog` が loop を監視し、5分ごとに死活確認して停止時は自動再起動する。Agent は `AGENT_LOOP_TICK_meeting_notes_sync` を受けて上記手順を実行する。

## Notes

`summary` が `(生成中)` の場合、要約ジョブ実行中。同じ `source` を再 save すると upsert され、本文・要約が更新される。
