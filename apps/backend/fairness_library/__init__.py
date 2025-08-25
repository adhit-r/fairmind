"""
Standardized Fairness & Bias Library
A single, version-controlled library for all approved fairness metrics and bias detection methods.
"""

__version__ = "1.0.0"
__author__ = "Fairmind AI Governance Team"

from .metrics import (
    demographic_parity_diff,
    equalized_odds_diff,
    equal_opportunity_diff,
    statistical_parity_diff,
    calibration_by_group,
    intersectional_fairness
)

from .llm_bias import (
    weat_score,
    seat_score,
    minimal_pairs_test,
    behavioral_bias_detection,
    embedding_bias_analysis
)

from .monitoring import (
    FairnessMonitor,
    BiasDetector,
    AlertManager,
    DriftDetector
)

from .governance import (
    GovernanceGate,
    PolicyEngine,
    ComplianceChecker,
    AuditLogger
)

from .registry import (
    ModelRegistry,
    DatasetRegistry,
    FairnessReport,
    ModelCard,
    DatasetDatasheet
)

__all__ = [
    # Core metrics
    "demographic_parity_diff",
    "equalized_odds_diff", 
    "equal_opportunity_diff",
    "statistical_parity_diff",
    "calibration_by_group",
    "intersectional_fairness",
    
    # LLM bias detection
    "weat_score",
    "seat_score",
    "minimal_pairs_test",
    "behavioral_bias_detection",
    "embedding_bias_analysis",
    
    # Monitoring
    "FairnessMonitor",
    "BiasDetector", 
    "AlertManager",
    "DriftDetector",
    
    # Governance
    "GovernanceGate",
    "PolicyEngine",
    "ComplianceChecker",
    "AuditLogger",
    
    # Registry
    "ModelRegistry",
    "DatasetRegistry",
    "FairnessReport",
    "ModelCard",
    "DatasetDatasheet"
]
