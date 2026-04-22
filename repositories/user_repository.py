import sqlite3
from datetime import datetime, timezone
from typing import Optional

from models.user import User

def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db(db_path: str) -> None:
    with _get_conn(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                email           TEXT    NOT NULL UNIQUE,
                password_hash   TEXT    NOT NULL,
                role            TEXT    NOT NULL DEFAULT 'user',
                status          TEXT    NOT NULL DEFAULT 'pending',
                email_verified  INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT    NOT NULL,
                updated_at      TEXT    NOT NULL,
                last_login      TEXT,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until    TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

class UserRepository:
    def __init__(self, db_path: str):
        self._db = db_path

    # ------------------------------------------------------------------ #
    # Leitura
    # ------------------------------------------------------------------ #
    def find_by_id(self, user_id: int) -> Optional[User]:
        with _get_conn(self._db) as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User.from_row(dict(row)) if row else None

    def find_by_email(self, email: str) -> Optional[User]:
        with _get_conn(self._db) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
            ).fetchone()
        return User.from_row(dict(row)) if row else None

    def list_all(self) -> list[User]:
        with _get_conn(self._db) as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [User.from_row(dict(r)) for r in rows]

    # ------------------------------------------------------------------ #
    # Escrita
    # ------------------------------------------------------------------ #
    def create(self, user: User) -> User:
        with _get_conn(self._db) as conn:
            cur = conn.execute(
                """INSERT INTO users
                   (name, email, password_hash, role, status, email_verified,
                    created_at, updated_at, last_login, failed_attempts, locked_until)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (user.name, user.email, user.password_hash, user.role, user.status,
                 int(user.email_verified), user.created_at, user.updated_at,
                 user.last_login, user.failed_attempts, user.locked_until),
            )
            user.id = cur.lastrowid
        return user

    def update(self, user: User) -> None:
        user.updated_at = datetime.now(timezone.utc).isoformat()
        with _get_conn(self._db) as conn:
            conn.execute(
                """UPDATE users SET
                   name=?, email=?, password_hash=?, role=?, status=?,
                   email_verified=?, updated_at=?, last_login=?,
                   failed_attempts=?, locked_until=?
                   WHERE id=?""",
                (user.name, user.email, user.password_hash, user.role, user.status,
                 int(user.email_verified), user.updated_at, user.last_login,
                 user.failed_attempts, user.locked_until, user.id),
            )

    def delete(self, user_id: int) -> None:
        with _get_conn(self._db) as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def email_exists(self, email: str) -> bool:
        with _get_conn(self._db) as conn:
            row = conn.execute(
                "SELECT 1 FROM users WHERE email = ? COLLATE NOCASE", (email,)
            ).fetchone()
        return row is not None
