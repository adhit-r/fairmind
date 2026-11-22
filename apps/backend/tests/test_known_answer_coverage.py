"""eval_engines.VALIDATED (maturity L4) is exactly the evaluations the known-answer tests cover."""

import importlib
import json
from pathlib import Path

from src.application.services.evaluation_results import RULES
from src.application.services.eval_engines import REGISTRY, VALIDATED
from tests.known_answer import COVERED


def test_validated_equals_the_known_answer_tests():
    for f in sorted(Path(__file__).parent.glob("test_known_answer_*.py")):
        importlib.import_module(f"tests.{f.stem}")
    assert VALIDATED == COVERED & (set(REGISTRY) | set(RULES)) and VALIDATED == set(REGISTRY) | set(RULES)


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
