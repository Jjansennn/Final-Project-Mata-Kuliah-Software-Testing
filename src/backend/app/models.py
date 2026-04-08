import sqlite3
import os

DATABASE = os.environ.get("DATABASE", "database.db")


class TaskNotFoundError(Exception):
    pass


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER  PRIMARY KEY AUTOINCREMENT,
            email         TEXT     NOT NULL UNIQUE,
            password_hash TEXT     NOT NULL,
            created_at    DATETIME NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER  PRIMARY KEY AUTOINCREMENT,
            title       TEXT     NOT NULL,
            description TEXT,
            status      TEXT     NOT NULL DEFAULT 'pending',
            created_at  DATETIME NOT NULL,
            updated_at  DATETIME NOT NULL
        );
    """)
    # Safe migration: add deadline and user_id columns if they don't exist
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN deadline DATETIME")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN user_id INTEGER")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def insert_user(email: str, password_hash: str, created_at) -> int:
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
        (email, password_hash, created_at),
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def fetch_user_by_email(email: str) -> dict | None:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def fetch_user_by_id(user_id: int) -> dict | None:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_task(title, description, status, deadline, user_id, created_at, updated_at) -> int:
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, description, status, deadline, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, description, status, deadline, user_id, created_at, updated_at),
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def fetch_all_tasks(user_id=None) -> list:
    conn = get_db_connection()
    if user_id is not None:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_task_by_id(task_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_task_fields(task_id: int, fields: dict):
    if not fields:
        return fetch_task_by_id(task_id)
    set_clause = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [task_id]
    conn = get_db_connection()
    conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_task_by_id(task_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
