# Validation Notes

Run the maintained package readiness check from the repository root:

```bash
python3 research/aibom-fairness-evidence/evaluation/validate_research_package.py
```

This stdlib check verifies required files, example JSON parsing, old artifact names, FairMind profile component counts, fault-case references, generic baseline mapping, CycloneDX-style baseline mapping, profile-only field separation, and the response-sheet template header.

Use a JSON Schema validator that supports draft 2020-12. The command below uses `uvx check-jsonschema` so validation does not require adding a project dependency.

```bash
uvx --from check-jsonschema check-jsonschema \
  --schemafile research/aibom-fairness-evidence/schema/aibom_fairness_evidence.schema.json \
  research/aibom-fairness-evidence/examples/loan_approval_fairness_profile.json \
  research/aibom-fairness-evidence/examples/hiring_ranker_fairness_profile.json \
  research/aibom-fairness-evidence/examples/healthcare_triage_fairness_profile.json
```

Run the cross-artifact consistency check after schema validation:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

base = Path("research/aibom-fairness-evidence")
profiles = [
    base / "examples/loan_approval_fairness_profile.json",
    base / "examples/hiring_ranker_fairness_profile.json",
    base / "examples/healthcare_triage_fairness_profile.json",
]

component_ids_by_system = {}
for profile_path in profiles:
    document = json.loads(profile_path.read_text())
    if document.get("fairmind_context", {}).get("platform_name") != "FairMind":
        raise SystemExit(f"{profile_path} missing FairMind context")
    if len(document["components"]) < 6:
        raise SystemExit(f"{profile_path} has fewer than six components")
    component_ids_by_system[document["system_name"]] = {
        component["component_id"] for component in document["components"]
    }

fault_path = base / "evaluation/fault_injection_cases.csv"
with fault_path.open(newline="") as handle:
    rows = list(csv.DictReader(handle))

expected_columns = {
    "case_id",
    "system",
    "component_id",
    "fault_type",
    "generic_bom_visible",
    "fairness_profile_visible",
    "expected_reviewer_action",
    "severity",
    "ground_truth_explanation",
}
if set(rows[0]) != expected_columns:
    raise SystemExit(f"unexpected CSV columns: {rows[0].keys()}")
if len(rows) != 24:
    raise SystemExit(f"expected 24 fault cases, found {len(rows)}")

for row in rows:
    if row["component_id"] not in component_ids_by_system[row["system"]]:
        raise SystemExit(f"unknown component for {row['case_id']}: {row['component_id']}")

print("validated FairMind context, component counts, and 24 fault-injection cases")
PY
```

Run the stronger-baseline consistency check before a reviewer pilot:

```bash
uvx --from check-jsonschema check-jsonschema \
  --schemafile https://cyclonedx.org/schema/bom-1.7.schema.json \
  research/aibom-fairness-evidence/examples/cyclonedx_style_loan_approval_mlbom.json \
  research/aibom-fairness-evidence/examples/cyclonedx_style_hiring_ranker_mlbom.json \
  research/aibom-fairness-evidence/examples/cyclonedx_style_healthcare_triage_mlbom.json
```

```bash
python3 - <<'PY'
import json
from pathlib import Path

base = Path("research/aibom-fairness-evidence")
profile_paths = {
    "Loan Approval Model": base / "examples/loan_approval_fairness_profile.json",
    "Hiring Ranker": base / "examples/hiring_ranker_fairness_profile.json",
    "Healthcare Triage Model": base / "examples/healthcare_triage_fairness_profile.json",
}
baseline_paths = {
    "Loan Approval Model": base / "examples/cyclonedx_style_loan_approval_mlbom.json",
    "Hiring Ranker": base / "examples/cyclonedx_style_hiring_ranker_mlbom.json",
    "Healthcare Triage Model": base / "examples/cyclonedx_style_healthcare_triage_mlbom.json",
}
profile_only_keys = {
    "unknowns",
    "review_status",
    "validation_state",
    "evidence_freshness",
    "reviewer_action",
    "simulated_evidence_count",
    "stale_evidence_count",
}

for system, profile_path in profile_paths.items():
    profile = json.loads(profile_path.read_text())
    profile_ids = {component["component_id"] for component in profile["components"]}

    baseline = json.loads(baseline_paths[system].read_text())
    if baseline.get("bomFormat") != "CycloneDX":
        raise SystemExit(f"{baseline_paths[system]} is not CycloneDX-style")
    if not baseline.get("components"):
        raise SystemExit(f"{baseline_paths[system]} has no components")

    baseline_ids = {component["bom-ref"] for component in baseline["components"]}
    missing = profile_ids - baseline_ids
    extra = baseline_ids - profile_ids
    if missing or extra:
        raise SystemExit(
            f"{system} component mismatch: missing={sorted(missing)}, extra={sorted(extra)}"
        )

    encoded = json.dumps(baseline)
    leaked_keys = [key for key in profile_only_keys if f'"{key}"' in encoded]
    if leaked_keys:
        raise SystemExit(
            f"{baseline_paths[system]} contains profile-only keys: {leaked_keys}"
        )

print("validated CycloneDX-style baseline mapping and profile-only field separation")
PY
```

Run a generated-profile schema check after changing the FairMind generator:

```bash
tmp_profile="/tmp/fairmind-generated-fairness-profile.json"
cd apps/backend
uv run python - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

from src.application.services.fairness_evidence_profile_service import (
    FairnessEvidenceProfileService,
)

service = FairnessEvidenceProfileService()
profile = service.generate_profile(
    bom_document={
        "id": "bom-generated-001",
        "project_name": "Generated Schema Check",
        "system_domain": "research_validation",
        "components": [
            {
                "id": "generated.model",
                "name": "Generated Model",
                "type": "model",
                "version": "1.0.0",
                "dependencies": [],
            }
        ],
    },
    evidence_records={
        "generated.model": {
            "protected_attributes_tested": ["gender"],
            "subgroup_coverage": {
                "evaluated_groups": ["gender:female", "gender:male"],
                "missing_groups": [],
                "coverage_notes": "Generated schema validation fixture.",
            },
            "fairness_metrics": [
                {
                    "metric": "selection_rate_gap",
                    "value": 0.04,
                    "threshold": 0.1,
                    "affected_groups": [],
                    "evidence_state": "current",
                }
            ],
            "bias_tests_run": [
                {
                    "test_name": "selection parity",
                    "test_type": "parity",
                    "result": "within threshold",
                    "evidence_state": "current",
                    "evidence_ref": "generated-evidence-001",
                }
            ],
            "evidence_refs": ["generated-evidence-001"],
            "evidence_freshness": {
                "last_updated": "2026-06-01T00:00:00Z",
                "expires_at": "2026-09-01T00:00:00Z",
                "staleness_rule": "Re-run quarterly.",
                "evidence_state": "current",
            },
            "review_status": "accepted",
            "reviewer": "schema-check-reviewer",
        }
    },
    generated_at=datetime(2026, 6, 6, tzinfo=timezone.utc),
)
Path("/tmp/fairmind-generated-fairness-profile.json").write_text(
    json.dumps(profile, indent=2) + "\n"
)
PY
cd ../..
uvx --from check-jsonschema check-jsonschema \
  --schemafile research/aibom-fairness-evidence/schema/aibom_fairness_evidence.schema.json \
  "$tmp_profile"
```
