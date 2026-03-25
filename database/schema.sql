-- Bosch Plausibility Check Tool — SQLite schema (v3)

CREATE TABLE IF NOT EXISTS engine_types (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    engine_type     TEXT NOT NULL,
    engine_variant  TEXT,
    engine_code     TEXT,
    test_bed_id     TEXT,
    customer_oem    TEXT,
    emission_norm   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active       INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS limit_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    engine_type         TEXT NOT NULL,
    parameter_name      TEXT NOT NULL,
    parameter_type      TEXT NOT NULL,
    category            TEXT,
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
    version_test    TEXT,
    application     TEXT,
    datum           TEXT,
    record_count    INTEGER,
    pass_count      INTEGER,
    warn_count      INTEGER,
    fail_count      INTEGER,
    above_count     INTEGER DEFAULT 0,
    below_count     INTEGER DEFAULT 0,
    nodata_count    INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS measurements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL,
    parameter_name  TEXT NOT NULL,
    description     TEXT,
    category        TEXT,
    param_type      TEXT,
    unit            TEXT,
    num_runs        INTEGER,
    measured_value  REAL,
    value_min       REAL,
    value_max       REAL,
    value_avg       REAL,
    value_type      TEXT DEFAULT 'aggregate',
    timestamp       TEXT,
    status          TEXT NOT NULL,
    deviation       REAL,
    limit_lower     REAL,
    limit_upper     REAL,
    root_cause      TEXT,
    corrective_action TEXT,
    values_sample TEXT,
    FOREIGN KEY (session_id) REFERENCES upload_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_measurements_session ON measurements(session_id);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_project ON upload_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_limit_profiles_engine ON limit_profiles(engine_type);

INSERT OR IGNORE INTO engine_types (name, description) VALUES
    ('Turbo 4-Cyl', 'Turbocharged 4-cylinder'),
    ('NA 4-Cyl', 'Naturally aspirated 4-cylinder'),
    ('Turbo 6-Cyl', 'Turbocharged 6-cylinder'),
    ('NA 6-Cyl', 'Naturally aspirated 6-cylinder'),
    ('Diesel CR', 'Common rail diesel'),
    ('Hybrid', 'Hybrid powertrain');
