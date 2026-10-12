import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_NAME = "tasks.db"


def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_NAME) -> None:
    """Initializes the SQLite database with required tables."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                is_completed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (user_id, is_completed)"
        )
        conn.commit()


def add_task(user_id: int, title: str, db_path: str = DB_NAME) -> int:
    """Adds a new task for the given user."""
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (user_id, title, is_completed, created_at)
            VALUES (?, ?, 0, ?)
            """,
            (user_id, title.strip(), created_at),
        )
        conn.commit()
        return cursor.lastrowid


def get_active_tasks(user_id: int, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    """Retrieves all incomplete tasks for the given user."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, created_at
            FROM tasks
            WHERE user_id = ? AND is_completed = 0
            ORDER BY id ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_completed_tasks(user_id: int, limit: int = 10, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    """Retrieves recent completed tasks for the given user."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, completed_at
            FROM tasks
            WHERE user_id = ? AND is_completed = 1
            ORDER BY completed_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def complete_task(task_id: int, user_id: int, db_path: str = DB_NAME) -> bool:
    """Marks a task as completed."""
    completed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET is_completed = 1, completed_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (completed_at, task_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_task(task_id: int, user_id: int, db_path: str = DB_NAME) -> bool:
    """Deletes a task completely."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM tasks
            WHERE id = ? AND user_id = ?
            """,
            (task_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_user_stats(user_id: int, db_path: str = DB_NAME) -> Dict[str, Any]:
    """Calculates completion statistics for the user."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_completed = 0 THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
            FROM tasks
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        total = row["total"] or 0
        active = row["active"] or 0
        completed = row["completed"] or 0
        rate = round((completed / total * 100), 1) if total > 0 else 0.0

        return {
            "total": total,
            "active": active,
            "completed": completed,
            "completion_rate": rate,
        }
