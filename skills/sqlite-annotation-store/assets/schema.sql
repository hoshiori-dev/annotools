-- annotools annotation store, schema version 1. Conventions: normalized 0-1 coordinates relative to the
-- uncropped source; file pointers only (never binary data).
PRAGMA journal_mode = WAL;
-- foreign_keys is connection-scoped: every client must run `PRAGMA foreign_keys = ON` after connecting.

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id         INTEGER PRIMARY KEY,
    uri        TEXT NOT NULL UNIQUE,          -- local path or fsspec URL
    media_type TEXT NOT NULL CHECK (media_type IN ('image','video','audio')),
    width      INTEGER,
    height     INTEGER,
    duration   REAL,                          -- seconds, for video/audio
    split      TEXT NOT NULL DEFAULT 'train' CHECK (split IN ('train','val','test','unsplit')),
    meta_json  TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY,
    model         TEXT NOT NULL,
    prompt_sha256 TEXT NOT NULL,
    config_json   TEXT DEFAULT '{}',
    started_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    finished_at   TEXT
);

CREATE TABLE IF NOT EXISTS annotations (
    id           INTEGER PRIMARY KEY,
    item_id      INTEGER NOT NULL REFERENCES items(id),
    run_id       INTEGER NOT NULL REFERENCES runs(id),
    kind         TEXT NOT NULL CHECK (kind IN ('bbox','polygon','keypoints','rbox','caption','tag','mask','segment')),
    key          TEXT NOT NULL DEFAULT '',    -- disambiguates several annotations of one kind (index, variant)
    label        TEXT,
    payload_json TEXT NOT NULL,               -- shape depends on kind; see SKILL.md
    confidence   REAL,
    rounds       INTEGER DEFAULT 0,           -- correction rounds used before commit
    status       TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','final','needs_review','rejected')),
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (item_id, run_id, kind, key)
);
CREATE INDEX IF NOT EXISTS idx_annotations_item_run_kind ON annotations(item_id, run_id, kind);

CREATE TABLE IF NOT EXISTS reviews (
    id            INTEGER PRIMARY KEY,
    annotation_id INTEGER NOT NULL REFERENCES annotations(id),
    reviewer      TEXT NOT NULL,
    verdict       TEXT NOT NULL CHECK (verdict IN ('accept','reject','fix')),
    note          TEXT,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TRIGGER IF NOT EXISTS annotations_touch AFTER UPDATE ON annotations
BEGIN
    UPDATE annotations SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = NEW.id;
END;

-- Final annotations: for each (item, kind) the rows of the latest run that produced a final row of that
-- kind, so a caption from run 1 survives a bbox-only run 2.
CREATE VIEW IF NOT EXISTS final_annotations AS
SELECT a.*
FROM annotations a
JOIN (
    SELECT item_id, kind, MAX(run_id) AS run_id
    FROM annotations
    WHERE status = 'final'
    GROUP BY item_id, kind
) latest ON latest.item_id = a.item_id AND latest.kind = a.kind AND latest.run_id = a.run_id
WHERE a.status = 'final';

CREATE VIEW IF NOT EXISTS items_pending AS
SELECT i.*
FROM items i
LEFT JOIN final_annotations f ON f.item_id = i.id
WHERE f.id IS NULL;
