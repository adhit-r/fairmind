"""Hand-reviewed terminal result-axis cases shared by contract parity tests."""

from __future__ import annotations

from itertools import product

PASSPORT_TECHNICAL_STATUSES = (
    "succeeded",
    "failed",
    "timed_out",
    "cancelled",
)
EVIDENCE_RESULT_STATUSES = (
    "pending",
    "passed",
    "passed_with_limitations",
    "failed",
    "informational",
    "error",
    "unavailable",
    "insufficient_data",
    "unknown",
)
ALLOWED_EVIDENCE_RESULTS_BY_TECHNICAL_STATUS = {
    "succeeded": frozenset(
        {
            "passed",
            "passed_with_limitations",
            "failed",
            "informational",
            "insufficient_data",
            "unknown",
        }
    ),
    "failed": frozenset({"error", "unavailable", "insufficient_data", "unknown"}),
    "timed_out": frozenset({"error", "unavailable", "insufficient_data", "unknown"}),
    "cancelled": frozenset({"pending", "unavailable", "unknown"}),
}
TERMINAL_RESULT_AXIS_CASES = tuple(
    (
        technical_status,
        evidence_result_status,
        evidence_result_status in ALLOWED_EVIDENCE_RESULTS_BY_TECHNICAL_STATUS[technical_status],
    )
    for technical_status, evidence_result_status in product(
        PASSPORT_TECHNICAL_STATUSES,
        EVIDENCE_RESULT_STATUSES,
    )
)
