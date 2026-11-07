"""
FairMind-E expert panel: response importer.

Turns a raw survey export into the two CSVs that analysis/hypotheses.py
consumes, joining each response to its rater role and study arm from
assignment_plan_arms.csv.

Raw export contract (one row per rater-item; column order is irrelevant,
extra columns are ignored):

    rater_id             stable across the whole study (R01..R15)
    profile_id           P01..P12
    recommendation       go | conditional_go | no_go
    controls_required    semicolon-joined ENV-1..ENV-6, may be empty
    decision_confidence_1_5   integer 1-5
    time_to_decision_s   number of seconds, optional
    confidence_shown     yes | no, required on module-arm items only
                         (the H1 manipulation check)

Outputs:

    panel_responses.csv     rater_id, rater_role, profile_id, recommendation,
                            decision_confidence_1_5, decisive_controls,
                            time_to_decision_s
    coverage_pre_post.csv   system_id, coverage_rate_pre, coverage_rate_post

Coverage is scored against the gold checklist: coverage_rate is the count of
distinct ENV controls the rater demanded divided by the number of applicable
controls for that profile. Baseline-arm means become coverage_rate_pre and
module-arm means become coverage_rate_post, paired per profile.

Responses that fail the manipulation check (a module-arm item where the rater
reports no confidence score was shown) are dropped from H1 and reported, rather
than silently diluting the correlation. Nothing is imputed: a missing or
malformed row is reported and excluded, never repaired with a guess.

Stdlib only.

Usage:
    python3 research/fairmind-e/panel/import_responses.py --responses raw.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

PANEL_DIR = Path(__file__).resolve().parent

VALID_RECOMMENDATIONS = ("go", "conditional_go", "no_go")
BASELINE = "baseline"
MODULE = "module"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle)]


def load_arms(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Map (rater_id, profile_id) -> assignment row."""
    return {(r["rater_id"], r["profile_id"]): r for r in _read_csv(path)}


def load_gold(path: Path) -> dict[str, set[str]]:
    """Map profile_id -> set of applicable control codes."""
    gold: dict[str, set[str]] = {}
    for row in _read_csv(path):
        if str(row.get("applicable", "")).strip().lower() in ("yes", "true", "1"):
            gold.setdefault(row["profile_id"], set()).add(row["control"])
    return gold


def parse_controls(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = [p.strip().upper() for p in str(raw).replace(",", ";").split(";")]
    return [p for p in parts if p]


def import_responses(
    responses_path: Path,
    arms_path: Path,
    gold_path: Path,
    out_dir: Path,
) -> dict[str, object]:
    arms = load_arms(arms_path)
    gold = load_gold(gold_path)
    raw_rows = _read_csv(responses_path)

    problems: list[str] = []
    panel_rows: list[dict[str, object]] = []
    # profile -> arm -> list of coverage rates
    coverage: dict[str, dict[str, list[float]]] = {}
    failed_checks = 0
    seen: set[tuple[str, str]] = set()

    for index, row in enumerate(raw_rows, start=2):  # header is line 1
        rater_id = (row.get("rater_id") or "").strip()
        profile_id = (row.get("profile_id") or "").strip()
        key = (rater_id, profile_id)
        if key not in arms:
            problems.append(
                f"line {index}: ({rater_id}, {profile_id}) is not in the assignment plan"
            )
            continue
        if key in seen:
            problems.append(
                f"line {index}: duplicate response for ({rater_id}, {profile_id}); "
                "first response kept"
            )
            continue
        seen.add(key)
        assignment = arms[key]
        arm = assignment["arm"]

        recommendation = (row.get("recommendation") or "").strip().lower()
        if recommendation not in VALID_RECOMMENDATIONS:
            problems.append(
                f"line {index}: recommendation '{recommendation}' is not one of "
                f"{VALID_RECOMMENDATIONS}"
            )
            continue

        applicable = gold.get(profile_id)
        if not applicable:
            problems.append(f"line {index}: no gold checklist for {profile_id}")
            continue

        # Manipulation check: a module item must have shown the confidence score.
        shown = (row.get("confidence_shown") or "").strip().lower()
        if arm == MODULE and not shown:
            problems.append(
                f"line {index}: confidence_shown is required on module-arm rows"
            )
            continue

        controls = parse_controls(row.get("controls_required"))
        unknown = [c for c in controls if c not in applicable]
        if unknown:
            problems.append(f"line {index}: unknown control codes {unknown}")
        demanded = {c for c in controls if c in applicable}
        coverage.setdefault(profile_id, {BASELINE: [], MODULE: []})[arm].append(
            len(demanded) / len(applicable)
        )

        if arm == MODULE and shown in ("no", "false", "0"):
            failed_checks += 1
            continue

        confidence_raw = (row.get("decision_confidence_1_5") or "").strip()
        try:
            decision_confidence = int(float(confidence_raw))
        except ValueError:
            problems.append(f"line {index}: decision_confidence_1_5 '{confidence_raw}' is not numeric")
            continue
        if not 1 <= decision_confidence <= 5:
            problems.append(f"line {index}: decision_confidence_1_5 {decision_confidence} outside 1-5")
            continue

        time_raw = (row.get("time_to_decision_s") or "").strip()
        try:
            time_to_decision = float(time_raw) if time_raw else ""
        except ValueError:
            time_to_decision = ""

        panel_rows.append(
            {
                "rater_id": rater_id,
                "rater_role": assignment["role"],
                "profile_id": profile_id,
                "recommendation": recommendation,
                "decision_confidence_1_5": decision_confidence,
                "decisive_controls": ";".join(sorted(demanded)),
                "time_to_decision_s": time_to_decision,
                "arm": arm,
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    panel_out = out_dir / "panel_responses.csv"
    with panel_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rater_id",
                "rater_role",
                "profile_id",
                "recommendation",
                "decision_confidence_1_5",
                "decisive_controls",
                "time_to_decision_s",
                "arm",
            ],
        )
        writer.writeheader()
        for row in sorted(panel_rows, key=lambda r: (r["rater_id"], r["profile_id"])):
            writer.writerow(row)

    coverage_rows: list[dict[str, object]] = []
    unpaired: list[str] = []
    for profile_id in sorted(coverage):
        pre = coverage[profile_id][BASELINE]
        post = coverage[profile_id][MODULE]
        if not pre or not post:
            unpaired.append(profile_id)
            continue
        coverage_rows.append(
            {
                "system_id": profile_id,
                "coverage_rate_pre": round(sum(pre) / len(pre), 6),
                "coverage_rate_post": round(sum(post) / len(post), 6),
            }
        )
    coverage_out = out_dir / "coverage_pre_post.csv"
    with coverage_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["system_id", "coverage_rate_pre", "coverage_rate_post"]
        )
        writer.writeheader()
        for row in coverage_rows:
            writer.writerow(row)

    return {
        "responses_read": len(raw_rows),
        "panel_rows": len(panel_rows),
        "coverage_pairs": len(coverage_rows),
        "manipulation_check_failures": failed_checks,
        "unpaired_profiles": unpaired,
        "problems": problems,
        "panel_out": str(panel_out),
        "coverage_out": str(coverage_out),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import FairMind-E panel responses")
    parser.add_argument("--responses", required=True, type=Path, help="raw survey export CSV")
    parser.add_argument(
        "--arms", type=Path, default=PANEL_DIR / "assignment_plan_arms.csv"
    )
    parser.add_argument("--gold", type=Path, default=PANEL_DIR / "gold_checklists.csv")
    parser.add_argument("--out-dir", type=Path, default=PANEL_DIR / "responses")
    args = parser.parse_args(argv)

    summary = import_responses(args.responses, args.arms, args.gold, args.out_dir)
    print(
        f"read {summary['responses_read']} responses -> {summary['panel_rows']} panel rows, "
        f"{summary['coverage_pairs']} coverage pairs"
    )
    if summary["manipulation_check_failures"]:
        print(
            f"excluded from H1: {summary['manipulation_check_failures']} module-arm "
            "responses failed the confidence-visibility check"
        )
    if summary["unpaired_profiles"]:
        print(f"profiles missing one arm (excluded from H2): {summary['unpaired_profiles']}")
    for problem in summary["problems"]:
        print(f"PROBLEM: {problem}")
    print(f"wrote {summary['panel_out']}")
    print(f"wrote {summary['coverage_out']}")
    return 1 if summary["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
