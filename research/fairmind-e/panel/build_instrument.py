"""
FairMind-E expert panel: instrument builder.

Reads the engine-validated profiles and the counterbalanced assignment plan,
assigns each (rater, profile) pair to a study arm, and emits the printable
rater packets plus the machine-readable artifacts the analysis needs.

The two-arm design is not optional. H2 compares ENV control coverage between a
baseline condition (raw measurements only) and a module condition (full
FairMind-E output). A single-condition instrument produces zero baseline
observations and H2 cannot be computed from it afterwards; see
analysis/DESIGN_NOTES.md.

Arm assignment is deterministic and contamination-free: each rater's eight
profiles are split into two disjoint halves of four, so no rater ever sees the
same profile under both conditions. Raters alternate which half they see first,
so presentation order is counterbalanced across the panel.

Stdlib only. No wall-clock, no unseeded randomness: rerunning reproduces every
byte.

Usage:
    python3 research/fairmind-e/panel/build_instrument.py
    python3 research/fairmind-e/panel/build_instrument.py --check
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PANEL_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = PANEL_DIR.parent

BASELINE = "baseline"
MODULE = "module"

# Every control in the MVP set applies to every profile (controls.py defines no
# optional controls), so the gold checklist is all six for each profile and the
# H2 denominator is a constant 6. If optional controls are added later, this is
# the single place that must change.
ENV_CONTROLS = ("ENV-1", "ENV-2", "ENV-3", "ENV-4", "ENV-5", "ENV-6")

ENV_CONTROL_LABELS = {
    "ENV-1": "Assessment boundary declared (system, lifecycle phase, functional unit)",
    "ENV-2": "Energy accounting (total kWh for the declared boundary)",
    "ENV-3": "Dual carbon accounting (location-based and market-based kgCO2e)",
    "ENV-4": "Per-functional-unit efficiency metric",
    "ENV-5": "Evidence confidence (provenance class and disclosed uncertainty)",
    "ENV-6": "Mitigation or owned exception for a conditional release",
}

# Metric labels and units for the rater-facing measurement table.
METRIC_LABELS = [
    ("total_kwh", "Total energy", "kWh"),
    ("total_kg_co2e_location", "Carbon, location-based", "kg CO2e"),
    ("total_kg_co2e_market", "Carbon, market-based", "kg CO2e"),
    ("kg_co2e_per_1000_requests", "Intensity per 1000 requests", "kg CO2e"),
    ("kg_co2e_per_1m_tokens", "Intensity per 1M tokens", "kg CO2e"),
    ("location_carbon_intensity_g_co2e_per_kwh", "Grid intensity, location", "g CO2e/kWh"),
    ("market_carbon_intensity_g_co2e_per_kwh", "Grid intensity, market", "g CO2e/kWh"),
    ("carbon_intensity_basis", "Intensity basis", ""),
    ("pue", "PUE", ""),
    ("wue_litres_per_kwh", "WUE", "litres/kWh"),
    ("embodied_kg_co2e", "Embodied carbon", "kg CO2e"),
    ("energy_renewable_pct", "Renewable share", "percent"),
    ("offsets_retired_kg_co2e", "Offsets retired (disclosed)", "kg CO2e"),
]


def load_profiles(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    profiles = payload["profiles"] if isinstance(payload, dict) else payload
    return {p["id"]: p for p in profiles}


def load_assignments(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle)]
    rows.sort(key=lambda r: (r["rater_id"], int(r["position"])))
    return rows


def assign_arms(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Assign each (rater, profile) pair to an arm, balanced on both margins.

    Two constraints pull against each other: every rater must carry an equal
    split of the two conditions (so within-rater effects cannot masquerade as
    condition effects), and every profile must be seen roughly equally often
    under each condition (so the H2 per-profile pairing is not dominated by one
    arm). A deterministic greedy pass satisfies both: raters are processed in
    order, and each rater contributes its baseline half to whichever of its
    profiles is currently most starved of baseline ratings.

    Each rater's profiles are disjoint across arms, so no rater ever assesses
    the same profile twice and recall cannot contaminate the contrast.
    """
    by_rater: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_rater.setdefault(row["rater_id"], []).append(row)

    baseline_seen: dict[str, int] = {}
    module_seen: dict[str, int] = {}
    out: list[dict[str, str]] = []

    for rater_id in sorted(by_rater):
        rater_rows = by_rater[rater_id]
        target_baseline = len(rater_rows) // 2
        # Most baseline-starved profiles first; profile id breaks ties so the
        # assignment is reproducible byte for byte.
        ranked = sorted(
            rater_rows,
            key=lambda r: (
                baseline_seen.get(r["profile_id"], 0) - module_seen.get(r["profile_id"], 0),
                baseline_seen.get(r["profile_id"], 0),
                r["profile_id"],
            ),
        )
        baseline_ids = {r["profile_id"] for r in ranked[:target_baseline]}

        half = len(rater_rows) // 2
        for position_index, row in enumerate(rater_rows):
            arm = BASELINE if row["profile_id"] in baseline_ids else MODULE
            if arm == BASELINE:
                baseline_seen[row["profile_id"]] = baseline_seen.get(row["profile_id"], 0) + 1
            else:
                module_seen[row["profile_id"]] = module_seen.get(row["profile_id"], 0) + 1
            enriched = dict(row)
            enriched["arm"] = arm
            enriched["block"] = "first" if position_index < half else "second"
            out.append(enriched)
    return out


def _fmt(value: object) -> str:
    if value is None:
        return "not reported"
    if isinstance(value, float):
        text = f"{value:.4f}".rstrip("0").rstrip(".")
        return text if text else "0"
    return str(value)


def measurement_table(profile: dict) -> list[str]:
    """Raw measurement table. Shown in BOTH arms - it is the shared stimulus."""
    metrics = profile["assessment"].get("metrics", {})
    lines = ["| Quantity | Value | Unit |", "| --- | ---: | --- |"]
    for key, label, unit in METRIC_LABELS:
        if metrics.get(key) is None:
            continue
        lines.append(f"| {label} | {_fmt(metrics[key])} | {unit} |")
    return lines


def boundary_block(profile: dict) -> list[str]:
    assessment = profile["assessment"]
    boundary = assessment.get("boundary_json") or {}
    lines = [
        f"- Lifecycle phase: {assessment.get('lifecycle_phase', 'not reported')}",
        f"- Functional unit: {assessment.get('functional_unit', 'not reported')}",
    ]
    if assessment.get("period_start") or assessment.get("period_end"):
        lines.append(
            f"- Measurement period: {assessment.get('period_start', '?')} to "
            f"{assessment.get('period_end', '?')}"
        )
    if isinstance(boundary, dict):
        for key, value in boundary.items():
            lines.append(f"- {str(key).replace('_', ' ').capitalize()}: {_fmt(value)}")
    return lines


def render_profile(profile: dict, arm: str, position: int) -> list[str]:
    """Render one profile for a rater packet.

    Baseline arm: description, boundary, raw measurements, and the measurement
    source narrative. No confidence score, no tier, no matrix, no recommendation,
    no control-coverage table.

    Module arm: everything above plus the full FairMind-E output.
    """
    assessment = profile["assessment"]
    expected = profile["expected"]
    lines: list[str] = []
    lines.append(f"## Item {position}: {profile['title']}")
    lines.append("")
    lines.append(f"Profile reference: {profile['id']} (arm: {arm})")
    lines.append("")

    description = profile["description"]
    paragraphs = description if isinstance(description, list) else [description]
    for paragraph in paragraphs:
        lines.append(str(paragraph))
        lines.append("")

    lines.append("### Declared boundary")
    lines.append("")
    lines.extend(boundary_block(profile))
    lines.append("")

    lines.append("### Reported measurements")
    lines.append("")
    lines.extend(measurement_table(profile))
    lines.append("")

    lines.append("### Measurement source as submitted")
    lines.append("")
    lines.append(f"- Stated source: {assessment.get('measurement_source', 'not stated')}")
    if assessment.get("uncertainty_pct") is not None:
        lines.append(f"- Stated uncertainty: {_fmt(assessment['uncertainty_pct'])} percent")
    else:
        lines.append("- Stated uncertainty: not reported")
    if assessment.get("intensity_vs_baseline") is not None:
        lines.append(
            f"- Intensity versus the team's declared baseline: "
            f"{_fmt(assessment['intensity_vs_baseline'])}x"
        )
    lines.append("")

    mitigations = assessment.get("mitigations_json") or []
    if mitigations:
        lines.append("### Proposed mitigations")
        lines.append("")
        for item in mitigations:
            if not isinstance(item, dict):
                continue
            bits = [str(item.get("description", "unspecified"))]
            if item.get("target_date"):
                bits.append(f"target date {item['target_date']}")
            if item.get("owner"):
                bits.append(f"owner {item['owner']}")
            if item.get("expected_reduction_pct") is not None:
                bits.append(f"expected reduction {_fmt(item['expected_reduction_pct'])} percent")
            lines.append(f"- {'; '.join(bits)}")
        lines.append("")

    exception = assessment.get("exception")
    if isinstance(exception, dict) and exception:
        lines.append("### Requested exception")
        lines.append("")
        lines.append(f"- Owner: {_fmt(exception.get('owner'))}")
        lines.append(f"- Expiry: {_fmt(exception.get('expiry'))}")
        lines.append(f"- Rationale: {_fmt(exception.get('rationale'))}")
        lines.append("")

    if arm == MODULE:
        lines.append("### FairMind-E assessment output")
        lines.append("")
        lines.append(f"- Provenance class: {expected['provenance_class']}")
        lines.append(
            f"- Evidence confidence: {_fmt(expected['confidence_score'])} "
            f"(band: {expected['confidence_band']})"
        )
        lines.append(f"- Impact tier: {expected['risk_tier']}")
        lines.append(
            f"- Decision-matrix position: {expected['risk_tier']} impact x "
            f"{expected['confidence_band']} confidence"
        )
        lines.append(f"- Module recommendation: {expected['recommendation']}")
        lines.append(
            f"- Approval blocking: {'yes' if expected['approval_blocking'] else 'no'}"
        )
        lines.append("")
        lines.append("ENV control coverage as computed by the module:")
        lines.append("")
        lines.append("| Control | Requirement | Status |")
        lines.append("| --- | --- | --- |")
        for code in ENV_CONTROLS:
            status = expected["coverage"].get(code, "missing")
            lines.append(f"| {code} | {ENV_CONTROL_LABELS[code]} | {status} |")
        lines.append("")
        lines.append(
            f"Coverage rate: {_fmt(expected['coverage_rate'])} of applicable controls."
        )
        lines.append("")

    lines.append("### Your assessment")
    lines.append("")
    lines.append(f"Record your answers for item {position} ({profile['id']}) in the form.")
    lines.append("")
    lines.append("1. Release recommendation: go / conditional_go / no_go")
    lines.append(
        "2. Which ENV controls would you require as evidence before release? "
        "Select every control you would demand (ENV-1 to ENV-6)."
    )
    lines.append("3. How confident are you in this decision? (1 = not at all, 5 = very)")
    if arm == MODULE:
        lines.append(
            "4. Manipulation check: did this item display an evidence confidence score? yes / no"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def build_packet(rater_id: str, role: str, rows: list[dict[str, str]], profiles: dict) -> str:
    lines: list[str] = []
    lines.append(f"# FairMind-E reviewer panel: packet {rater_id}")
    lines.append("")
    lines.append(f"Role group: {role}")
    lines.append(f"Items: {len(rows)}")
    lines.append("")
    lines.append(
        "Work through the items in the order printed. Do not skip ahead, do not "
        "revisit an earlier item after moving on, and do not discuss the items "
        "with other reviewers until the study closes. Some items include an "
        "automated assessment summary and some do not; both kinds are part of "
        "the study, and an item without one is not an error or an omission."
    )
    lines.append("")
    lines.append(
        "Assume in every case that you are the governance reviewer who must "
        "decide whether this system may be released, and that the submission in "
        "front of you is the complete environmental evidence the team has filed."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    for row in rows:
        profile = profiles[row["profile_id"]]
        lines.extend(render_profile(profile, row["arm"], int(row["position"])))
    return "\n".join(lines).rstrip() + "\n"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build(check_only: bool = False) -> dict[str, object]:
    profiles_path = RESEARCH_DIR / "profiles" / "profiles.json"
    plan_path = PANEL_DIR / "assignment_plan.csv"
    profiles = load_profiles(profiles_path)
    assignments = assign_arms(load_assignments(plan_path))

    # Integrity checks that must hold for the analysis to be computable.
    problems: list[str] = []
    per_profile_arms: dict[str, dict[str, int]] = {}
    per_rater_profiles: dict[str, list[str]] = {}
    for row in assignments:
        profile_id = row["profile_id"]
        if profile_id not in profiles:
            problems.append(f"assignment references unknown profile {profile_id}")
            continue
        counts = per_profile_arms.setdefault(profile_id, {BASELINE: 0, MODULE: 0})
        counts[row["arm"]] += 1
        per_rater_profiles.setdefault(row["rater_id"], []).append(profile_id)

    for rater_id, seen in per_rater_profiles.items():
        if len(seen) != len(set(seen)):
            problems.append(f"{rater_id} sees a repeated profile across arms")
    for profile_id, counts in sorted(per_profile_arms.items()):
        if counts[BASELINE] < 2 or counts[MODULE] < 2:
            problems.append(
                f"{profile_id} has too few ratings per arm "
                f"(baseline {counts[BASELINE]}, module {counts[MODULE]})"
            )

    summary: dict[str, object] = {
        "raters": len(per_rater_profiles),
        "profiles": len(per_profile_arms),
        "assignments": len(assignments),
        "arm_counts": per_profile_arms,
        "problems": problems,
    }
    if check_only:
        return summary
    if problems:
        return summary

    # Extended assignment plan with arms.
    write_csv(
        PANEL_DIR / "assignment_plan_arms.csv",
        ["rater_id", "role", "position", "profile_id", "arm", "block"],
        [
            {
                "rater_id": r["rater_id"],
                "role": r["role"],
                "position": r["position"],
                "profile_id": r["profile_id"],
                "arm": r["arm"],
                "block": r["block"],
            }
            for r in assignments
        ],
    )

    # Gold checklist: the H2 denominator, one row per profile per control.
    write_csv(
        PANEL_DIR / "gold_checklists.csv",
        ["profile_id", "control", "applicable", "requirement"],
        [
            {
                "profile_id": profile_id,
                "control": code,
                "applicable": "yes",
                "requirement": ENV_CONTROL_LABELS[code],
            }
            for profile_id in sorted(profiles)
            for code in ENV_CONTROLS
        ],
    )

    # Per-rater packets.
    packets_dir = PANEL_DIR / "packets"
    packets_dir.mkdir(exist_ok=True)
    by_rater: dict[str, list[dict[str, str]]] = {}
    for row in assignments:
        by_rater.setdefault(row["rater_id"], []).append(row)
    for rater_id, rows in sorted(by_rater.items()):
        role = rows[0]["role"]
        (packets_dir / f"{rater_id}.md").write_text(
            build_packet(rater_id, role, rows, profiles), encoding="utf-8"
        )

    summary["packets_written"] = len(by_rater)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the FairMind-E panel instrument")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the design without writing any files",
    )
    args = parser.parse_args(argv)

    summary = build(check_only=args.check)
    problems = summary.get("problems") or []
    print(
        f"raters: {summary['raters']} | profiles: {summary['profiles']} | "
        f"assignments: {summary['assignments']}"
    )
    balanced = summary["arm_counts"]
    if isinstance(balanced, dict):
        spread = sorted({(c[BASELINE], c[MODULE]) for c in balanced.values()})
        print(f"per-profile (baseline, module) splits: {spread}")
    if problems:
        for problem in problems:
            print(f"PROBLEM: {problem}", file=sys.stderr)
        return 1
    if args.check:
        print("design check passed; no files written")
    else:
        print(f"wrote {summary.get('packets_written')} packets, arms plan, gold checklists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
