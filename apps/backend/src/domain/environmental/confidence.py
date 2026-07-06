"""
Evidence-confidence scoring.

Maps the *provenance* of an environmental measurement to a numeric confidence
score in [0.0, 1.0] and a coarse band (measured / estimated / unknown). This is
the distinguishing primitive of FairMind-E: we gate on whether the carbon number
can be *trusted*, not just on its magnitude.

Confidence bands (used by the decision matrix columns):
    measured   score >= 0.70
    estimated  0.35 <= score < 0.70
    unknown    score < 0.35

Provenance -> confidence ranges. The lower the human/assumption content of the
measurement, the higher the trust:

    hardware telemetry (IPMI / RAPL / NVIDIA-SMI)        0.85 - 1.00
    cloud billing API (AWS / GCP / Azure)               0.70 - 0.85
    tool-estimated (CodeCarbon / EcoLogits / Green Algo) 0.50 - 0.70
    vendor-reported (TDP x runtime)                      0.35 - 0.55
    manual FLOP estimate                                 0.20 - 0.40
    unknown / undisclosed                                0.00

These ranges are part of the paper's confidence-mapping table; keep code and
paper in sync.
"""

from __future__ import annotations

# Canonical measurement-source keys -> (min_confidence, max_confidence).
CONFIDENCE_RANGES: dict[str, tuple[float, float]] = {
    "hardware_telemetry": (0.85, 1.00),
    "cloud_api": (0.70, 0.85),
    "tool_estimated": (0.50, 0.70),
    "vendor_reported": (0.35, 0.55),
    "manual_estimate": (0.20, 0.40),
    "unknown": (0.0, 0.0),
}

# Common aliases callers may pass, normalised to a canonical source key.
_SOURCE_ALIASES: dict[str, str] = {
    "hardware": "hardware_telemetry",
    "telemetry": "hardware_telemetry",
    "ipmi": "hardware_telemetry",
    "rapl": "hardware_telemetry",
    "nvidia_smi": "hardware_telemetry",
    "nvidia-smi": "hardware_telemetry",
    "cloud": "cloud_api",
    "cloud_billing": "cloud_api",
    "billing_api": "cloud_api",
    "aws": "cloud_api",
    "gcp": "cloud_api",
    "azure": "cloud_api",
    "tool": "tool_estimated",
    "codecarbon": "tool_estimated",
    "ecologits": "tool_estimated",
    "green_algorithms": "tool_estimated",
    "vendor": "vendor_reported",
    "tdp": "vendor_reported",
    "manual": "manual_estimate",
    "flop_estimate": "manual_estimate",
    "manual_flop": "manual_estimate",
    "undisclosed": "unknown",
    "none": "unknown",
    "": "unknown",
}

# Band thresholds. Exposed for tests and the API benchmarks endpoint.
MEASURED_THRESHOLD = 0.70
ESTIMATED_THRESHOLD = 0.35


def normalize_source(source: str | None) -> str:
    """Return the canonical source key for an arbitrary caller-supplied source."""
    if source is None:
        return "unknown"
    key = str(source).strip().lower().replace(" ", "_").replace("-", "_")
    if key in CONFIDENCE_RANGES:
        return key
    return _SOURCE_ALIASES.get(key, "unknown")


def confidence_range(source: str | None) -> tuple[float, float]:
    """Return the (min, max) confidence range for a measurement source.

    Unrecognised sources fall back to the ``unknown`` range (0.0, 0.0) — an
    undisclosed source is never given the benefit of the doubt.
    """
    return CONFIDENCE_RANGES[normalize_source(source)]


def confidence_from_source(source: str | None) -> float:
    """Map a measurement source to a single representative confidence score.

    Uses the midpoint of the provenance range, rounded to two decimals. Callers
    that have a more precise score (e.g. a tool that reports its own uncertainty)
    should pass that score directly to the decision matrix instead.
    """
    low, high = confidence_range(source)
    return round((low + high) / 2, 2)


def band_from_score(score: float) -> str:
    """Map a numeric confidence score to a band: measured / estimated / unknown."""
    if score >= MEASURED_THRESHOLD:
        return "measured"
    if score >= ESTIMATED_THRESHOLD:
        return "estimated"
    return "unknown"


def get_confidence_band(source: str | None) -> str:
    """Map a measurement source to its confidence band via its representative score."""
    return band_from_score(confidence_from_source(source))
