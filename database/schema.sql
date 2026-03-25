-- PRÜF SQLite schema

CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    engine_type     TEXT NOT NULL,
    engine_variant  TEXT,
    test_bed_id     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active       INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS limit_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    engine_type         TEXT NOT NULL,
    parameter_name      TEXT NOT NULL,
    parameter_type      TEXT NOT NULL,
    unit                TEXT,
    lower_limit         REAL,
    upper_limit         REAL,
    warning_pct         REAL DEFAULT 10.0,
    root_cause          TEXT,
    corrective_action   TEXT,
    description         TEXT,
    is_required         INTEGER DEFAULT 0,
    is_enabled          INTEGER DEFAULT 1,
    UNIQUE(engine_type, parameter_name)
);

CREATE TABLE IF NOT EXISTS upload_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL,
    file_name       TEXT NOT NULL,
    file_path       TEXT,
    upload_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_count    INTEGER,
    pass_count      INTEGER,
    warn_count      INTEGER,
    fail_count      INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS measurements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL,
    parameter_name  TEXT NOT NULL,
    measured_value  REAL,
    value_min       REAL,
    value_max       REAL,
    value_avg       REAL,
    value_type      TEXT DEFAULT 'instant',
    timestamp       TEXT,
    status          TEXT NOT NULL,
    deviation       REAL,
    limit_lower     REAL,
    limit_upper     REAL,
    root_cause      TEXT,
    corrective_action TEXT,
    FOREIGN KEY (session_id) REFERENCES upload_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_measurements_session ON measurements(session_id);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_project ON upload_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_limit_profiles_engine ON limit_profiles(engine_type);
