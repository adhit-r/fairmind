"""Bundled grid carbon-intensity data for the FairMind-E measurement harness.

DATA STATUS: PLACEHOLDER. Every number in this module is a development-time
placeholder with representative magnitudes only, compiled 2026 from public
summaries of 2023-vintage annual grid averages. None of these values may be
cited in the paper or in any compliance artifact. Before the real measurement
study is reported, replace this table with figures from an authoritative,
versioned source (for example Ember Yearly Electricity Data or IEA emission
factors), record the exact source edition in ``DATA_SOURCE_NOTE``, and drop
the PLACEHOLDER marker. Rows derived from this module always carry
``provenance_class=manual``; the placeholder status is additionally repeated
in the row notes so the labeling survives into the CSV.

Two datasets:

- ``GRID_INTENSITY_G_PER_KWH``: static annual-average location-based and
  market-based intensity per region (gCO2e/kWh). Used by the manual_flop
  method and the region_shift mitigation.
- ``HOURLY_SHAPE_MULTIPLIERS``: a generic 24-value diurnal shape (solar dip
  around midday, evening peak) applied to a region's base intensity. Used by
  the time_shift mitigation. The shape is illustrative, not measured.
"""

from __future__ import annotations

DATA_SOURCE_YEAR = 2023
DATA_SOURCE_NOTE = (
    "PLACEHOLDER grid-intensity table (representative magnitudes, compiled 2026 "
    "from public summaries of 2023 annual averages; NOT citable). Replace with "
    "an authoritative versioned source before reporting the real study."
)

# Region ISO-3166 alpha-3 code -> annual-average intensity in gCO2e/kWh.
# "location" is the physical grid average; "market" is a contractual-mix
# placeholder (differs from location where renewable procurement is common).
GRID_INTENSITY_G_PER_KWH: dict[str, dict[str, float]] = {
    "IND": {"location": 713.0, "market": 713.0},
    "USA": {"location": 369.0, "market": 300.0},
    "DEU": {"location": 381.0, "market": 290.0},
    "FRA": {"location": 56.0, "market": 52.0},
    "SWE": {"location": 41.0, "market": 30.0},
}

DEFAULT_REGION = "IND"

# Generic diurnal shape: multiplier on the region's base location intensity,
# indexed by local hour 0-23. Mean is close to 1.0; midday solar depresses
# intensity, the evening ramp raises it. PLACEHOLDER shape, not measured.
HOURLY_SHAPE_MULTIPLIERS: tuple[float, ...] = (
    1.04, 1.02, 1.00, 0.99, 0.98, 0.99,  # 00-05
    1.01, 1.03, 1.02, 0.97, 0.90, 0.84,  # 06-11
    0.80, 0.78, 0.80, 0.85, 0.92, 1.02,  # 12-17
    1.12, 1.18, 1.16, 1.12, 1.09, 1.06,  # 18-23
)


def intensities_for(region: str) -> dict[str, float]:
    """Return {"location": ..., "market": ...} for a region code.

    Raises KeyError for unknown regions; callers surface the known set in the
    error path rather than guessing a value.
    """

    if region not in GRID_INTENSITY_G_PER_KWH:
        known = ", ".join(sorted(GRID_INTENSITY_G_PER_KWH))
        raise KeyError(f"region {region!r} not in placeholder table ({known})")
    return dict(GRID_INTENSITY_G_PER_KWH[region])


def hourly_location_intensity(region: str, hour: int) -> float:
    """Location intensity for a region at a local hour, via the bundled shape."""

    if not 0 <= hour <= 23:
        raise ValueError(f"hour must be 0..23, got {hour}")
    base = intensities_for(region)["location"]
    return base * HOURLY_SHAPE_MULTIPLIERS[hour]
