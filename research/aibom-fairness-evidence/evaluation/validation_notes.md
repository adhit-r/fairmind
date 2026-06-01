# Validation Notes

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
