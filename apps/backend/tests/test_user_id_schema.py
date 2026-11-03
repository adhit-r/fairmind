"""A Postgres database built from the models must match production, where users.id and every reference to it are varchar."""

import uuid

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from database.models import AuditLog, Organization, OrganizationMember, OrganizationInvitation, User, UserId


def _ddl(model, dialect):
    return str(CreateTable(model.__table__).compile(dialect=dialect))


def test_user_id_columns_are_varchar_on_postgres():
    pg = postgresql.dialect()
    assert "id VARCHAR(255) NOT NULL" in _ddl(User, pg)
    assert "owner_id VARCHAR(255) NOT NULL" in _ddl(Organization, pg)
    assert "user_id VARCHAR(255)" in _ddl(AuditLog, pg)
    assert "user_id VARCHAR NOT NULL" in _ddl(OrganizationMember, pg)  # text, as production's org_members
    assert "invited_by VARCHAR" in _ddl(OrganizationInvitation, pg)


def test_users_create_table_leaves_out_the_keys_back_to_organizations():
    users = _ddl(User, postgresql.dialect())
    assert "REFERENCES organizations" not in users  # added after organizations exists
    assert "REFERENCES users" in _ddl(Organization, postgresql.dialect())


def test_sqlite_is_unchanged():
    users = _ddl(User, sqlite.dialect())
    assert "id UUID NOT NULL" in users  # as before UserId existed
    assert "FOREIGN KEY(org_id) REFERENCES organizations (id)" in users  # SQLite cannot ALTER, so the key stays inline
    # Member ids match users.id on SQLite, so its foreign-key checks accept them (text only on Postgres).
    assert "user_id UUID NOT NULL" in _ddl(OrganizationMember, sqlite.dialect())


def test_user_id_round_trips_as_uuid_on_postgres():
    t, pg, value = UserId(), postgresql.dialect(), uuid.uuid4()
    assert t.process_bind_param(value, pg) == str(value)
    assert t.process_result_value(str(value), pg) == value
    assert t.process_result_value("legacy-id", pg) == "legacy-id"
