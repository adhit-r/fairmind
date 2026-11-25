"""eval_engines.VALIDATED (maturity L4) is exactly the evaluations the known-answer tests cover on every path."""

import importlib
import json
from pathlib import Path

from src.application.services.evaluation_results import RULES
from src.application.services.eval_engines import JUDGED, REGISTRY, VALIDATED, paths
from tests.known_answer import COVERED


def _main_path(evaluation_id):
    engine = REGISTRY.get(evaluation_id)
    return "rule" if engine is None else "live" if engine.live else "platform" if engine.run is None else "file"


def _covered():
    for f in sorted(Path(__file__).parent.glob("test_known_answer_*.py")):
        importlib.import_module(f"tests.{f.stem}")
    out = {}
    for evaluation_id, path in COVERED:
        out.setdefault(evaluation_id, set()).add(path or _main_path(evaluation_id))
    return out


def test_validated_is_earned_on_every_path():
    covered = _covered()
    earned = {e for e in set(REGISTRY) | set(RULES) if paths(e, RULES) <= covered.get(e, set())}
    assert VALIDATED == earned
    for evaluation_id, tested in covered.items():  # a tag names a path the evaluation has
        assert tested <= paths(evaluation_id, RULES), evaluation_id


def test_an_untested_path_keeps_an_evaluation_below_l4():
    # EV-DAT-01's text features have no known-answer test yet; its numeric features do
    assert "file" in _covered()["EV-DAT-01"] and "text" in paths("EV-DAT-01") and "EV-DAT-01" not in VALIDATED


def test_judged_evaluations_are_the_behaviour_tests_and_judged_platform_checks():
    assert {"EV-SEC-01", "EV-AGT-01", "EV-SLF-01"} <= JUDGED and "EV-DAT-01" not in JUDGED


def test_catalogue_maturity_matches_the_code():
    import json

    path = Path(__file__).resolve().parents[1] / "src/api/routers/pack_catalogue_data/catalogue.json"
    l4 = {e["id"] for e in json.loads(path.read_text())["evaluations"] if e.get("maturity") == "L4"}
    assert l4 == set(VALIDATED)


def test_every_maturity_level_has_a_plain_label_that_does_not_claim_a_benchmark():
    path = Path(__file__).resolve().parents[1] / "src/api/routers/pack_catalogue_data/catalogue.json"
    for e in json.loads(path.read_text())["evaluations"]:
        if e.get("maturity") == "L4":
            assert e["maturityLabel"] == "Known-answer tested (not independently benchmarked)", e["id"]
        elif e.get("maturity"):
            assert e["maturityLabel"], e["id"]
