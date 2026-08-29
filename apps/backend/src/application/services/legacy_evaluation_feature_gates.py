"""Default-deny capability gates for legacy evaluation mutations.

The v1 workflow intentionally remains readable for compatibility, but these
capabilities cannot be activated through production environment values. The
field remains injectable only so tests can exercise the historical contract
while every composed API request stays denied.
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
