CREATE TABLE IF NOT EXISTS refs (
  id         TEXT PRIMARY KEY,
  title      TEXT NOT NULL,
  summary    TEXT,
  content    TEXT,
  source     TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
  name     TEXT PRIMARY KEY,
  category TEXT NOT NULL CHECK (category IN ('client', 'project', 'team'))
);

CREATE TABLE IF NOT EXISTS ref_tags (
  ref_id TEXT NOT NULL,
  tag    TEXT NOT NULL,
  PRIMARY KEY (ref_id, tag),
  FOREIGN KEY (ref_id) REFERENCES refs(id) ON DELETE CASCADE,
  FOREIGN KEY (tag) REFERENCES tags(name)
);

INSERT OR IGNORE INTO tags (name, category) VALUES
  ('阪急交通社', 'client'),
  ('トリプルエス', 'client'),
  ('SABON', 'client'),
  ('キナリ', 'client'),
  ('資生堂', 'client'),
  ('イオンペット', 'client'),
  ('PoC型化', 'project'),
  ('マーケOps', 'team'),
  ('FDE', 'team'),
  ('ISMS', 'team');

CREATE TABLE IF NOT EXISTS tag_rules (
  tag     TEXT NOT NULL,
  pattern TEXT NOT NULL,
  PRIMARY KEY (tag, pattern),
  FOREIGN KEY (tag) REFERENCES tags(name)
);

DELETE FROM tag_rules;

INSERT INTO tag_rules (tag, pattern) VALUES
  -- FDE
  ('FDE', 'FDE'),
  ('FDE', 'FDEデイリー'),
  ('FDE', '[マーケOps] Weekly MTG'),
  ('FDE', '1on1'),
  ('FDE', '課題確認の定例会（NBナラマケ-AC）'),
  ('FDE', 'Opsコスト削減に向けた議論'),
  ('FDE', 'FDE会'),
  -- ISMS
  ('ISMS', 'ISMS'),
  ('ISMS', '情報セキュリティ委員会'),
  -- キナリ
  ('キナリ', 'キナリ'),
  ('キナリ', 'キナリ様内部定例'),
  ('キナリ', '[SABON様] Ops定例'),
  ('キナリ', '【Marutto 1to1】キナリ様定例'),
  -- マーケOps
  ('マーケOps', 'マーケOps'),
  ('マーケOps', 'Ops'),
  ('マーケOps', 'maruttoデイリー'),
  ('マーケOps', '[マーケOps] Weekly MTG'),
  ('マーケOps', '課題確認の定例会（NBナラマケ-AC）'),
  ('マーケOps', 'Opsコスト削減に向けた議論'),
  ('マーケOps', '【Opsチーム】PoCの型化検討分科会'),
  ('マーケOps', '[SABON様] Ops定例'),
  ('マーケOps', 'maruttoチームプランニング-ops'),
  -- 資生堂
  ('資生堂', '資生堂'),
  ('資生堂', 'エリクシール'),
  ('資生堂', '【Meet】 エリクシールmarutto内部定例'),
  ('資生堂', '資生堂/エリクシール様　制作定期MTG'),
  ('資生堂', 'Marutto1to1定例'),
  ('資生堂', '[Meet]エリクシールmaruttoラップアップ'),
  ('資生堂', 'エリクシール AC内部定例'),
  -- イオンペット
  ('イオンペット', 'イオンペット'),
  ('イオンペット', 'イオンペットさま内部定例'),
  ('イオンペット', '【社外/Meet】イオンペットさま 定例（marutto1to1）'),
  -- SABON
  ('SABON', 'SABON'),
  ('SABON', '【Marutto1to1】SABONさま定例'),
  ('SABON', 'SABON内部定例'),
  ('SABON', '[SABON様] Ops定例'),
  -- 阪急交通社
  ('阪急交通社', '阪急交通社'),
  ('阪急交通社', '[マーケOps] Weekly MTG'),
  ('阪急交通社', '確定：阪急さま定例'),
  -- トリプルエス
  ('トリプルエス', 'トリプルエス'),
  ('トリプルエス', '課題確認の定例会（NBナラマケ-AC）'),
  ('トリプルエス', '確定：トリプルエスさま定例');
