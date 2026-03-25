#!/usr/bin/env python3
"""
Run PRÜF plausibility without the Tk GUI (Codespaces / CI / SSH).

Examples:
  python3 scripts/cli_plausibility.py list-projects
  python3 scripts/cli_plausibility.py run --project-id 1 --file ./sample.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repo root on path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.analysis_service import run_plausibility_for_file
from core.data_loader import detect_column_mapping, load_dataframe
from core.models import EngineType, Project
from core.profile_manager import ensure_default_profile
from database.db_manager import DatabaseManager


def cmd_list_projects(db: DatabaseManager) -> int:
    rows = db.list_projects()
    if not rows:
        print("No projects. Create one with the GUI or insert into SQLite.")
        return 0
    print(f"{'ID':>4}  {'Name':<32}  {'Engine':<22}  Test bed")
    print("-" * 80)
    for p in rows:
        print(
            f"{p.id or 0:>4}  {p.name[:32]:<32}  {p.engine_type.value[:22]:<22}  {p.test_bed_id or '—'}"
        )
    return 0


def cmd_create_project(
    db: DatabaseManager,
    name: str,
    engine: str,
    test_bed: str,
) -> int:
    et = EngineType.TURBO_4CYL
    for e in EngineType:
        if e.value == engine:
            et = e
            break
    proj = Project(name=name, engine_type=et, test_bed_id=test_bed)
    pid = db.insert_project(proj)
    ensure_default_profile(db, et.value)
    print(f"Created project id={pid}  ({name})")
    return 0


def cmd_run(db: DatabaseManager, project_id: int, file_path: Path) -> int:
    proj = db.get_project(project_id)
    if not proj:
        print(f"Error: project id {project_id} not found.", file=sys.stderr)
        return 1
    ensure_default_profile(db, proj.engine_type.value)
    fp = Path(file_path).resolve()
    if not fp.is_file():
        print(f"Error: file not found: {fp}", file=sys.stderr)
        return 1

    df = load_dataframe(fp)
    mapping = detect_column_mapping(df)
    if not mapping.get("mappings"):
        print("Error: no parameter columns detected. Check headers.", file=sys.stderr)
        return 1

    sid = run_plausibility_for_file(
        db,
        project_id,
        proj.engine_type.value,
        fp,
        mapping.get("timestamp_col"),
        mapping["mappings"],
        file_name=fp.name,
    )
    meas = db.get_measurements_for_session(sid)
    print(f"Session id: {sid}  |  Parameters: {len(meas)}")
    print(f"{'Status':<10}  {'Param':<12}  {'Value':>10}  Root cause")
    print("-" * 70)
    for m in sorted(meas, key=lambda x: (x.get("status", ""), x.get("parameter_name", ""))):
        v = m.get("measured_value")
        vs = f"{v:.4g}" if v is not None else "—"
        rc = (m.get("root_cause") or "")[:40]
        print(f"{str(m.get('status')):<10}  {str(m.get('parameter_name')):<12}  {vs:>10}  {rc}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="PRÜF CLI (no GUI)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-projects", help="List projects in the database")

    mk = sub.add_parser("create-project", help="Create a project (no GUI)")
    mk.add_argument("--name", required=True)
    mk.add_argument(
        "--engine",
        default=EngineType.TURBO_4CYL.value,
        choices=[e.value for e in EngineType],
    )
    mk.add_argument("--test-bed", default="TB-01")

    runp = sub.add_parser("run", help="Run plausibility on a file")
    runp.add_argument("--project-id", type=int, required=True)
    runp.add_argument("--file", type=Path, required=True)

    args = p.parse_args()
    db = DatabaseManager()
    db.connect()
    try:
        if args.cmd == "list-projects":
            return cmd_list_projects(db)
        if args.cmd == "create-project":
            return cmd_create_project(db, args.name, args.engine, args.test_bed)
        if args.cmd == "run":
            return cmd_run(db, args.project_id, args.file)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
