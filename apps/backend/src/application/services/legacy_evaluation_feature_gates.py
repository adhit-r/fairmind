"""Default-deny capability gates for legacy evaluation mutations.

The v1 workflow intentionally remains readable for compatibility, but these
capabilities must not become active merely because an older client sends their
shape.  Each flag requires the literal string ``true`` so accidental truthy
configuration values cannot enable a higher-risk mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


FAIRMIND_WORKER_FLAG = "FAIRMIND_ASSURANCE_LEGACY_FAIRMIND_WORKER_ENABLED"
EVIDENCE_LINKING_FLAG = "FAIRMIND_ASSURANCE_LEGACY_EVIDENCE_LINKING_ENABLED"


def _explicitly_enabled(environment: Mapping[str, str], name: str) -> bool:
    return environment.get(name) == "true"


@dataclass(frozen=True)
class LegacyEvaluationFeatureGates:
    """Release controls for mutations not backed by the V2 assurance kernel."""

    fairmind_worker_enabled: bool = False
    evidence_linking_enabled: bool = False

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> "LegacyEvaluationFeatureGates":
        values = os.environ if environment is None else environment
        return cls(
            fairmind_worker_enabled=_explicitly_enabled(values, FAIRMIND_WORKER_FLAG),
            evidence_linking_enabled=_explicitly_enabled(values, EVIDENCE_LINKING_FLAG),
        )
