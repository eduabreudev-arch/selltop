import os
import sys
from logging.config import fileConfig
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from models.user import metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

turso_url = os.environ.get("TURSO_URL", "")
turso_token = os.environ.get("TURSO_AUTH_TOKEN", "")
db_path = os.environ.get("DATABASE", "selltop.db")

def run_migrations_turso() -> None:
    import libsql_experimental as libsql

    conn = libsql.connect(database=turso_url, auth_token=turso_token)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
    """)

    row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
    current = row[0] if row else None
    print(f"Versão atual no Turso: {current or 'nenhuma'}")

    from alembic.script import ScriptDirectory
    from alembic.config import Config as AlembicConfig

    cfg = AlembicConfig("alembic.ini")
    script = ScriptDirectory.from_config(cfg)

    applied = False
    for sc in reversed(list(script.walk_revisions("base", "heads"))):
        if current and sc.revision <= current:
            print(f"Pulando {sc.revision} — já aplicada")
            continue
        print(f"Aplicando {sc.revision}: {sc.doc}")
        for sql in sc.module.UPGRADE_SQL:
            conn.execute(sql)
        conn.execute(
            "INSERT OR REPLACE INTO alembic_version (version_num) VALUES (?)",
            (sc.revision,)
        )
        applied = True

    conn.commit()
    if applied:
        print("✅ Migrations aplicadas com sucesso!")
    else:
        print("✅ Banco já está atualizado!")


def run_migrations_online() -> None:
    from sqlalchemy import create_engine, pool
    engine = create_engine(
        f"sqlite:///{db_path}",
        poolclass=pool.NullPool,
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
            compare_type=True,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if turso_url:
    run_migrations_turso()
else:
    run_migrations_online()