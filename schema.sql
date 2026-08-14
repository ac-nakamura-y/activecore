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
  ('品質管理エージェント', 'project'),
  ('マーケOps', 'team'),
  ('FDE', 'team');
