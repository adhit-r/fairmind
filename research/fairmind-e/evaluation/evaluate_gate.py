#!/usr/bin/env python3
"""Evaluate FairMind-E gate labels for the paper wedge.

This is intentionally small: a checked-in labeled fixture set, the production
domain engine, and deterministic CSV/Markdown/SVG outputs.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import pathlib
import sys
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "apps" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.domain.environmental import EnvironmentalAssessment, run_assessment  # noqa: E402


FIXTURE_PATH = pathlib.Path(__file__).resolve().parent / "fixtures" / "paper_gate_cases.json"

CSV_COLUMNS = [
    "case_id",
    "description",
    "provenance_class",
    "lifecycle_phase",
    "expected_recommendation",
    "actual_recommendation",
    "expected_approval_blocking",
    "actual_approval_blocking",
    "expected_impact_tier",
    "actual_impact_tier",
    "expected_confidence_score",
    "actual_confidence_score",
    "match",
    "failure_reason",
]


def bool_text(value: bool) -> str:
    return "true" if bool(value) else "false"


def fmt_score(value: Any) -> str:
    return f"{float(value):.2f}"


def load_fixture(path: pathlib.Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"fixture has no cases: {path}")
    return data


def normalize_assessment(raw: dict[str, Any]) -> dict[str, Any]:
    return EnvironmentalAssessment(**raw).normalized_payload()


def evaluate_case(case: dict[str, Any]) -> dict[str, str]:
    expected = case["expected"]
    assessment = normalize_assessment(case["assessment"])
    result = run_assessment(assessment)

    failures: list[str] = []
    actual_recommendation = result.recommendation
    actual_blocking = bool(result.approval_blocking)
    actual_tier = result.impact_tier
    actual_confidence = float(result.confidence_score)

    if expected["recommendation"] != actual_recommendation:
        failures.append("recommendation")
    if bool(expected["approval_blocking"]) != actual_blocking:
        failures.append("approval_blocking")
    if expected["impact_tier"] != actual_tier:
        failures.append("impact_tier")
    if abs(float(expected["confidence_score"]) - actual_confidence) > 0.0001:
        failures.append("confidence_score")

    return {
        "case_id": str(case["id"]),
        "description": str(case["description"]),
        "provenance_class": str(assessment["provenance_class"]),
        "lifecycle_phase": str(assessment["lifecycle_phase"]),
        "expected_recommendation": str(expected["recommendation"]),
        "actual_recommendation": actual_recommendation,
        "expected_approval_blocking": bool_text(bool(expected["approval_blocking"])),
        "actual_approval_blocking": bool_text(actual_blocking),
        "expected_impact_tier": str(expected["impact_tier"]),
        "actual_impact_tier": actual_tier,
        "expected_confidence_score": fmt_score(expected["confidence_score"]),
        "actual_confidence_score": fmt_score(actual_confidence),
        "match": bool_text(not failures),
        "failure_reason": ";".join(failures),
    }


def evaluate_cases(cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [evaluate_case(case) for case in cases]


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return counts


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    total = len(rows)
    matches = sum(1 for row in rows if row["match"] == "true")
    recommendation_matches = sum(
        1 for row in rows if row["expected_recommendation"] == row["actual_recommendation"]
    )
    blocking_matches = sum(
        1 for row in rows if row["expected_approval_blocking"] == row["actual_approval_blocking"]
    )
    return {
        "total": total,
        "matches": matches,
        "accuracy": matches / total if total else 0.0,
        "recommendation_matches": recommendation_matches,
        "blocking_matches": blocking_matches,
        "expected_recommendations": count_by(rows, "expected_recommendation"),
        "actual_recommendations": count_by(rows, "actual_recommendation"),
        "failures": [row for row in rows if row["match"] != "true"],
    }


def write_csv(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: pathlib.Path, rows: list[dict[str, str]], fixture: dict[str, Any]) -> None:
    summary = summarize(rows)
    expected = summary["expected_recommendations"]
    actual = summary["actual_recommendations"]
    failures = summary["failures"]
    failure_text = "None." if not failures else "\n".join(
        f"- `{row['case_id']}`: {row['failure_reason']}" for row in failures
    )
    body = f"""# FairMind-E Paper Gate Evaluation

Fixture: `paper_gate_cases.json`

Claim under test: {fixture.get("claim", "")}

## Results

- Cases: {summary["total"]}
- Exact label accuracy: {summary["matches"]}/{summary["total"]} ({summary["accuracy"]:.1%})
- Recommendation matches: {summary["recommendation_matches"]}/{summary["total"]}
- Approval-blocking matches: {summary["blocking_matches"]}/{summary["total"]}

## Expected Recommendations

- `go`: {expected.get("go", 0)}
- `conditional_go`: {expected.get("conditional_go", 0)}
- `no_go`: {expected.get("no_go", 0)}

## Actual Recommendations

- `go`: {actual.get("go", 0)}
- `conditional_go`: {actual.get("conditional_go", 0)}
- `no_go`: {actual.get("no_go", 0)}

## Failures

{failure_text}

## Claim Boundary

This is a hand-labeled fixture evaluation for the paper method section. It is
not a workload-emissions measurement study, a regulatory compliance audit, or a
statistical benchmark over production systems.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def svg_bar(x: int, y: int, width: int, height: int, label: str, fill: str) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="#111111" stroke-width="2"/>',
            f'<text x="{x}" y="288" font-size="12" font-family="Arial, sans-serif" fill="#111111">{html.escape(label)}</text>',
        ]
    )


def write_svg(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    expected = count_by(rows, "expected_recommendation")
    actual = count_by(rows, "actual_recommendation")
    labels = ["go", "conditional_go", "no_go"]
    max_count = max([1, *expected.values(), *actual.values()])
    colors = {"expected": "#0F766E", "actual": "#F97316"}
    bars: list[str] = []
    for index, label in enumerate(labels):
        base_x = 80 + index * 190
        expected_height = int(170 * expected.get(label, 0) / max_count)
        actual_height = int(170 * actual.get(label, 0) / max_count)
        bars.append(svg_bar(base_x, 250 - expected_height, 52, expected_height, f"expected {label}", colors["expected"]))
        bars.append(svg_bar(base_x + 64, 250 - actual_height, 52, actual_height, f"actual {label}", colors["actual"]))
        bars.append(
            f'<text x="{base_x}" y="{238 - expected_height}" font-size="12" font-family="Arial, sans-serif" fill="#111111">{expected.get(label, 0)}</text>'
        )
        bars.append(
            f'<text x="{base_x + 64}" y="{238 - actual_height}" font-size="12" font-family="Arial, sans-serif" fill="#111111">{actual.get(label, 0)}</text>'
        )

    summary = summarize(rows)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="330" viewBox="0 0 720 330" role="img" aria-label="FairMind-E paper gate decision counts">
<rect width="100%" height="100%" fill="#FFFFFF"/>
<text x="36" y="38" font-size="24" font-family="Arial, sans-serif" font-weight="700" fill="#111111">FairMind-E paper gate decisions</text>
<text x="36" y="64" font-size="13" font-family="Arial, sans-serif" fill="#333333">Expected versus actual gate labels; exact accuracy {summary["accuracy"]:.1%}.</text>
<rect x="36" y="82" width="16" height="16" fill="#0F766E" stroke="#111111" stroke-width="2"/>
<text x="60" y="95" font-size="12" font-family="Arial, sans-serif" fill="#111111">expected</text>
<rect x="136" y="82" width="16" height="16" fill="#F97316" stroke="#111111" stroke-width="2"/>
<text x="160" y="95" font-size="12" font-family="Arial, sans-serif" fill="#111111">actual</text>
<line x1="42" y1="252" x2="678" y2="252" stroke="#111111" stroke-width="3"/>
{chr(10).join(bars)}
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def run(fixture_path: pathlib.Path, output_root: pathlib.Path) -> dict[str, Any]:
    fixture = load_fixture(fixture_path)
    rows = evaluate_cases(fixture["cases"])
    write_csv(output_root / "results" / "paper_gate_eval.csv", rows)
    write_summary(output_root / "results" / "paper_gate_summary.md", rows, fixture)
    write_svg(output_root / "plots" / "paper_gate_decisions.svg", rows)
    return summarize(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=pathlib.Path, default=FIXTURE_PATH)
    parser.add_argument(
        "--output-root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(args.fixtures, args.output_root)
    return 0 if summary["matches"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
