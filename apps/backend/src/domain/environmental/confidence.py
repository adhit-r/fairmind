"""
Evidence-confidence scoring.

Maps the *provenance class* of an environmental measurement to a numeric
confidence score in [0.0, 1.0] and a coarse band (measured / estimated /
unknown). Provenance is categorical and separate from quantified uncertainty.

Confidence bands (used by the decision matrix columns):
    measured   score >= 0.70
    estimated  0.35 <= score < 0.70
    unknown    score < 0.35

Provenance -> confidence ranges:

    measured        0.85 - 1.00
    tool_estimated  0.60 - 0.85
    vendor_reported 0.40 - 0.60
    manual          0.20 - 0.40
    unknown         0.00

Vendor-reported evidence is capped at 0.60. Offsets and RECs never improve
confidence.
"""

from __future__ import annotations

# Canonical provenance class keys -> (min_confidence, max_confidence).
CONFIDENCE_RANGES: dict[str, tuple[float, float]] = {
    "measured": (0.85, 1.00),
    "tool_estimated": (0.60, 0.85),
    "vendor_reported": (0.40, 0.60),
    "manual": (0.20, 0.40),
    "unknown": (0.0, 0.0),
}

# Common aliases callers may pass, normalised to a canonical provenance class.
_SOURCE_ALIASES: dict[str, str] = {
    "hardware": "measured",
    "hardware_telemetry": "measured",
    "telemetry": "measured",
    "metered": "measured",
    "metered_feed": "measured",
    "ipmi": "measured",
    "rapl": "measured",
    "nvidia_smi": "measured",
    "nvidia-smi": "measured",
    "cloud": "vendor_reported",
    "cloud_api": "vendor_reported",
    "cloud_billing": "vendor_reported",
    "billing_api": "vendor_reported",
    "aws": "vendor_reported",
    "gcp": "vendor_reported",
    "azure": "vendor_reported",
    "tool": "tool_estimated",
    "codecarbon": "tool_estimated",
    "ecologits": "tool_estimated",
    "green_algorithms": "tool_estimated",
    "vendor": "vendor_reported",
    "provider": "vendor_reported",
    "cloud_provider": "vendor_reported",
    "tdp": "vendor_reported",
    "manual_estimate": "manual",
    "flop_estimate": "manual",
    "manual_flop": "manual",
    "undisclosed": "unknown",
    "none": "unknown",
    "": "unknown",
}

# Band thresholds. Exposed for tests and the API benchmarks endpoint.
MEASURED_THRESHOLD = 0.70
ESTIMATED_THRESHOLD = 0.35


def normalize_source(source: str | None) -> str:
    """Return the canonical provenance class for a caller-supplied source."""
    if source is None:
        return "unknown"
    key = str(source).strip().lower().replace(" ", "_").replace("-", "_")
    if key in CONFIDENCE_RANGES:
        return key
    return _SOURCE_ALIASES.get(key, "unknown")


def normalize_provenance(provenance_class: str | None) -> str:
    """Return the canonical FairMind-E provenance class."""
    return normalize_source(provenance_class)


def confidence_range(source: str | None) -> tuple[float, float]:
    """Return the (min, max) confidence range for a provenance class.

    Unrecognised sources fall back to the ``unknown`` range (0.0, 0.0) — an
    undisclosed source is never given the benefit of the doubt.
    """
    return CONFIDENCE_RANGES[normalize_source(source)]


def confidence_from_source(source: str | None) -> float:
    """Map a provenance class to a single representative confidence score.

    Uses the midpoint of the provenance range, rounded to two decimals.
    """
    low, high = confidence_range(source)
    return round((low + high) / 2, 2)


def cap_confidence_for_provenance(score: float | None, provenance_class: str | None) -> float:
    """Apply provenance caps to a caller-supplied confidence score."""
    provenance = normalize_provenance(provenance_class)
    if provenance == "unknown":
        return 0.0
    if score is None:
        return confidence_from_source(provenance)
    bounded = max(0.0, min(float(score), 1.0))
    _, high = CONFIDENCE_RANGES[provenance]
    return round(min(bounded, high), 4)


def band_from_score(score: float) -> str:
    """Map a numeric confidence score to a band: measured / estimated / unknown."""
    if score >= MEASURED_THRESHOLD:
        return "measured"
    if score >= ESTIMATED_THRESHOLD:
        return "estimated"
    return "unknown"


def get_confidence_band(source: str | None) -> str:
    """Map a provenance class to its confidence band via its representative score."""
    return band_from_score(confidence_from_source(source))
