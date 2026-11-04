import uuid

from sqlalchemy.dialects.postgresql import psycopg2

from database.models import OrganizationMember


def test_org_member_user_id_binds_as_text_for_postgres():
    # org_members.user_id is varchar in Postgres (users.id is varchar); a ::UUID bind
    # raises "operator does not exist: character varying = uuid" on every membership check.
    compiled = (OrganizationMember.__table__.c.user_id == uuid.uuid4()).compile(dialect=psycopg2.dialect())
    assert "::UUID" not in str(compiled)
    (value,) = compiled.construct_params().values()
    bound = compiled.binds["user_id_1"].type.bind_processor(psycopg2.dialect())
    assert isinstance(bound(value) if bound else value, str)
