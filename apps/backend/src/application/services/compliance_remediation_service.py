"""
Compliance Remediation Service

Handles remediation planning and tracking for compliance gaps.
Integrates with AI-powered gap analysis and provides step-by-step
remediation guidance.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from src.infrastructure.db.database.models import (
    ComplianceRemediationPlan,
    ComplianceViolation,
)
from config.database import db_manager

logger = logging.getLogger(__name__)


class RemediationStep:
    """Represents a single remediation step"""

    def __init__(
        self,
        step_number: int,
        action: str,
        description: str,
        effort_hours: Optional[float] = None,
        owner: Optional[str] = None,
    ):
        self.step_number = step_number
        self.action = action
        self.description = description
        self.effort_hours = effort_hours
        self.owner = owner

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            "step_number": self.step_number,
            "action": self.action,
            "description": self.description,
            "effort_hours": self.effort_hours,
            "owner": self.owner,
        }


class ComplianceRemediationService:
    """Service for managing compliance remediation plans"""

    async def create_remediation_plan(
        self,
        db: Session,
        framework: str,
        gap_id: str,
        gap_description: str,
        severity: str,
        remediation_steps: List[Dict[str, Any]],
        estimated_effort_hours: float,
        legal_citations: List[str],
        success_criteria: List[str],
        model_id: Optional[str] = None,
    ) -> ComplianceRemediationPlan:
        """
        Create a new remediation plan for a compliance gap.

        Args:
            db: Database session
            framework: Compliance framework name
            gap_id: ID of the compliance gap
            gap_description: Description of the gap
            severity: Severity level (critical, high, medium, low)
            remediation_steps: List of remediation steps with actions and descriptions
            estimated_effort_hours: Estimated effort in hours
            legal_citations: Legal/regulatory citations
            success_criteria: Criteria for successful remediation
            model_id: Optional model ID reference

        Returns:
            Created ComplianceRemediationPlan object
        """
        try:
            plan_id = str(uuid.uuid4())

            plan = ComplianceRemediationPlan(
                id=plan_id,
                framework=framework,
                gap_id=gap_id,
                gap_description=gap_description,
                model_id=model_id,
                severity=severity,
                remediation_steps=remediation_steps,
                estimated_effort_hours=estimated_effort_hours,
                legal_citations=legal_citations,
                success_criteria=success_criteria,
                generated_by="ai",
                generated_at=datetime.utcnow(),
                status="pending",
            )

            db.add(plan)
            db.commit()
            db.refresh(plan)

            logger.info(f"Created remediation plan {plan_id} for gap {gap_id} in {framework}")
            return plan

        except Exception as e:
            logger.error(f"Error creating remediation plan: {e}", exc_info=True)
            db.rollback()
            raise

    async def get_remediation_plan(
        self,
        db: Session,
        plan_id: str,
    ) -> Optional[ComplianceRemediationPlan]:
        """
        Get a remediation plan by ID.

        Args:
            db: Database session
            plan_id: Plan ID

        Returns:
            ComplianceRemediationPlan or None
        """
        try:
            return db.query(ComplianceRemediationPlan).filter(
                ComplianceRemediationPlan.id == plan_id
            ).first()
        except Exception as e:
            logger.error(f"Error retrieving remediation plan: {e}")
            return None

    async def list_remediation_plans(
        self,
        db: Session,
        framework: Optional[str] = None,
        status: Optional[str] = None,
        gap_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 25,
    ) -> tuple[List[ComplianceRemediationPlan], int]:
        """
        List remediation plans with optional filtering.

        Args:
            db: Database session
            framework: Filter by framework name
            status: Filter by status (pending, in_progress, completed)
            gap_id: Filter by gap ID
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (list of plans, total count)
        """
        try:
            query = db.query(ComplianceRemediationPlan)

            if framework:
                query = query.filter(ComplianceRemediationPlan.framework == framework)
            if status:
                query = query.filter(ComplianceRemediationPlan.status == status)
            if gap_id:
                query = query.filter(ComplianceRemediationPlan.gap_id == gap_id)

            total = query.count()
            plans = query.order_by(ComplianceRemediationPlan.created_at.desc()).offset(offset).limit(
                limit
            ).all()

            return plans, total

        except Exception as e:
            logger.error(f"Error listing remediation plans: {e}")
            return [], 0

    async def update_remediation_status(
        self,
        db: Session,
        plan_id: str,
        status: str,
        evidence_links: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update the status of a remediation plan.

        Args:
            db: Database session
            plan_id: Plan ID
            status: New status (pending, in_progress, completed)
            evidence_links: Links to evidence of remediation
            notes: Additional notes

        Returns:
            True if successful
        """
        try:
            plan = await self.get_remediation_plan(db, plan_id)
            if not plan:
                logger.warning(f"Remediation plan {plan_id} not found")
                return False

            plan.status = status
            if evidence_links:
                plan.evidence_links = evidence_links
            if notes:
                plan.notes = notes

            # Update timestamps based on status
            if status == "in_progress" and not plan.started_at:
                plan.started_at = datetime.utcnow()
            elif status == "completed" and not plan.completed_at:
                plan.completed_at = datetime.utcnow()

            plan.updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"Updated remediation plan {plan_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating remediation status: {e}")
            db.rollback()
            return False

    async def get_remediation_plan_summary(
        self,
        db: Session,
        plan_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a summary of remediation plan progress and metrics.

        Args:
            db: Database session
            plan_id: Plan ID

        Returns:
            Summary dict or None
        """
        try:
            plan = await self.get_remediation_plan(db, plan_id)
            if not plan:
                return None

            total_steps = len(plan.remediation_steps) if plan.remediation_steps else 0
            completion_percentage = 0

            if plan.status == "completed":
                completion_percentage = 100
            elif plan.status == "in_progress":
                completion_percentage = 50
            elif plan.status == "pending":
                completion_percentage = 0

            return {
                "plan_id": plan.id,
                "framework": plan.framework,
                "gap_id": plan.gap_id,
                "status": plan.status,
                "severity": plan.severity,
                "total_steps": total_steps,
                "estimated_effort_hours": plan.estimated_effort_hours,
                "completion_percentage": completion_percentage,
                "started_at": plan.started_at.isoformat() if plan.started_at else None,
                "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
                "success_criteria": plan.success_criteria,
                "evidence_count": len(plan.evidence_links) if plan.evidence_links else 0,
            }

        except Exception as e:
            logger.error(f"Error getting remediation summary: {e}")
            return None

    async def auto_generate_remediation_steps(
        self,
        violation_type: str,
        severity: str,
        framework: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate remediation steps for a specific violation.

        This is a template-based approach that can be enhanced with AI.

        Args:
            violation_type: Type of violation
            severity: Severity level
            framework: Compliance framework

        Returns:
            List of remediation steps
        """
        # Template-based remediation steps
        steps = []

        # Common initial steps for all violations
        steps.append(
            RemediationStep(
                step_number=1,
                action="Impact Assessment",
                description=f"Assess the impact and scope of the {violation_type} violation",
                effort_hours=4,
                owner="Compliance Team",
            ).to_dict()
        )

        # Framework-specific steps
        if "consent" in violation_type.lower():
            steps.extend([
                RemediationStep(
                    step_number=2,
                    action="Design Consent Mechanism",
                    description="Create user-facing consent form and workflow",
                    effort_hours=16,
                    owner="Frontend Team",
                ).to_dict(),
                RemediationStep(
                    step_number=3,
                    action="Implement Consent Tracking",
                    description="Add consent records to database with timestamp tracking",
                    effort_hours=12,
                    owner="Backend Team",
                ).to_dict(),
            ])

        elif "data retention" in violation_type.lower():
            steps.extend([
                RemediationStep(
                    step_number=2,
                    action="Define Retention Policy",
                    description="Document data retention requirements per framework",
                    effort_hours=8,
                    owner="Compliance Team",
                ).to_dict(),
                RemediationStep(
                    step_number=3,
                    action="Implement Deletion Process",
                    description="Build automated data deletion workflow",
                    effort_hours=20,
                    owner="Backend Team",
                ).to_dict(),
            ])

        elif "transparency" in violation_type.lower():
            steps.extend([
                RemediationStep(
                    step_number=2,
                    action="Create Documentation",
                    description="Document model behavior and decision process",
                    effort_hours=12,
                    owner="Data Science Team",
                ).to_dict(),
                RemediationStep(
                    step_number=3,
                    action="Build Dashboard",
                    description="Create user-facing transparency dashboard",
                    effort_hours=24,
                    owner="Frontend Team",
                ).to_dict(),
            ])

        # Final verification step
        steps.append(
            RemediationStep(
                step_number=len(steps) + 1,
                action="Verification & Testing",
                description="Verify remediation meets compliance requirements",
                effort_hours=8,
                owner="QA Team",
            ).to_dict()
        )

        return steps


# Global instance
compliance_remediation_service = ComplianceRemediationService()
