SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    fetched_at  REAL NOT NULL,
    expires_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS subscribers (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_state (
    match_id        INTEGER PRIMARY KEY,
    home_score      INTEGER NOT NULL DEFAULT 0,
    away_score      INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL,
    home_team       TEXT NOT NULL,
    away_team       TEXT NOT NULL,
    last_alerted_at REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS api_budget (
    date        TEXT PRIMARY KEY,
    used        INTEGER NOT NULL DEFAULT 0,
    limit_day   INTEGER NOT NULL DEFAULT 100
);

CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(active);
"""
