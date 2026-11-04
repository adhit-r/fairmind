"""Disposable PostgreSQL databases for tests.

FAIRMIND_TEST_POSTGRES_URL names a server the tests may create and drop
databases on (never Neon or any shared database). Each test session gets:

* an app database built by scripts/setup_db.py, used as DATABASE_URL, and
* a template with every ORM table, cloned by ``fresh_engine()`` into an empty
  per-test database.
"""

import atexit
import os
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

SERVER_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL", "")
_PREFIX = f"fairmind_test_{os.getpid()}"
_TEMPLATE = f"{_PREFIX}_template"
_created: list[str] = []  # session databases
_per_test: list[tuple[str, object]] = []  # (database, engine) from fresh_engine()
_template_ready = False


def _url(database: str) -> str:
    return make_url(SERVER_URL).set(database=database).render_as_string(hide_password=False)


def _admin(sql: str) -> None:
    engine = create_engine(SERVER_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
    finally:
        engine.dispose()


def _create(name: str, template: str = "template0") -> str:
    _admin(f'CREATE DATABASE "{name}" TEMPLATE "{template}"')
    _created.append(name)
    return _url(name)


def create_app_database() -> str:
    """Create a fully migrated database and return its URL."""
    backend = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend / "scripts"))
    import setup_db

    url = _create(f"{_PREFIX}_app")
    # Before any database module imports: they bind their engines to it.
    os.environ["DATABASE_URL"] = url
    with create_engine(url).connect() as conn:
        schema = conn.execute(text("SELECT current_schema()")).scalar()
    setup_db.apply_chain(url, schema)
    engine = create_engine(url)
    setup_db.add_orm_tables_and_columns(engine)
    engine.dispose()
    setup_db.apply_always(url)
    return url


def _ensure_template() -> None:
    global _template_ready
    if _template_ready:
        return
    from database.connection import Base
    import database.governance_models as governance_models
    import database.models as user_models

    engine = create_engine(_create(_TEMPLATE))
    for metadata in {id(m): m for m in (Base.metadata, user_models.Base.metadata, governance_models.Base.metadata)}.values():
        metadata.create_all(engine)
    engine.dispose()
    _template_ready = True


def fresh_engine(**kwargs):
    """Engine on a new database holding every ORM table and no rows.

    Dropped after the test by ``drop_test_databases`` (autouse in conftest).
    """
    _ensure_template()
    name = f"{_PREFIX}_{uuid.uuid4().hex[:12]}"
    _admin(f'CREATE DATABASE "{name}" TEMPLATE "{_TEMPLATE}"')
    engine = create_engine(_url(name), **kwargs)
    _per_test.append((name, engine))
    return engine


def drop_test_databases() -> None:
    while _per_test:
        name, engine = _per_test.pop()
        engine.dispose()
        _admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@atexit.register
def _drop_all() -> None:
    if not SERVER_URL:
        return
    drop_test_databases()
    for name in reversed(_created):
        try:
            _admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        except Exception:
            pass
