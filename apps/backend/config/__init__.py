# Config Package


import psycopg
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def _bind_parameters_client_side(dbapi_connection, _connection_record):
    """Keep psycopg2's client-side parameter binding on psycopg 3 connections.

    The raw SQL here relies on it: with server-side binding Postgres cannot type
    a parameter used only in ``:x IS NULL`` and rejects the query.
    """
    if isinstance(dbapi_connection, psycopg.Connection):
        dbapi_connection.cursor_factory = psycopg.ClientCursor
