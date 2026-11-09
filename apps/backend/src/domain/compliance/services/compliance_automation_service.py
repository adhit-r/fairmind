import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy.orm import Session
from sqlalchemy import String, cast, select, text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.models import ComplianceSchedule, ComplianceViolation, AIBOMDocument, OrganizationMember
from database.connection import db_manager
from core.container import inject, provide

from domain.reports.services.report_generator_service import ReportGeneratorService
from src.infrastructure.email.compliance_notifier import compliance_notifier, NotificationChannel

logger = logging.getLogger(__name__)

class ComplianceAutomationService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.report_generator = inject(ReportGeneratorService)
        self._scheduler_started = False

    async def start_scheduler(self) -> None:
        """Start scheduler during app startup when event loop is available."""
        if self._scheduler_started:
            return
        try:
            asyncio.get_running_loop()
            self.scheduler.start()
            self._scheduler_started = True
            self.reload_schedules()
            logger.info("Compliance Automation Scheduler started")
        except RuntimeError:
            logger.warning("Could not start compliance scheduler: no running event loop")

    async def stop_scheduler(self) -> None:
        """Stop scheduler during app shutdown."""
        if not self._scheduler_started:
            return
        try:
            self.scheduler.shutdown(wait=False)
            self._scheduler_started = False
            logger.info("Compliance Automation Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping compliance scheduler: {e}")

    @staticmethod
    def _trigger(frequency: str) -> CronTrigger:
        if frequency == "weekly":
            return CronTrigger(day_of_week="mon", hour=0, minute=0)  # Monday midnight
        if frequency == "monthly":
            return CronTrigger(day=1, hour=0, minute=0)  # 1st of month
        return CronTrigger(hour=0, minute=0)  # daily, and the fallback

    def _add_job(self, schedule_id: str, frequency: str) -> None:
        self.scheduler.add_job(
            self.generate_automated_report,
            trigger=self._trigger(frequency),
            args=[schedule_id],
            id=schedule_id,
            replace_existing=True,
        )

    def reload_schedules(self) -> int:
        """Re-register every active schedule row; the scheduler is in-memory, so a restart would otherwise drop them."""
        try:
            with db_manager.get_session() as db:
                rows = db.query(ComplianceSchedule).filter(ComplianceSchedule.is_active == True).all()  # noqa: E712
                for row in rows:
                    self._add_job(row.id, row.frequency)
                logger.info(f"Reloaded {len(rows)} active compliance schedules")
                return len(rows)
        except Exception as e:
            logger.error(f"Could not reload compliance schedules: {e}", exc_info=True)
            return 0

    async def create_schedule(
        self,
        db: Session,
        framework: str,
        frequency: str,
        recipients: List[str],
        filters: Dict[str, Any],
        org_id: Optional[str] = None,
    ) -> ComplianceSchedule:
        """Create a new compliance report schedule"""
        await self.start_scheduler()
        
        next_run = datetime.utcnow() + timedelta(days=1)  # Default to tomorrow

        schedule_id = str(uuid.uuid4())
        
        schedule = ComplianceSchedule(
            id=schedule_id,
            framework=framework,
            frequency=frequency,
            recipients=recipients,
            filters=filters,
            next_run=next_run, # Placeholder, actual scheduling handled by APScheduler
            is_active=True,
            org_id=org_id,
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        self._add_job(schedule_id, frequency)
        
        logger.info(f"Created compliance schedule {schedule_id} for {framework}")
        return schedule

    @staticmethod
    def _compliance_from_evidence(db: Session, schedule: ComplianceSchedule, system_name: str) -> Dict[str, Any]:
        """Requirements read from the release gate over the evidence stored for the governance system of this name.

        Pass only on proven evidence, Fail when measured checks fail, Attested when only a statement is on file,
        Not assessed (evidence False) when nothing is stored. The overall status is Compliant only if every one passes.
        """
        from src.application.services.fairness_run_service import release_gate

        system = db.execute(
            text("SELECT id, risk_tier FROM governance_ai_systems WHERE org_id = :org AND lower(name) = lower(:name) LIMIT 1"),
            {"org": str(schedule.org_id), "name": system_name},
        ).fetchone()
        records = []
        if system:
            for r in db.execute(
                text("SELECT id, evidence_type, content_json, confidence, metadata_json, created_at FROM governance_evidence WHERE system_id = :id"),
                {"id": system[0]},
            ).fetchall():
                load = lambda v: v if isinstance(v, dict) else (json.loads(v) if v else {})
                records.append({"id": r[0], "evidenceType": r[1], "content": load(r[2]), "confidence": r[3], "metadata": load(r[4]), "created_at": r[5]})
        gate = release_gate(system[1] if system else "high", records)
        requirements = []
        for c in gate["checks"]:
            status = "Fail" if c.get("fails") else {"proven": "Pass", "attested": "Attested"}.get(c["state"], "Not assessed")
            requirements.append({"name": c["label"], "status": status, "evidence": c["state"] != "open"})
        statuses = {r["status"] for r in requirements}
        overall = "Non-Compliant" if "Fail" in statuses else "Compliant" if statuses == {"Pass"} else "Not assessed"
        return {"framework": schedule.framework, "status": overall, "requirements": requirements}

    async def generate_automated_report(self, schedule_id: str):
        """Generate and send a scheduled report"""
        logger.info(f"Generating automated report for schedule {schedule_id}")

        try:
            # Create a new DB session for the job
            with db_manager.get_session() as db:
                schedule = db.query(ComplianceSchedule).filter(ComplianceSchedule.id == schedule_id).first()
                if not schedule or not schedule.is_active:
                    logger.warning(f"Schedule {schedule_id} not found or inactive")
                    return

                # 1. Fetch relevant models based on filters
                # Only the schedule's own organisation: AI-BOM documents record their creator,
                # so a model belongs to the organisation its creator is an active member of.
                # (In production this should also use schedule.filters.)
                members = select(cast(OrganizationMember.user_id, String)).where(
                    cast(OrganizationMember.org_id, String) == str(schedule.org_id),
                    OrganizationMember.status == "active",
                )
                models = (
                    db.query(AIBOMDocument).filter(AIBOMDocument.created_by.in_(members)).all()
                    if schedule.org_id
                    else []
                )

                generated_reports = []
                passed = total = 0

                for model in models:
                    # 2. Run compliance checks / Generate Report
                    # We'll generate a compliance certificate for each model

                    model_data = {"name": model.name, "version": model.version}
                    compliance_data = self._compliance_from_evidence(db, schedule, model.name)
                    passed += sum(1 for r in compliance_data["requirements"] if r["status"] == "Pass")
                    total += len(compliance_data["requirements"])

                    try:
                        report_path = await self.report_generator.generate_compliance_certificate(
                            model_data=model_data,
                            compliance_data=compliance_data
                        )
                        generated_reports.append(report_path)
                    except Exception as e:
                        logger.error(f"Failed to generate report for model {model.id}: {e}")

                # 3. Send notifications to recipients
                if schedule.recipients:
                    try:
                        # Calculate metrics
                        overall_score = passed / total * 100 if total else 0

                        compliance_status = "compliant" if overall_score > 80 else (
                            "partial" if overall_score > 60 else "non_compliant"
                        )

                        # Send report ready notification
                        await compliance_notifier.notify_report_ready(
                            recipients=schedule.recipients,
                            framework=schedule.framework,
                            overall_score=overall_score,
                            status=compliance_status,
                            report_id=schedule_id,
                            violation_count=len(db.query(ComplianceViolation).filter(
                                ComplianceViolation.org_id == schedule.org_id,
                                ComplianceViolation.framework == schedule.framework,
                                ComplianceViolation.resolved == False
                            ).all()),
                            critical_count=len(db.query(ComplianceViolation).filter(
                                ComplianceViolation.org_id == schedule.org_id,
                                ComplianceViolation.framework == schedule.framework,
                                ComplianceViolation.severity == "critical",
                                ComplianceViolation.resolved == False
                            ).all()),
                            channels=NotificationChannel.EMAIL,
                        )
                        logger.info(f"Notification sent to {len(schedule.recipients)} recipients")
                    except Exception as e:
                        logger.error(f"Failed to send notification: {e}", exc_info=True)

                # Update last run
                schedule.last_run = datetime.utcnow()
                db.commit()

                logger.info(f"Report generation completed for schedule {schedule_id}")

        except Exception as e:
            logger.error(f"Error in generate_automated_report: {e}", exc_info=True)

    async def list_schedules(self, db: Session, org_id: str) -> List[ComplianceSchedule]:
        return db.query(ComplianceSchedule).filter(ComplianceSchedule.org_id == org_id).all()

    async def list_violations(self, db: Session, org_id: str) -> List[ComplianceViolation]:
        return db.query(ComplianceViolation).filter(
            ComplianceViolation.org_id == org_id, ComplianceViolation.resolved == False
        ).all()

    async def notify_violations(
        self,
        db: Session,
        violations: List[ComplianceViolation],
        framework: str,
        recipients: List[str]
    ) -> bool:
        """
        Send violation notifications to recipients.

        Args:
            db: Database session
            violations: List of violations to notify about
            framework: Compliance framework name
            recipients: Email addresses to notify

        Returns:
            True if notifications sent successfully
        """
        if not violations or not recipients:
            return False

        try:
            # Format violations for email
            violation_data = [
                {
                    "id": v.id,
                    "violation_type": v.violation_type,
                    "severity": v.severity,
                    "description": v.description,
                }
                for v in violations
            ]

            # Send violation alert
            success = await compliance_notifier.notify_violations(
                recipients=recipients,
                violations=violation_data,
                framework=framework,
                channels=NotificationChannel.EMAIL,
            )

            logger.info(f"Violation notifications sent: {success}")
            return success

        except Exception as e:
            logger.error(f"Failed to send violation notifications: {e}", exc_info=True)
            return False

    async def get_automation_status(self, db: Session, org_id: str) -> Dict[str, Any]:
        """Get current status of compliance automation for one organisation"""
        try:
            active_schedules = db.query(ComplianceSchedule).filter(
                ComplianceSchedule.org_id == org_id,
                ComplianceSchedule.is_active == True
            ).count()

            pending_violations = db.query(ComplianceViolation).filter(
                ComplianceViolation.org_id == org_id,
                ComplianceViolation.resolved == False
            ).all()

            critical_violations = len([
                v for v in pending_violations if v.severity == "critical"
            ])

            return {
                "scheduler_running": self._scheduler_started,
                "active_schedules": active_schedules,
                "pending_jobs": len(self.scheduler.get_jobs()) if self._scheduler_started else 0,
                "total_violations": len(pending_violations),
                "critical_violations": critical_violations,
                "reports_generated_today": db.query(ComplianceSchedule).filter(
                    ComplianceSchedule.org_id == org_id,
                    ComplianceSchedule.last_run >= datetime.utcnow().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                ).count(),
                "last_scheduler_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting automation status: {e}", exc_info=True)
            return {
                "error": str(e),
                "scheduler_running": self._scheduler_started,
            }

# Global instance (scheduler lifecycle is managed by FastAPI lifespan hooks)
compliance_automation_service = ComplianceAutomationService()
