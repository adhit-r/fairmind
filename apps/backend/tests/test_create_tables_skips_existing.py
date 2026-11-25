"""create_tables() must not issue a per-table check for tables that already exist.

Route handlers call it on their first request; against a remote database each
check is a network round trip, and ~80 of them froze the event loop for minutes.
"""

from sqlalchemy import Table, inspect

from database.connection import db_manager


def test_create_tables_skips_tables_that_already_exist(monkeypatch):
    db_manager.create_tables()  # whatever was missing exists now
    existing = set(inspect(db_manager.engine).get_table_names())
    assert existing

    attempted = []
    monkeypatch.setattr(Table, "create", lambda self, *args, **kwargs: attempted.append(self.name))
    db_manager.create_tables()

    assert [name for name in attempted if name in existing] == []
