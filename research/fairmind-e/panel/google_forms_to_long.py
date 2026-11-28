"""
FairMind-E expert panel: Google Forms export to the importer's long format.

Google Forms exports one row per respondent. ``import_responses.py`` wants one
row per rater-item. This reshapes the export, taking each item's profile from
the rater's position in ``assignment_plan_arms.csv``, so raters never type a
profile reference and cannot mistype one.

The form must use these question titles exactly (INSTRUMENT.md, Section 5a):

    Rater ID
    Item N: release recommendation        go | conditional_go | no_go
    Item N: required evidence             checkboxes labelled "ENV-1 ...".."ENV-6 ..."
    Item N: decision confidence           linear scale 1-5
    Item N: confidence score shown        yes | no

for N = 1..8. Google Forms cannot time individual items, so
``time_to_decision_s`` is left empty. A rater whose ID is not in the plan, or
an item with no recommendation, is reported and skipped, never guessed.

Stdlib only.

Usage:
    python3 research/fairmind-e/panel/google_forms_to_long.py \\
        --export forms_export.csv --out raw_export.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

PANEL_DIR = Path(__file__).resolve().parent
ITEMS = 8
OUT_COLUMNS = (
    "rater_id",
    "profile_id",
    "recommendation",
    "controls_required",
    "decision_confidence_1_5",
    "time_to_decision_s",
    "confidence_shown",
)
_FIELDS = {
    "recommendation": "release recommendation",
    "controls": "required evidence",
    "confidence": "decision confidence",
    "shown": "confidence score shown",
}


def _plan(path: Path) -> dict[tuple[str, int], str]:
    with path.open(encoding="utf-8") as handle:
        return {
            (row["rater_id"], int(row["position"])): row["profile_id"]
            for row in csv.DictReader(handle)
        }


def _column(headers: list[str], item: int, field: str) -> str | None:
    title = f"item {item}: {_FIELDS[field]}"
    return next((h for h in headers if h.strip().lower() == title), None)


def convert(rows: list[dict[str, str]], plan: dict[tuple[str, int], str]) -> tuple[list[dict[str, str]], list[str]]:
    """Return (long rows, problems)."""
    out: list[dict[str, str]] = []
    problems: list[str] = []
    headers = list(rows[0].keys()) if rows else []
    rater_col = next((h for h in headers if h.strip().lower() == "rater id"), None)
    if rater_col is None:
        return [], ["export has no 'Rater ID' column"]
    for index, row in enumerate(rows, start=2):
        rater = (row.get(rater_col) or "").strip().upper()
        if not any(r == rater for r, _ in plan):
            problems.append(f"line {index}: rater '{rater}' is not in the assignment plan")
            continue
        for item in range(1, ITEMS + 1):
            cols = {f: _column(headers, item, f) for f in _FIELDS}
            recommendation = (row.get(cols["recommendation"] or "") or "").strip()
            if not recommendation:
                problems.append(f"{rater} item {item}: no recommendation, skipped")
                continue
            controls = sorted(
                set(re.findall(r"ENV-[1-6]", row.get(cols["controls"] or "") or "")),
                key=lambda code: int(code.split("-")[1]),
            )
            out.append(
                {
                    "rater_id": rater,
                    "profile_id": plan[(rater, item)],
                    "recommendation": recommendation,
                    "controls_required": ";".join(controls),
                    "decision_confidence_1_5": (row.get(cols["confidence"] or "") or "").strip(),
                    "time_to_decision_s": "",
                    "confidence_shown": (row.get(cols["shown"] or "") or "").strip().lower(),
                }
            )
    return out, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reshape a Google Forms panel export")
    parser.add_argument("--export", required=True, type=Path, help="Google Forms CSV download")
    parser.add_argument("--out", required=True, type=Path, help="long CSV for import_responses.py")
    parser.add_argument("--plan", type=Path, default=PANEL_DIR / "assignment_plan_arms.csv")
    args = parser.parse_args(argv)

    with args.export.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    long_rows, problems = convert(rows, _plan(args.plan))
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUT_COLUMNS)
        writer.writeheader()
        writer.writerows(long_rows)
    for problem in problems:
        print(f"WARNING {problem}", file=sys.stderr)
    print(f"wrote {len(long_rows)} rater-item rows from {len(rows)} responses to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
