"""Project CRUD helpers."""

from __future__ import annotations

from typing import Any, Optional

from core.models import Project
from database.db_manager import DatabaseManager


def create_project(db: DatabaseManager, project: Project) -> int:
    """Insert project and return id."""
    return db.insert_project(project)


def save_project(db: DatabaseManager, project: Project) -> None:
    """Update existing project."""
    db.update_project(project)


def load_project(db: DatabaseManager, project_id: int) -> Optional[Project]:
    """Fetch project by id."""
    return db.get_project(project_id)


def list_projects_with_stats(db: DatabaseManager) -> list[dict[str, Any]]:
    """Projects with upload stats for landing cards."""
    items: list[dict[str, Any]] = []
    for p in db.list_projects():
        st = db.project_upload_stats(p.id or 0)
        items.append({"project": p, **st})
    return items
