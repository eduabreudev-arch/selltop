"""cria tabela users

Revision ID: b90be32279a0
Revises: 
Create Date: 2026-04-27 23:36:20.971107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b90be32279a0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — usado pelo Alembic no SQLite local."""
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('email', sa.Text(), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('role', sa.Text(), server_default='user', nullable=False),
    sa.Column('status', sa.Text(), server_default='pending', nullable=False),
    sa.Column('email_verified', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.Text(), nullable=False),
    sa.Column('last_login', sa.Text(), nullable=True),
    sa.Column('failed_attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('locked_until', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )


def downgrade() -> None:
    """Downgrade schema — usado pelo Alembic no SQLite local."""
    op.drop_table('users')


# ── SQL puro para o Turso (libsql_experimental) ───────────────────────────
UPGRADE_SQL = [
    """
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
    """,
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
]

DOWNGRADE_SQL = [
    "DROP INDEX IF EXISTS idx_users_email",
    "DROP TABLE IF EXISTS users",
]