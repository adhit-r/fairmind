"""Default-deny capability gates for legacy evaluation mutations.

The v1 workflow remains readable for compatibility. Environment values cannot
enable these capabilities: ``from_environment`` always returns the default
disabled gates. Tests may explicitly construct or substitute a non-default
gate to exercise retired compatibility paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class LegacyEvaluationFeatureGates:
    """Release controls for mutations not backed by the V2 assurance kernel."""

    evidence_linking_enabled: bool = False

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> "LegacyEvaluationFeatureGates":
        del environment
        return cls()
