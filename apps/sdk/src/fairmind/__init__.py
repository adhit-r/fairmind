"""Typed Python client for FairMind."""

__version__ = "0.1.0"

from .client import FairMind, FairMindError, verify_pack  # noqa: E402
from .types import (  # noqa: E402
    Attestation,
    Clause,
    ClauseMap,
    FairnessRun,
    Framework,
    Gate,
    GateCheck,
    MonitoringRun,
    System,
)

__all__ = [
    "FairMind",
    "FairMindError",
    "verify_pack",
    "Attestation",
    "Clause",
    "ClauseMap",
    "FairnessRun",
    "Framework",
    "Gate",
    "GateCheck",
    "MonitoringRun",
    "System",
    "__version__",
]
