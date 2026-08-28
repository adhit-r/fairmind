"""Framework-free contracts for database-authoritative evidence freshness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EvidenceFreshnessClassification:
    """One exact result returned by the versioned database classifier.

    ``recorded_freshness_status`` remains the immutable admission-time
    snapshot. ``effective_freshness_status`` is the operational status at the
    database-owned ``evaluated_at`` instant.
    """

    classification_status: str
    freshness_contract_version: str
    recorded_freshness_status: str | None
    effective_freshness_status: str | None
    evaluated_at: datetime
    effective_at: datetime | None
    expiring_at: datetime | None
    reason_codes: tuple[str, ...]
    decision_eligible: bool | None


__all__ = ["EvidenceFreshnessClassification"]
