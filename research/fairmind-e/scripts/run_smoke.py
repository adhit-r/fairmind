#!/usr/bin/env python3
"""Deterministic FairMind-E smoke harness.

This runner does not measure real workloads. It turns checked-in synthetic
workload configs into reproducible CSV and SVG artifacts for research package
validation.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import pathlib
from typing import Any


PROVENANCE_DEFAULT_CONFIDENCE = {
    "measured": 0.95,
    "tool_estimated": 0.75,
    "vendor_reported": 0.60,
    "manual": 0.30,
    "unknown": 0.00,
}

PROVENANCE_RANGES = {
    "measured": (0.85, 1.00),
    "tool_estimated": (0.60, 0.85),
    "vendor_reported": (0.40, 0.60),
    "manual": (0.20, 0.40),
    "unknown": (0.00, 0.00),
}

CSV_COLUMNS = [
    "workload_id",
    "run_id",
    "method",
    "functional_unit",
    "duration_seconds",
    "energy_kwh",
    "location_carbon_intensity_g_co2e_per_kwh",
    "market_carbon_intensity_g_co2e_per_kwh",
    "carbon_intensity_basis",
    "location_kg_co2e",
    "market_kg_co2e",
    "provenance_class",
    "uncertainty_pct",
    "confidence_score",
    "impact_level",
    "intensity_vs_baseline",
    "risk_tier",
    "recommendation",
    "mitigation_readiness",
    "offsets_retired_kg_co2e",
    "notes",
]


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def confidence_score(provenance_class: str, uncertainty_pct: float) -> float:
    if provenance_class not in PROVENANCE_DEFAULT_CONFIDENCE:
        raise ValueError(f"unknown provenance_class: {provenance_class}")
    if provenance_class == "unknown":
        return 0.0

    base = PROVENANCE_DEFAULT_CONFIDENCE[provenance_class]
    minimum, maximum = PROVENANCE_RANGES[provenance_class]

    # Uncertainty can only move confidence downward within the same provenance
    # class; it can never upgrade evidence to a stronger class.
    penalty = max(0.0, uncertainty_pct - 30.0) / 100.0
    return round(clamp(base - penalty, minimum, maximum), 2)


def confidence_band(confidence: float) -> str:
    if confidence >= 0.75:
        return "strong"
    if confidence >= 0.40:
        return "moderate"
    return "weak"


def recommendation_for(
    impact_level: str, confidence: float, mitigation_readiness: str
) -> str:
    band = confidence_band(confidence)
    has_mitigation = mitigation_readiness == "documented"

    if impact_level == "low":
        return "go" if band == "strong" else "conditional_go"
    if impact_level == "moderate":
        return "conditional_go" if band in {"strong", "moderate"} else "no_go"
    if impact_level == "high":
        if band == "strong" and has_mitigation:
            return "conditional_go"
        return "no_go"
    raise ValueError(f"unknown impact_level: {impact_level}")


def risk_tier_for(impact_level: str, recommendation: str) -> str:
    if recommendation == "go":
        return "low"
    if recommendation == "no_go":
        return "critical"
    if impact_level == "low":
        return "medium"
    return "high"


def assess_record(record: dict[str, Any]) -> dict[str, str]:
    confidence = confidence_score(
        str(record["provenance_class"]), float(record.get("uncertainty_pct", 0.0))
    )
    recommendation = recommendation_for(
        str(record["impact_level"]),
        confidence,
        str(record.get("mitigation_readiness", "none")),
    )
    return {
        "confidence_score": f"{confidence:.2f}",
        "intensity_vs_baseline": format_float(
            float(record.get("intensity_vs_baseline", 0.0)), 2
        ),
        "risk_tier": risk_tier_for(str(record["impact_level"]), recommendation),
        "recommendation": recommendation,
    }


def carbon_kg(energy_kwh: float, carbon_intensity_g_co2e_per_kwh: float) -> float:
    return energy_kwh * carbon_intensity_g_co2e_per_kwh / 1000.0


def format_float(value: float, digits: int) -> str:
    return f"{value:.{digits}f}"


def row_from_record(config: dict[str, Any], record: dict[str, Any]) -> dict[str, str]:
    energy_kwh = float(record["energy_kwh"])
    location_ci = float(record["location_carbon_intensity_g_co2e_per_kwh"])
    market_ci = float(record["market_carbon_intensity_g_co2e_per_kwh"])
    assessment = assess_record(record)

    row = {
        "workload_id": str(config["workload_id"]),
        "run_id": str(config.get("run_id", "smoke")),
        "method": str(record["method"]),
        "functional_unit": str(config["functional_unit"]),
        "duration_seconds": str(int(record["duration_seconds"])),
        "energy_kwh": format_float(energy_kwh, 6),
        "location_carbon_intensity_g_co2e_per_kwh": format_float(location_ci, 1),
        "market_carbon_intensity_g_co2e_per_kwh": format_float(market_ci, 1),
        "carbon_intensity_basis": str(record["carbon_intensity_basis"]),
        "location_kg_co2e": format_float(carbon_kg(energy_kwh, location_ci), 6),
        "market_kg_co2e": format_float(carbon_kg(energy_kwh, market_ci), 6),
        "provenance_class": str(record["provenance_class"]),
        "uncertainty_pct": str(int(record["uncertainty_pct"])),
        "impact_level": str(record["impact_level"]),
        "mitigation_readiness": str(record.get("mitigation_readiness", "none")),
        "offsets_retired_kg_co2e": format_float(
            float(record.get("offsets_retired_kg_co2e", 0.0)), 3
        ),
        "notes": str(record.get("notes", "")),
    }
    row.update(assessment)
    return row


def load_configs(config_dir: pathlib.Path) -> list[dict[str, Any]]:
    configs = []
    for path in sorted(config_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            config = json.load(handle)
        config["_path"] = str(path)
        configs.append(config)
    if not configs:
        raise FileNotFoundError(f"no JSON configs found in {config_dir}")
    return configs


def write_csv(output_root: pathlib.Path, config: dict[str, Any]) -> list[dict[str, str]]:
    rows = [row_from_record(config, record) for record in config["records"]]
    result_dir = output_root / "results" / str(config["workload_id"])
    result_dir.mkdir(parents=True, exist_ok=True)
    csv_path = result_dir / f"{config.get('run_id', 'smoke')}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def svg_bar(
    x: int,
    y: int,
    width: int,
    height: int,
    label: str,
    value_label: str,
    fill: str,
) -> str:
    safe_label = html.escape(label)
    safe_value = html.escape(value_label)
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="#111111" stroke-width="2"/>',
            f'<text x="{x}" y="{y + height + 18}" font-size="12" fill="#111111">{safe_label}</text>',
            f'<text x="{x}" y="{max(20, y - 8)}" font-size="12" fill="#111111">{safe_value}</text>',
        ]
    )


def write_summary_svg(output_root: pathlib.Path, rows: list[dict[str, str]]) -> None:
    plots_dir = output_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        workload = row["workload_id"]
        grouped.setdefault(workload, {"market": 0.0, "confidence": 0.0, "count": 0.0})
        grouped[workload]["market"] += float(row["market_kg_co2e"])
        grouped[workload]["confidence"] += float(row["confidence_score"])
        grouped[workload]["count"] += 1.0

    max_market = max(values["market"] for values in grouped.values()) or 1.0
    colors = ["#0F766E", "#F97316", "#111111", "#14B8A6", "#EAB308"]
    bars = []
    for index, (workload, values) in enumerate(sorted(grouped.items())):
        bar_height = int(170 * values["market"] / max_market)
        x = 58 + index * 138
        y = 250 - bar_height
        average_confidence = values["confidence"] / values["count"]
        label = workload.replace("_", " ")
        value = f'{values["market"]:.3f} kg, c={average_confidence:.2f}'
        bars.append(svg_bar(x, y, 86, bar_height, label, value, colors[index % len(colors)]))

    width = max(760, 120 + len(grouped) * 138)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="330" viewBox="0 0 {width} 330" role="img" aria-label="FairMind-E smoke summary">
<rect width="100%" height="100%" fill="#FFFFFF"/>
<text x="36" y="38" font-size="24" font-family="Arial, sans-serif" font-weight="700" fill="#111111">FairMind-E smoke summary</text>
<text x="36" y="64" font-size="13" font-family="Arial, sans-serif" fill="#333333">Market-based kg CO2e by workload; confidence is averaged across evidence methods.</text>
<line x1="42" y1="252" x2="{width - 36}" y2="252" stroke="#111111" stroke-width="3"/>
{chr(10).join(bars)}
</svg>
"""
    (plots_dir / "fairmind_e_smoke_summary.svg").write_text(svg, encoding="utf-8")


def write_gate_svg(output_root: pathlib.Path, rows: list[dict[str, str]]) -> None:
    counts: dict[str, int] = {"go": 0, "conditional_go": 0, "no_go": 0}
    for row in rows:
        counts[row["recommendation"]] += 1

    total = max(sum(counts.values()), 1)
    bars = []
    labels = ["go", "conditional_go", "no_go"]
    colors = ["#0F766E", "#F97316", "#111111"]
    for index, label in enumerate(labels):
        bar_height = int(160 * counts[label] / total)
        x = 92 + index * 160
        y = 230 - bar_height
        bars.append(svg_bar(x, y, 96, bar_height, label, str(counts[label]), colors[index]))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="620" height="310" viewBox="0 0 620 310" role="img" aria-label="FairMind-E gate outcomes">
<rect width="100%" height="100%" fill="#FFFFFF"/>
<text x="36" y="38" font-size="24" font-family="Arial, sans-serif" font-weight="700" fill="#111111">FairMind-E gate outcomes</text>
<text x="36" y="64" font-size="13" font-family="Arial, sans-serif" fill="#333333">Deterministic smoke records by release recommendation.</text>
<line x1="54" y1="232" x2="550" y2="232" stroke="#111111" stroke-width="3"/>
{chr(10).join(bars)}
</svg>
"""
    plots_dir = output_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    (plots_dir / "fairmind_e_gate_outcomes.svg").write_text(svg, encoding="utf-8")


def run(config_dir: pathlib.Path, output_root: pathlib.Path) -> int:
    all_rows: list[dict[str, str]] = []
    for config in load_configs(config_dir):
        all_rows.extend(write_csv(output_root, config))
    write_summary_svg(output_root, all_rows)
    write_gate_svg(output_root, all_rows)
    return 0


def main(argv: list[str] | None = None) -> int:
    default_root = pathlib.Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=pathlib.Path, default=default_root / "configs")
    parser.add_argument("--output-root", type=pathlib.Path, default=default_root)
    args = parser.parse_args(argv)
    return run(args.config_dir, args.output_root)


if __name__ == "__main__":
    raise SystemExit(main())
