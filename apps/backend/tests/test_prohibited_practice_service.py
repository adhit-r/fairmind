"""Art 5 screening: conservative outcomes and strict input."""
import pytest

from src.application.services.prohibited_practice_service import KEYS, questions, screen


def _all(value):
    return {k: value for k in KEYS}


def test_covers_art_5_1_a_to_h():
    assert KEYS == tuple("abcdefgh")
    assert [q["clause"] for q in questions()] == [f"Art 5(1)({k})" for k in KEYS]


def test_all_no_is_clear_and_not_a_compliance_claim():
    r = screen(_all("no"))
    assert r["outcome"] == "clear" and r["open"] == [] and r["indicated"] == []
    assert "not a finding of compliance" in r["summary"]


def test_any_yes_is_indicated_even_when_others_are_unsure():
    r = screen({**_all("unsure"), "c": "yes"})
    assert r["outcome"] == "indicated" and r["indicated"] == ["Art 5(1)(c)"]


def test_unsure_or_missing_cannot_conclude():
    assert screen({**_all("no"), "f": "unsure"})["outcome"] == "needs_legal_review"
    r = screen({k: "no" for k in KEYS if k != "h"})
    assert r["outcome"] == "needs_legal_review" and r["open"] == ["Art 5(1)(h)"]
    assert screen(None)["outcome"] == "needs_legal_review"


def test_exceptions_are_named_never_applied():
    notes = {q["key"]: q["note"] for q in questions()}
    assert "medical or safety" in notes["f"]
    assert screen({**_all("no"), "f": "yes"})["outcome"] == "indicated"


@pytest.mark.parametrize("bad", [{"z": "no"}, {"a": "maybe"}, {"a": True}])
def test_unknown_keys_and_values_are_rejected(bad):
    with pytest.raises(ValueError):
        screen(bad)
