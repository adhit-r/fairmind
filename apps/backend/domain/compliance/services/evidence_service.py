"""
Evidence Collection Service.

Handles automated and manual evidence collection for compliance.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
import hashlib
import json

from core.base_service import AsyncBaseService
from core.container import service, ServiceLifetime
from core.exceptions import ValidationError
from core.interfaces import ILogger


class EvidenceType(str, Enum):
    """Types of evidence."""
    TEST_RESULT = "test_result"
    DATASET = "dataset"
    DOCUMENT = "document"
    AUDIT_TRAIL = "audit_trail"
    MANUAL_ATTESTATION = "manual_attestation"
    TECHNICAL_SCAN = "technical_scan"


class EvidenceStatus(str, Enum):
    """Status of evidence."""
    VALID = "valid"
    EXPIRED = "expired"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


@dataclass
class Evidence:
    """Evidence domain model."""
    id: str
    type: EvidenceType
    control_id: str
    framework: str
    collected_at: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    hash: str
    source: str
    status: EvidenceStatus = EvidenceStatus.VALID


@service(lifetime=ServiceLifetime.SINGLETON)
class EvidenceService(AsyncBaseService):
    """
    Evidence collection service.
    
    Migrated to use BaseService and DI.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.evidence_store: Dict[str, Evidence] = {}
        
    async def collect_evidence(
        self,
        control_id: str,
        evidence_type: EvidenceType,
        data: Dict[str, Any],
        framework: str,
        source: str = "automated"
    ) -> Evidence:
        """
        Collect and store evidence.
        """
        self._validate_required(control_id=control_id, data=data)
        
        # Calculate hash
        evidence_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        evidence = Evidence(
            id=f"EV-{control_id}-{datetime.now().timestamp()}",
            type=evidence_type,
            control_id=control_id,
            framework=framework,
            collected_at=datetime.now(),
            data=data,
            metadata={"source": source},
            hash=evidence_hash,
            source=source,
            status=EvidenceStatus.VALID
        )
        
        # Store (in memory for now)
        self.evidence_store[evidence.id] = evidence
        
        self._log_operation(
            "collect_evidence",
            evidence_id=evidence.id,
            type=evidence_type,
            control=control_id
        )
        
        return evidence

    async def get_evidence(self, evidence_id: str) -> Evidence:
        """Get evidence by ID."""
        if evidence_id not in self.evidence_store:
            raise ValidationError(f"Evidence not found: {evidence_id}")
        return self.evidence_store[evidence_id]

    async def list_evidence(self, framework: Optional[str] = None) -> List[Evidence]:
        """List collected evidence."""
        if framework:
            return [e for e in self.evidence_store.values() if e.framework == framework]
        return list(self.evidence_store.values())
