-- Lumiere schema

CREATE TABLE IF NOT EXISTS reference (
  id         TEXT PRIMARY KEY,
  title      TEXT NOT NULL,
  content    TEXT,
  source     TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- 共通語彙（terms 系テーブル）
-- category: client | meeting | person | project | process | team | system | meta

CREATE TABLE IF NOT EXISTS terms (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  category    TEXT NOT NULL CHECK (category IN (
    'client', 'person', 'project', 'process', 'team', 'system', 'meeting', 'meta'
  )),
  description TEXT,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  UNIQUE (name, category)
);

-- 別名・タイトルマッチ用パターン（旧 tag_rules を統合）
CREATE TABLE IF NOT EXISTS term_aliases (
  term_id TEXT NOT NULL,
  alias   TEXT NOT NULL,
  PRIMARY KEY (term_id, alias),
  FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reference_terms (
  reference_id TEXT NOT NULL,
  term_id      TEXT NOT NULL,
  PRIMARY KEY (reference_id, term_id),
  FOREIGN KEY (reference_id) REFERENCES reference(id) ON DELETE CASCADE,
  FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS term_relations (
  from_id    TEXT NOT NULL,
  to_id      TEXT NOT NULL,
  relation   TEXT NOT NULL CHECK (relation IN (
    'member_of', 'works_for', 'part_of', 'uses', 'alias_of'
  )),
  PRIMARY KEY (from_id, to_id, relation),
  FOREIGN KEY (from_id) REFERENCES terms(id) ON DELETE CASCADE,
  FOREIGN KEY (to_id) REFERENCES terms(id) ON DELETE CASCADE
);

-- クライアント
INSERT OR IGNORE INTO terms (id, name, category, description, created_at, updated_at) VALUES
  ('client-hankyu-kotsu', '阪急交通社', 'client', 'クライアント。表記ゆれ: 阪急', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('client-triples', 'トリプルエス', 'client', 'クライアント。表記ゆれ: トリプルS', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('client-sabon', 'SABON', 'client', 'クライアント', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('client-kinari', 'キナリ', 'client', 'クライアント', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('client-shiseido', '資生堂', 'client', 'クライアント', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('client-aeonpet', 'イオンペット', 'client', 'クライアント', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900');

INSERT OR IGNORE INTO term_aliases (term_id, alias) VALUES
  ('client-hankyu-kotsu', '阪急'),
  ('client-triples', 'トリプルS'),
  ('client-shiseido', 'エリクシール'),
  ('client-kinari', '草花木果');

-- チーム・プロジェクト
INSERT OR IGNORE INTO terms (id, name, category, description, created_at, updated_at) VALUES
  ('team-marukeops', 'マーケOps', 'team', 'ActiveCore マーケティング Ops チーム', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('team-fde', 'FDE', 'team', 'Forward Deployed Engineering', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('team-isms', 'ISMS', 'team', '情報セキュリティ管理', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('team-career', 'キャリア', 'meta', '評価・査定・キャリア面談', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('project-poc', 'PoC型化', 'project', 'PoC の型化検討', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('project-marutto', 'marutto', 'project', 'marutto 1to1 定例・制作オペレーション', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('project-nb', 'ナラティブベース', 'team', '制作委託先チーム。ナラマケ案件を含む', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900');

INSERT OR IGNORE INTO term_aliases (term_id, alias) VALUES
  ('team-marukeops', 'Ops'),
  ('project-nb', 'NB'),
  ('project-nb', 'ナラマケ');

-- 会議（旧 tag_rules の定例名）
INSERT OR IGNORE INTO terms (id, name, category, description, created_at, updated_at) VALUES
  ('meeting-fde-daily', 'FDEデイリー', 'meeting', 'FDE デイリー', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-marukeops-weekly', '[マーケOps] Weekly MTG', 'meeting', 'マーケOps 週次', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-1on1', '1on1', 'meeting', '1on1', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-nb-naramake', '課題確認の定例会（NBナラマケ-AC）', 'meeting', 'NB 課題確認', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-ops-cost', 'Opsコスト削減に向けた議論', 'meeting', 'Ops コスト削減議論', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-fde-kai', 'FDE会', 'meeting', 'FDE会', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-isms', '情報セキュリティ委員会', 'meeting', 'ISMS 委員会', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-kinari-internal', 'キナリ様内部定例', 'meeting', 'キナリ内部定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-sabon-ops', '[SABON様] Ops定例', 'meeting', 'SABON Ops 定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-kinari-marutto', '【Marutto 1to1】キナリ様定例', 'meeting', 'キナリ marutto 定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-marutto-daily', 'maruttoデイリー', 'meeting', 'marutto デイリー', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-poc', '【Opsチーム】PoCの型化検討分科会', 'meeting', 'PoC 型化分科会', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-marutto-planning', 'maruttoチームプランニング-ops', 'meeting', 'marutto プランニング', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-shiseido-internal', '【Meet】 エリクシールmarutto内部定例', 'meeting', 'エリクシール内部定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-shiseido-mtg', '資生堂/エリクシール様　制作定期MTG', 'meeting', 'エリクシール制作 MTG', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-shiseido-1to1', 'Marutto1to1定例', 'meeting', 'エリクシール marutto 定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-shiseido-wrap', '[Meet]エリクシールmaruttoラップアップ', 'meeting', 'エリクシールラップアップ', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-shiseido-ac', 'エリクシール AC内部定例', 'meeting', 'エリクシール AC 内部定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-aeonpet-internal', 'イオンペットさま内部定例', 'meeting', 'イオンペット内部定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-aeonpet-1to1', '【社外/Meet】イオンペットさま 定例（marutto1to1）', 'meeting', 'イオンペット定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-sabon-1to1', '【Marutto1to1】SABONさま定例', 'meeting', 'SABON 定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-sabon-internal', 'SABON内部定例', 'meeting', 'SABON 内部定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-hankyu-teirei', '確定：阪急さま定例', 'meeting', '阪急定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('meeting-triples-teirei', '確定：トリプルエスさま定例', 'meeting', 'トリプルエス定例', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900');

INSERT OR IGNORE INTO term_relations (from_id, to_id, relation) VALUES
  ('meeting-fde-daily', 'team-fde', 'part_of'),
  ('meeting-marukeops-weekly', 'team-marukeops', 'part_of'),
  ('meeting-1on1', 'team-fde', 'part_of'),
  ('meeting-nb-naramake', 'project-nb', 'part_of'),
  ('meeting-ops-cost', 'team-marukeops', 'part_of'),
  ('meeting-fde-kai', 'team-fde', 'part_of'),
  ('meeting-isms', 'team-isms', 'part_of'),
  ('meeting-kinari-internal', 'client-kinari', 'part_of'),
  ('meeting-sabon-ops', 'client-sabon', 'part_of'),
  ('meeting-kinari-marutto', 'client-kinari', 'part_of'),
  ('meeting-marutto-daily', 'project-marutto', 'part_of'),
  ('meeting-poc', 'project-poc', 'part_of'),
  ('meeting-shiseido-internal', 'client-shiseido', 'part_of'),
  ('meeting-shiseido-mtg', 'client-shiseido', 'part_of'),
  ('meeting-shiseido-1to1', 'client-shiseido', 'part_of'),
  ('meeting-shiseido-wrap', 'client-shiseido', 'part_of'),
  ('meeting-shiseido-ac', 'client-shiseido', 'part_of'),
  ('meeting-aeonpet-internal', 'client-aeonpet', 'part_of'),
  ('meeting-aeonpet-1to1', 'client-aeonpet', 'part_of'),
  ('meeting-sabon-1to1', 'client-sabon', 'part_of'),
  ('meeting-sabon-internal', 'client-sabon', 'part_of'),
  ('meeting-hankyu-teirei', 'client-hankyu-kotsu', 'part_of'),
  ('meeting-triples-teirei', 'client-triples', 'part_of');

-- 業務工程
INSERT OR IGNORE INTO terms (id, name, category, description, created_at, updated_at) VALUES
  ('proc-planning', 'プランニング', 'process', '① 企画・プランニング', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-json-creative', 'JSONクリエイティブ企画書', 'process', '② 制作: JSON 企画書作成', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-html', 'HTML制作', 'process', '② 制作: build-html-tool による HTML 制作', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-banner', 'バナー制作', 'process', '② 制作: Image Agent によるバナー制作', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-revision', '修正対応', 'process', '② 制作: 修正対応', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-html-review', 'HTMLレビュー', 'process', '③ レビュー: HTML レビュー AG', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-banner-review', 'バナーレビュー', 'process', '③ レビュー: バナーチェックリスト採点', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-delivery', '配信設定', 'process', '④ 配信', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-metrics', '数値集計', 'process', '⑤ レポーティング: 数値集計', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-report', 'レポート作成', 'process', '⑤ レポーティング: 定例資料作成', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-task-mgmt', 'タスク作成・進行管理', 'process', '⑥ ディレクション', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-direction', '制作ディレクション・窓口', 'process', '⑥ ディレクション: 窓口', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('proc-improvement', '業務整理', 'process', '⑥ 分析・提案・改善', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900');

-- 人物
INSERT OR IGNORE INTO terms (id, name, category, description, created_at, updated_at) VALUES
  ('person-nagata', '永田', 'person', 'NB: プランニング・レポート', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('person-komatsu', '小松', 'person', 'NB: HTML 制作', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('person-asakura', '浅倉', 'person', 'NB/Ops: バナー制作・レビュー', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('person-fujikawa', '藤川', 'person', 'NB: 修正対応', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('person-tanaka', '田中', 'person', 'NB: HTML レビュー・数値集計', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('person-yamagami', '山上', 'person', 'NB: タスク管理・ディレクション', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900');

INSERT OR IGNORE INTO term_relations (from_id, to_id, relation) VALUES
  ('person-nagata', 'project-nb', 'works_for'),
  ('person-komatsu', 'project-nb', 'works_for'),
  ('person-asakura', 'project-nb', 'works_for'),
  ('person-fujikawa', 'project-nb', 'works_for'),
  ('person-tanaka', 'project-nb', 'works_for'),
  ('person-yamagami', 'project-nb', 'works_for'),
  ('person-nagata', 'proc-planning', 'part_of'),
  ('person-komatsu', 'proc-html', 'part_of'),
  ('person-asakura', 'proc-banner', 'part_of'),
  ('person-fujikawa', 'proc-revision', 'part_of'),
  ('person-tanaka', 'proc-html-review', 'part_of'),
  ('person-yamagami', 'proc-task-mgmt', 'part_of'),
  ('proc-html', 'client-triples', 'part_of'),
  ('proc-banner', 'client-triples', 'part_of'),
  ('proc-revision', 'client-triples', 'part_of');

-- システム（旧 tool）
INSERT OR IGNORE INTO terms (id, name, category, description, created_at, updated_at) VALUES
  ('system-build-html', 'build-html-tool', 'system', 'Mastra ベース HTML 制作ツール', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('system-image-agent', 'Image Agent', 'system', 'Mastra ベースバナー制作', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('system-notebooklm', 'NotebookLM', 'system', 'プランニング試行中', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('system-karte', 'KARTE', 'system', '配信プラットフォーム', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('system-backlog', 'Backlog', 'system', '課題・タスク管理', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900'),
  ('system-html-review-ag', 'HTMLレビュー担当AG', 'system', 'HTML レビュー自動化 AG', '2026-01-01T00:00:00+0900', '2026-01-01T00:00:00+0900');

INSERT OR IGNORE INTO term_relations (from_id, to_id, relation) VALUES
  ('proc-html', 'system-build-html', 'uses'),
  ('proc-banner', 'system-image-agent', 'uses'),
  ('proc-planning', 'system-notebooklm', 'uses'),
  ('proc-delivery', 'system-karte', 'uses'),
  ('proc-task-mgmt', 'system-backlog', 'uses'),
  ('proc-html-review', 'system-html-review-ag', 'uses');

