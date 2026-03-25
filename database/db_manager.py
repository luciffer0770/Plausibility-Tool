"""SQLite access: connection, migrations, CRUD."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Iterable, Optional

from core.models import EngineType, LimitDefinition, ParameterType, Project

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = 2


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


class DatabaseManager:
    """Application database."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or (_project_root() / "pruf_data.db")
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Open connection and run migrations."""
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            self._migrate()
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @contextmanager
    def cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = self.connect()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def _migrate(self) -> None:
        schema_file = Path(__file__).resolve().parent / "schema.sql"
        sql = schema_file.read_text(encoding="utf-8")
        self._conn.executescript(sql)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        row = self._conn.execute(
            "SELECT value FROM app_meta WHERE key = 'schema_version'"
        ).fetchone()
        ver = int(row["value"]) if row else 0
        if ver < _SCHEMA_VERSION:
            if ver < 2:
                try:
                    self._conn.execute(
                        "ALTER TABLE limit_profiles ADD COLUMN is_enabled INTEGER DEFAULT 1"
                    )
                except sqlite3.OperationalError:
                    pass
            self._conn.execute(
                "INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)",
                ("schema_version", str(_SCHEMA_VERSION)),
            )
            self._conn.commit()

    # --- Projects ---

    def insert_project(self, project: Project) -> int:
        with self.cursor() as c:
            c.execute(
                """
                INSERT INTO projects (name, engine_type, engine_variant, test_bed_id, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    project.name,
                    project.engine_type.value,
                    project.engine_variant or "",
                    project.test_bed_id or "",
                    1 if project.is_active else 0,
                ),
            )
            return int(c.lastrowid)

    def update_project(self, project: Project) -> None:
        if project.id is None:
            raise ValueError("project.id required")
        with self.cursor() as c:
            c.execute(
                """
                UPDATE projects SET name=?, engine_type=?, engine_variant=?,
                test_bed_id=?, updated_at=CURRENT_TIMESTAMP, is_active=?
                WHERE id=?
                """,
                (
                    project.name,
                    project.engine_type.value,
                    project.engine_variant or "",
                    project.test_bed_id or "",
                    1 if project.is_active else 0,
                    project.id,
                ),
            )

    def list_projects(self, active_only: bool = True) -> list[Project]:
        with self.cursor() as c:
            q = "SELECT * FROM projects"
            if active_only:
                q += " WHERE is_active=1"
            q += " ORDER BY updated_at DESC, created_at DESC"
            rows = c.execute(q).fetchall()
        return [self._row_to_project(r) for r in rows]

    def get_project(self, project_id: int) -> Optional[Project]:
        with self.cursor() as c:
            row = c.execute(
                "SELECT * FROM projects WHERE id=?", (project_id,)
            ).fetchone()
        return self._row_to_project(row) if row else None

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        et = EngineType.TURBO_4CYL
        for e in EngineType:
            if e.value == row["engine_type"]:
                et = e
                break
        return Project(
            id=row["id"],
            name=row["name"],
            engine_type=et,
            engine_variant=row["engine_variant"] or "",
            test_bed_id=row["test_bed_id"] or "",
            created_at=self._parse_ts(row["created_at"]),
            updated_at=self._parse_ts(row["updated_at"]),
            is_active=bool(row["is_active"]),
        )

    @staticmethod
    def _parse_ts(val: Any) -> Optional[datetime]:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        except ValueError:
            return None

    def project_upload_stats(self, project_id: int) -> dict[str, Any]:
        with self.cursor() as c:
            cnt = c.execute(
                "SELECT COUNT(*) AS n FROM upload_sessions WHERE project_id=?",
                (project_id,),
            ).fetchone()["n"]
            last = c.execute(
                """
                SELECT * FROM upload_sessions WHERE project_id=?
                ORDER BY upload_date DESC LIMIT 1
                """,
                (project_id,),
            ).fetchone()
        total_pass = 0
        total_meas = 0
        if last:
            with self.cursor() as c:
                agg = c.execute(
                    """
                    SELECT status, COUNT(*) AS n FROM measurements
                    WHERE session_id=? GROUP BY status
                    """,
                    (last["id"],),
                ).fetchall()
            for a in agg:
                total_meas += a["n"]
                if a["status"] == "OK":
                    total_pass += a["n"]
        pass_pct = round(100.0 * total_pass / total_meas, 1) if total_meas else None
        return {
            "upload_count": cnt,
            "last_session_id": last["id"] if last else None,
            "last_upload_date": last["upload_date"] if last else None,
            "last_pass_pct": pass_pct,
        }

    # --- Limit profiles ---

    def replace_limit_profile(
        self, engine_type: str, definitions: Iterable[LimitDefinition]
    ) -> None:
        with self.cursor() as c:
            c.execute("DELETE FROM limit_profiles WHERE engine_type=?", (engine_type,))
            for d in definitions:
                c.execute(
                    """
                    INSERT INTO limit_profiles (
                        engine_type, parameter_name, parameter_type, unit,
                        lower_limit, upper_limit, warning_pct, root_cause,
                        corrective_action, description, is_required, is_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        engine_type,
                        d.parameter_name,
                        d.parameter_type.value,
                        d.unit or "",
                        d.lower_limit,
                        d.upper_limit,
                        d.warning_pct,
                        d.root_cause or "",
                        d.corrective_action or "",
                        d.description or "",
                        1 if d.is_required else 0,
                        1 if d.is_enabled else 0,
                    ),
                )

    def get_limit_profile(self, engine_type: str) -> list[LimitDefinition]:
        with self.cursor() as c:
            rows = c.execute(
                """
                SELECT * FROM limit_profiles WHERE engine_type=?
                ORDER BY parameter_name
                """,
                (engine_type,),
            ).fetchall()
        out: list[LimitDefinition] = []
        for r in rows:
            pt = ParameterType.OTHER
            for p in ParameterType:
                if p.value == r["parameter_type"]:
                    pt = p
                    break
            out.append(
                LimitDefinition(
                    parameter_name=r["parameter_name"],
                    parameter_type=pt,
                    description=r["description"] or "",
                    unit=r["unit"] or "",
                    lower_limit=r["lower_limit"],
                    upper_limit=r["upper_limit"],
                    warning_pct=float(r["warning_pct"] or 10.0),
                    root_cause=r["root_cause"] or "",
                    corrective_action=r["corrective_action"] or "",
                    is_required=bool(r["is_required"]),
                    is_enabled=bool(r["is_enabled"]) if "is_enabled" in r else True,
                )
            )
        return out

    def list_engine_types_with_profiles(self) -> list[str]:
        with self.cursor() as c:
            rows = c.execute(
                "SELECT DISTINCT engine_type FROM limit_profiles ORDER BY engine_type"
            ).fetchall()
        return [r["engine_type"] for r in rows]

    # --- Upload sessions ---

    def insert_upload_session(
        self,
        project_id: int,
        file_name: str,
        file_path: Optional[str],
        record_count: int,
        pass_count: int,
        warn_count: int,
        fail_count: int,
    ) -> int:
        with self.cursor() as c:
            c.execute(
                """
                INSERT INTO upload_sessions (
                    project_id, file_name, file_path, record_count,
                    pass_count, warn_count, fail_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    file_name,
                    file_path,
                    record_count,
                    pass_count,
                    warn_count,
                    fail_count,
                ),
            )
            return int(c.lastrowid)

    def update_upload_session_counts(
        self,
        session_id: int,
        record_count: int,
        pass_count: int,
        warn_count: int,
        fail_count: int,
    ) -> None:
        with self.cursor() as c:
            c.execute(
                """
                UPDATE upload_sessions SET record_count=?, pass_count=?,
                warn_count=?, fail_count=? WHERE id=?
                """,
                (record_count, pass_count, warn_count, fail_count, session_id),
            )

    def list_upload_sessions(self, project_id: int, limit: int = 50) -> list[dict[str, Any]]:
        with self.cursor() as c:
            rows = c.execute(
                """
                SELECT * FROM upload_sessions WHERE project_id=?
                ORDER BY upload_date DESC LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_upload_session(self, session_id: int) -> Optional[dict[str, Any]]:
        with self.cursor() as c:
            row = c.execute(
                "SELECT * FROM upload_sessions WHERE id=?", (session_id,)
            ).fetchone()
        return dict(row) if row else None

    # --- Measurements ---

    def insert_measurements_batch(
        self, rows: list[tuple[Any, ...]]
    ) -> None:
        if not rows:
            return
        with self.cursor() as c:
            c.executemany(
                """
                INSERT INTO measurements (
                    session_id, parameter_name, measured_value,
                    value_min, value_max, value_avg, value_type,
                    timestamp, status, deviation, limit_lower, limit_upper,
                    root_cause, corrective_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def delete_measurements_for_session(self, session_id: int) -> None:
        with self.cursor() as c:
            c.execute("DELETE FROM measurements WHERE session_id=?", (session_id,))

    def get_measurements_for_session(self, session_id: int) -> list[dict[str, Any]]:
        with self.cursor() as c:
            rows = c.execute(
                """
                SELECT * FROM measurements WHERE session_id=?
                ORDER BY parameter_name
                """,
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_measurements_history(
        self, project_id: int, parameter_name: str
    ) -> list[dict[str, Any]]:
        with self.cursor() as c:
            rows = c.execute(
                """
                SELECT m.*, u.upload_date, u.file_name
                FROM measurements m
                JOIN upload_sessions u ON u.id = m.session_id
                WHERE u.project_id = ? AND m.parameter_name = ?
                ORDER BY u.upload_date ASC
                """,
                (project_id, parameter_name),
            ).fetchall()
        return [dict(r) for r in rows]

    def aggregate_status_by_session(self, project_id: int) -> list[dict[str, Any]]:
        with self.cursor() as c:
            rows = c.execute(
                """
                SELECT u.id, u.upload_date, u.file_name,
                    SUM(CASE WHEN m.status='OK' THEN 1 ELSE 0 END) AS ok_n,
                    SUM(CASE WHEN m.status='WARNING' THEN 1 ELSE 0 END) AS warn_n,
                    SUM(CASE WHEN m.status='FAIL' THEN 1 ELSE 0 END) AS fail_n,
                    SUM(CASE WHEN m.status='NO_DATA' THEN 1 ELSE 0 END) AS nd_n
                FROM upload_sessions u
                LEFT JOIN measurements m ON m.session_id = u.id
                WHERE u.project_id = ?
                GROUP BY u.id
                ORDER BY u.upload_date DESC
                LIMIT 30
                """,
                (project_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def top_failing_parameters(self, project_id: int, limit: int = 5) -> list[dict[str, Any]]:
        with self.cursor() as c:
            rows = c.execute(
                """
                SELECT m.parameter_name, SUM(CASE WHEN m.status='FAIL' THEN 1 ELSE 0 END) AS fails
                FROM measurements m
                JOIN upload_sessions u ON u.id = m.session_id
                WHERE u.project_id = ?
                GROUP BY m.parameter_name
                HAVING fails > 0
                ORDER BY fails DESC
                LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
