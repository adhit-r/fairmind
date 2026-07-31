"""
Generate the paper figures from the real measurement data.

Figures are built for print: the Okabe-Ito colourblind-safe palette, distinct
markers and hatching so identity is never carried by colour alone, direct
value labels (the palette validator flags the orange against a light surface
below 3:1 contrast, which obliges visible labels), and no reliance on a hover
layer that a PDF cannot provide.

Run from the backend environment:

    cd apps/backend
    uv run python ../../research/fairmind-e/analysis/make_figures.py
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

# Okabe-Ito, the established colourblind-safe scientific palette.
BLUE = "#0072B2"
ORANGE = "#E69F00"
VERMILLION = "#D55E00"
GREEN = "#009E73"
INK = "#111111"
MUTED = "#666666"
GRID = "#DDDDDD"

METHOD_STYLE = {
    "codecarbon": {"color": BLUE, "marker": "o", "label": "CodeCarbon (tool-estimated)"},
    "manual_flop": {"color": ORANGE, "marker": "s", "label": "Analytic FLOP (manual)"},
}

WORKLOAD_LABEL = {
    "classical_ml_training": "Classical ML",
    "transformer_finetune": "Fine-tune",
    "rag_inference": "RAG",
    "batch_embeddings": "Embeddings",
}

TIERS = ["low", "medium", "high"]
BANDS = ["measured", "estimated", "unknown"]
MATRIX = {
    ("low", "measured"): "go",
    ("low", "estimated"): "go",
    ("low", "unknown"): "conditional",
    ("medium", "measured"): "conditional",
    ("medium", "estimated"): "conditional",
    ("medium", "unknown"): "no-go",
    ("high", "measured"): "conditional",
    ("high", "estimated"): "no-go",
    ("high", "unknown"): "no-go",
}
CELL_FILL = {"go": "#E7F0F7", "conditional": "#FBF0DC", "no-go": "#F2F2F2"}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.5,
            "axes.edgecolor": MUTED,
            "axes.linewidth": 0.6,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "figure.dpi": 200,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
        }
    )


def read_runs(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r.get("method_available") == "true"]


def figure_energy_and_matrix(runs: list[dict[str, str]], out: Path) -> None:
    """Panel A: the two methods disagree. Panel B: same row, different column.

    Sized to the 5.5 inch text block so LaTeX does not rescale it and shrink
    the type below legibility.
    """
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(5.5, 2.6), width_ratios=[1.0, 1.02])
    fig.subplots_adjust(wspace=0.40, top=0.84, bottom=0.24)

    # --- Panel A: per-workload energy by method -------------------------------
    by = defaultdict(lambda: defaultdict(list))
    for r in runs:
        by[r["workload_id"]][r["measurement_method"]].append(float(r["energy_kwh"]))
    workloads = [w for w in WORKLOAD_LABEL if w in by]
    x = range(len(workloads))
    width = 0.30

    for offset, method in ((-width / 2, "codecarbon"), (width / 2, "manual_flop")):
        style = METHOD_STYLE[method]
        means = [statistics.mean(by[w][method]) for w in workloads]
        ax_a.bar(
            [i + offset for i in x], means, width=width, color=style["color"],
            edgecolor="white", linewidth=0.7, label=style["label"], zorder=2,
        )
        for i, w in enumerate(workloads):
            pts = by[w][method]
            ax_a.plot(
                [i + offset] * len(pts), pts, linestyle="none",
                marker=style["marker"], markersize=2.3, markerfacecolor="white",
                markeredgecolor=INK, markeredgewidth=0.45, zorder=3,
            )

    ax_a.set_yscale("log")
    # Headroom so the legend never sits on top of the tallest bar.
    tallest = max(statistics.mean(by[w][m]) for w in workloads for m in by[w])
    ax_a.set_ylim(top=tallest * 6)
    ax_a.set_ylabel("Energy per run (kWh, log)", fontsize=7)
    ax_a.set_xticks(list(x))
    ax_a.set_xticklabels([WORKLOAD_LABEL[w] for w in workloads], fontsize=6.5,
                         rotation=18, ha="right", rotation_mode="anchor")
    ax_a.tick_params(axis="y", labelsize=6.5)
    ax_a.set_axisbelow(True)
    ax_a.yaxis.grid(True, color=GRID, linewidth=0.5)
    ax_a.xaxis.grid(False)
    for side in ("top", "right"):
        ax_a.spines[side].set_visible(False)
    ax_a.legend(frameon=False, loc="upper left", handlelength=1.0, fontsize=6.2,
                borderpad=0.1, labelspacing=0.25)
    ax_a.set_title("(a) Same runs, two methods", loc="left", fontsize=7.5, color=INK, pad=5)

    # --- Panel B: the decision matrix, with the study's positions -------------
    ax_b.set_xlim(-1.35, 3.10)
    ax_b.set_ylim(-0.95, 4.25)
    ax_b.axis("off")

    short = {"go": "go", "conditional": "cond.", "no-go": "no-go"}
    for row, tier in enumerate(TIERS):
        for col, band in enumerate(BANDS):
            outcome = MATRIX[(tier, band)]
            y = 2 - row
            ax_b.add_patch(Rectangle((col, y), 1, 1, facecolor=CELL_FILL[outcome],
                                     edgecolor="white", linewidth=1.2))
            ax_b.text(col + 0.5, y + 0.5, short[outcome], ha="center", va="center",
                      fontsize=6.4, color=INK)

    # Both observed conditions sit in the low-impact row: only the column moved.
    for col, method, colour in ((0, "codecarbon", BLUE), (2, "manual_flop", ORANGE)):
        ax_b.add_patch(Rectangle((col + 0.05, 2.05), 0.90, 0.90, facecolor="none",
                                 edgecolor=colour, linewidth=1.8, zorder=4))
        ax_b.plot(col + 0.85, 2.84, marker=METHOD_STYLE[method]["marker"], markersize=3.6,
                  color=colour, markeredgecolor="white", markeredgewidth=0.5, zorder=5)

    for col, band in enumerate(BANDS):
        ax_b.text(col + 0.5, 3.08, band, ha="center", va="bottom", fontsize=5.5, color=MUTED)
    for row, tier in enumerate(TIERS):
        ax_b.text(-0.14, 2.5 - row, tier, ha="right", va="center", fontsize=6.4, color=MUTED)
    ax_b.text(1.5, 3.44, "evidence confidence", ha="center", fontsize=6.5, color=INK)
    ax_b.text(-1.22, 1.5, "impact", ha="center", va="center", rotation=90,
              fontsize=6.5, color=INK)
    ax_b.text(1.0, -0.72, "20/20 runs: same row, different decision",
              ha="center", fontsize=6.4, color=INK)
    ax_b.text(-1.35, 4.08, "(b) Where they land on the gate", ha="left",
              fontsize=7.5, color=INK)

    fig.savefig(out)
    plt.close(fig)


def figure_mitigations(path: Path, out: Path) -> None:
    """Percent reduction per mitigation pair, including the one that backfired."""
    with path.open(encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("method_available") == "true"]

    items = []
    for r in rows:
        pre, post = float(r["pre_location_kg_co2e"]), float(r["post_location_kg_co2e"])
        items.append(
            (
                f"{r['mitigation_id'].replace('_', ' ')} - {WORKLOAD_LABEL[r['workload_id']].replace(chr(10), ' ')}",
                (pre - post) / pre * 100.0,
            )
        )
    items.sort(key=lambda t: t[1])

    fig, ax = plt.subplots(figsize=(5.5, 2.7))
    labels = [t[0] for t in items]
    values = [t[1] for t in items]
    # The backfiring pair is about -3976%, which would flatten every other bar,
    # so the axis is clipped and that bar carries its true value inside it.
    floor = -120.0
    drawn = [max(v, floor) for v in values]
    colours = [BLUE if v >= 0 else VERMILLION for v in values]

    bars = ax.barh(range(len(values)), drawn, color=colours, edgecolor="white",
                   linewidth=0.7, height=0.66)
    for i, (actual, drawn_v) in enumerate(zip(values, drawn)):
        if actual < floor:
            # Label inside the bar so it cannot collide with the category axis,
            # plus a break marker showing the bar is truncated.
            ax.text(floor + 5, i, f"{actual:,.0f}%", va="center", ha="left",
                    fontsize=6.5, color="white")
            ax.plot([floor], [i], marker="<", markersize=4.5, color=VERMILLION,
                    markeredgecolor="white", markeredgewidth=0.5, clip_on=False)
        else:
            ax.text(drawn_v + 2.5, i, f"{actual:.1f}%", va="center", ha="left",
                    fontsize=6.5, color=INK)

    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.axvline(20, color=GREEN, linewidth=1.0, linestyle=(0, (4, 3)))
    ax.text(22, -0.75, "H4 target: 20%", fontsize=6.3, color=GREEN, va="center")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=6.3)
    ax.set_xlabel("Reduction in carbon intensity (%), positive is better", fontsize=7)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.set_xlim(floor - 6, 116)
    ax.set_ylim(-1.2, len(values) - 0.4)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=GRID, linewidth=0.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.set_title("Ten of eleven mitigations reduced intensity; one inverted the mean",
                 loc="left", fontsize=7.5, color=INK, pad=6)
    fig.savefig(out)
    plt.close(fig)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=root / "results/measurement/m1_runs.csv")
    parser.add_argument(
        "--mitigation", type=Path, default=root / "results/measurement/m1_runs_mitigations.csv"
    )
    parser.add_argument("--out-dir", type=Path, default=root / "paper/ccai2026/figures")
    args = parser.parse_args()

    apply_style()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    runs = read_runs(args.runs)
    f1 = args.out_dir / "fig1_provenance_decides.pdf"
    figure_energy_and_matrix(runs, f1)
    print(f"wrote {f1}")

    f2 = args.out_dir / "fig2_mitigations.pdf"
    figure_mitigations(args.mitigation, f2)
    print(f"wrote {f2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
