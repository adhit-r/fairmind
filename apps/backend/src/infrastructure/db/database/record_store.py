"""
Durable JSON records for services that used to keep state in process memory.

One table (service_records) holds every namespace; a record is a JSON object
under a unique key, optionally scoped to the user or organisation that owns it.
State survives restarts and is shared between workers.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

_ready = False


def _session():
    from database.connection import db_manager

    global _ready
    if not _ready:
        import database.governance_models  # noqa: F401  (registers service_records)

        db_manager.create_tables()  # skips tables that already exist
        _ready = True
    return db_manager.get_session()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RecordStore:
    """Records of one namespace."""

    def __init__(self, namespace: str):
        self.namespace = namespace

    def put(self, key: str, payload: Dict[str, Any], scope: Optional[str] = None) -> None:
        body = json.dumps(payload, default=str)
        now = _now()
        with _session() as session:
            session.execute(
                text(
                    "INSERT INTO service_records (id, namespace, record_key, scope, payload_json, created_at, updated_at) "
                    "VALUES (:id, :ns, :key, :scope, :body, :now, :now) "
                    "ON CONFLICT (namespace, record_key) DO UPDATE "
                    "SET payload_json = EXCLUDED.payload_json, scope = EXCLUDED.scope, updated_at = EXCLUDED.updated_at"
                ),
                {"id": str(uuid.uuid4()), "ns": self.namespace, "key": key, "scope": scope, "body": body, "now": now},
            )

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with _session() as session:
            row = session.execute(
                text("SELECT payload_json FROM service_records WHERE namespace = :ns AND record_key = :key"),
                {"ns": self.namespace, "key": key},
            ).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, scope: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Records oldest first; only those of `scope` when it is given."""
        sql = "SELECT payload_json FROM service_records WHERE namespace = :ns"
        params: Dict[str, Any] = {"ns": self.namespace}
        if scope is not None:
            sql += " AND scope = :scope"
            params["scope"] = scope
        sql += " ORDER BY created_at DESC, id DESC"
        if limit:
            sql += " LIMIT :limit"
            params["limit"] = int(limit)
        with _session() as session:
            rows = session.execute(text(sql), params).fetchall()
        return [json.loads(r[0]) for r in reversed(rows)]

    def delete(self, key: str) -> bool:
        with _session() as session:
            result = session.execute(
                text("DELETE FROM service_records WHERE namespace = :ns AND record_key = :key"),
                {"ns": self.namespace, "key": key},
            )
        return (result.rowcount or 0) > 0


class PersistentMap:
    """A dict-like view of one namespace, for services written against a dict.

    `dump` turns a value into a JSON object and `load` turns it back;
    `scope_of` names the owning user or organisation of a value, if any.
    """

    def __init__(self, namespace: str, load, dump, scope_of=None):
        self._store = RecordStore(namespace)
        self._load, self._dump, self._scope_of = load, dump, scope_of

    def __setitem__(self, key: str, value) -> None:
        self._store.put(str(key), self._dump(value), scope=self._scope_of(value) if self._scope_of else None)

    def get(self, key: str, default=None):
        raw = self._store.get(str(key))
        return self._load(raw) if raw is not None else default

    def __getitem__(self, key: str):
        raw = self._store.get(str(key))
        if raw is None:
            raise KeyError(key)
        return self._load(raw)

    def __contains__(self, key) -> bool:
        return self._store.get(str(key)) is not None

    def __delitem__(self, key: str) -> None:
        if not self._store.delete(str(key)):
            raise KeyError(key)

    def pop(self, key: str, default=None):
        value = self.get(key, default)
        self._store.delete(str(key))
        return value

    def values(self, scope: Optional[str] = None) -> List[Any]:
        return [self._load(raw) for raw in self._store.list(scope=scope)]

    def __len__(self) -> int:
        return len(self._store.list())
