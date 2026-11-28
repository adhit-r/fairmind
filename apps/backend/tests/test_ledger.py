"""The organisation ledger: one chain per organisation, appended through ledger_service, checked from the start."""

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.routes import shared_views
from src.application.services import ledger_service
from tests.test_packs_routes import PACKS, _client, _org, no_rate_limit, tmp_database  # noqa: F401  (fixtures)
from tests.test_shared_views import BOARD, PUBLIC, _code, _share, mail  # noqa: F401  (fixtures)


def _db(engine):
    return sessionmaker(bind=engine)()


def test_entries_chain_and_a_changed_entry_breaks_it(tmp_database):
    org = "org-a"
    with _db(tmp_database) as db:
        first = ledger_service.append(db, org, "thing.made", "thing", "t1", "u1", {"n": 1})
        second = ledger_service.append(db, org, "thing.changed", "thing", "t1", "u1", {"n": 2})
        ledger_service.append(db, "org-b", "thing.made", "thing", "t9", None, {})
        db.commit()
        assert first["prevHash"] == ledger_service.GENESIS and second["prevHash"] == first["hash"] and second["seq"] == 2
        assert ledger_service.verify(db, org) == {"valid": True, "count": 2, "head": second["hash"], "brokenAt": None}
        assert ledger_service.verify(db, "org-b")["count"] == 1  # each organisation has its own chain
        assert [e["kind"] for e in ledger_service.entries(db, org, "thing", "t1")] == ["thing.made", "thing.changed"]

        db.execute(text("UPDATE ledger_entries SET payload_json = :p WHERE org_id = :o AND seq = 1"), {"p": '{"n":99}', "o": org})
        db.commit()
        assert ledger_service.verify(db, org)["brokenAt"] == 1 and ledger_service.verify(db, "org-b")["valid"]


def test_a_removed_entry_and_a_taken_place_are_caught(tmp_database):
    with _db(tmp_database) as db:
        for i in range(3):
            ledger_service.append(db, "org-a", "k", "s", "1", None, {"i": i})
        db.commit()
        with pytest.raises(IntegrityError):  # two writers cannot share a place in the chain
            db.execute(text(
                "INSERT INTO ledger_entries (id, org_id, seq, kind, subject_type, subject_id, payload_json, canonical_json, prev_hash, hash, created_at) "
                "VALUES ('x', 'org-a', 3, 'k', 's', '1', '{}', '{}', 'p', 'h', 'now')"
            ))
        db.rollback()
        db.execute(text("DELETE FROM ledger_entries WHERE org_id = 'org-a' AND seq = 2"))
        db.commit()
        assert ledger_service.verify(db, "org-a")["brokenAt"] == 3


def test_sharing_pinning_and_revoking_land_on_the_ledger(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    pinned = owner.post(f"{PACKS}/boards", json={"question": "q", "board": BOARD}).json()
    view_id = _share(owner, org_id).json()["id"]
    owner.delete(f"{PACKS}/shared-views/{view_id}")
    owner.delete(f"{PACKS}/boards/{pinned['id']}")
    got = owner.get(f"{PACKS}/ledger").json()
    assert [e["kind"] for e in got["entries"]] == ["board.pinned", "view.sealed", "view.revoked", "board.unpinned"]
    assert got["chain"]["valid"] and got["chain"]["count"] == 4
    sealed = got["entries"][1]["payload"]
    assert sealed["readers"] == 1 and "auditor" not in str(got)  # counts and hashes only, never an address
    assert owner.get(f"{PACKS}/ledger", params={"subject_type": "shared_view", "subject_id": view_id}).json()["entries"][0]["subjectId"] == view_id


def test_only_a_manager_reads_the_ledger(tmp_database):
    org_id, _ = _org(tmp_database)
    assert _client(tmp_database, org_id, role="viewer").get(f"{PACKS}/ledger").status_code == 403


def test_a_reader_can_check_the_seal_against_the_ledger(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    view_id = _share(owner, org_id).json()["id"]
    reader = TestClient(app)
    assert reader.get(f"{PUBLIC}/{view_id}/seal").status_code == 401
    token = reader.post(f"{PUBLIC}/{view_id}/verify", json={"email": "auditor@example.com", "code": _code(mail, reader, view_id)}).json()["token"]
    got = reader.get(f"{PUBLIC}/{view_id}/seal", headers={"X-View-Token": token}).json()
    assert got["matchesStored"] and got["onLedger"] and got["chainValid"] and got["ledgerSeq"] == 1
    assert re.fullmatch(r"[0-9a-f]{64}", got["ledgerHash"])

    with _db(tmp_database) as db:  # the stored figures change after sealing
        db.execute(text("UPDATE shared_views SET data_json = :d WHERE id = :id"), {"d": '{"x":1}', "id": view_id})
        db.commit()
    changed = reader.get(f"{PUBLIC}/{view_id}/seal", headers={"X-View-Token": token}).json()
    assert changed["matchesStored"] is False and changed["onLedger"] is False and changed["chainValid"]
