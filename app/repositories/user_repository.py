import sqlite3
import libsql_experimental as libsql
from datetime import datetime, timezone
from typing import Optional

from app.models.user import User


def _get_local_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def _get_turso_client(url: str, auth_token: str):
    return libsql.connect(database=url, auth_token=auth_token)


def init_db(db_path: str) -> None:
    with _get_local_conn(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                           INTEGER PRIMARY KEY AUTOINCREMENT,
                name                         TEXT    NOT NULL,
                email                        TEXT    NOT NULL UNIQUE,
                password_hash                TEXT    NOT NULL,
                role                         TEXT    NOT NULL DEFAULT 'user',
                status                       TEXT    NOT NULL DEFAULT 'pending',
                email_verified               INTEGER NOT NULL DEFAULT 0,
                created_at                   TEXT    NOT NULL,
                updated_at                   TEXT    NOT NULL,
                last_login                   TEXT,
                failed_attempts              INTEGER NOT NULL DEFAULT 0,
                locked_until                 TEXT,
                verification_code            TEXT,
                verification_code_expires_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")


class UserRepository:
    def __init__(self, db_config: dict):
        self._config   = db_config
        self._is_turso = "url" in db_config

    def _execute(self, sql: str, params: tuple = ()) -> list[dict]:
        if self._is_turso:
            client = _get_turso_client(
                self._config["url"], self._config["auth_token"]
            )
            cursor = client.execute(sql, tuple(params))
            rows   = cursor.fetchall()
            if not rows:
                return []
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        else:
            with _get_local_conn(self._config["path"]) as conn:
                rows = conn.execute(sql, params).fetchall()
                return [dict(r) for r in rows]

    def _execute_write(self, sql: str, params: tuple = ()) -> int:
        if self._is_turso:
            client = _get_turso_client(
                self._config["url"], self._config["auth_token"]
            )
            cursor = client.execute(sql, tuple(params))
            client.commit()
            return cursor.lastrowid or 0
        else:
            with _get_local_conn(self._config["path"]) as conn:
                cur = conn.execute(sql, params)
                return cur.lastrowid

    # ── Leitura ───────────────────────────────────────────────────────────────

    def find_by_id(self, user_id: int) -> Optional[User]:
        rows = self._execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return User.from_row(rows[0]) if rows else None

    def find_by_email(self, email: str) -> Optional[User]:
        rows = self._execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
        )
        return User.from_row(rows[0]) if rows else None

    def find_by_email_and_code(self, email: str, code: str) -> Optional[User]:
        rows = self._execute(
            "SELECT * FROM users WHERE email = ? AND verification_code = ? COLLATE NOCASE",
            (email, code),
        )
        return User.from_row(rows[0]) if rows else None

    def list_all(self) -> list[User]:
        rows = self._execute("SELECT * FROM users ORDER BY created_at DESC")
        return [User.from_row(r) for r in rows]

    def email_exists(self, email: str) -> bool:
        rows = self._execute(
            "SELECT 1 FROM users WHERE email = ? COLLATE NOCASE", (email,)
        )
        return len(rows) > 0

    # ── Escrita ───────────────────────────────────────────────────────────────

    def create(self, user: User) -> User:
        last_id = self._execute_write(
            """INSERT INTO users
               (name, email, password_hash, role, status, email_verified,
                created_at, updated_at, last_login, failed_attempts, locked_until,
                verification_code, verification_code_expires_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user.name, user.email, user.password_hash, user.role, user.status,
                int(user.email_verified), user.created_at, user.updated_at,
                user.last_login, user.failed_attempts, user.locked_until,
                user.verification_code, user.verification_code_expires_at,
            ),
        )
        user.id = last_id
        return user

    def update(self, user: User) -> None:
        user.updated_at = datetime.now(timezone.utc).isoformat()
        self._execute_write(
            """UPDATE users SET
               name=?, email=?, password_hash=?, role=?, status=?,
               email_verified=?, updated_at=?, last_login=?,
               failed_attempts=?, locked_until=?,
               verification_code=?, verification_code_expires_at=?
               WHERE id=?""",
            (
                user.name, user.email, user.password_hash, user.role, user.status,
                int(user.email_verified), user.updated_at, user.last_login,
                user.failed_attempts, user.locked_until,
                user.verification_code, user.verification_code_expires_at,
                user.id,
            ),
        )

    def delete(self, user_id: int) -> None:
        self._execute_write("DELETE FROM users WHERE id = ?", (user_id,))