import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.models import ComplianceSchedule, ComplianceViolation, AIBOMDocument
from database.connection import db_manager
from core.container import inject, provide

from domain.reports.services.report_generator_service import ReportGeneratorService
from domain.models.services.model_test_service import ModelTestService
from src.infrastructure.email.compliance_notifier import compliance_notifier, NotificationChannel

logger = logging.getLogger(__name__)

class ComplianceAutomationService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.report_generator = inject(ReportGeneratorService)
        self.model_test_service = inject(ModelTestService)
        self._scheduler_started = False

    async def start_scheduler(self) -> None:
        """Start scheduler during app startup when event loop is available."""
        if self._scheduler_started:
            return
        try:
            asyncio.get_running_loop()
            self.scheduler.start()
            self._scheduler_started = True
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

    async def create_schedule(
        self,
        db: Session,
        framework: str,
        frequency: str,
        recipients: List[str],
        filters: Dict[str, Any]
    ) -> ComplianceSchedule:
        """Create a new compliance report schedule"""
        await self.start_scheduler()
        
        # Calculate next run based on frequency
        now = datetime.utcnow()
        next_run = now + timedelta(days=1) # Default to tomorrow
        
        if frequency == "daily":
            trigger = CronTrigger(hour=0, minute=0) # Midnight
        elif frequency == "weekly":
            trigger = CronTrigger(day_of_week='mon', hour=0, minute=0) # Monday midnight
        elif frequency == "monthly":
            trigger = CronTrigger(day=1, hour=0, minute=0) # 1st of month
        else:
            # Default fallback
            trigger = CronTrigger(hour=0, minute=0)

        schedule_id = str(uuid.uuid4())
        
        schedule = ComplianceSchedule(
            id=schedule_id,
            framework=framework,
            frequency=frequency,
            recipients=recipients,
            filters=filters,
            next_run=next_run, # Placeholder, actual scheduling handled by APScheduler
            is_active=True
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        # Add job to scheduler
        self.scheduler.add_job(
            self.generate_automated_report,
            trigger=trigger,
            args=[schedule_id],
            id=schedule_id,
            replace_existing=True
        )
        
        logger.info(f"Created compliance schedule {schedule_id} for {framework}")
        return schedule

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
                # For now, we'll fetch all models, but in production this should use schedule.filters
                models = db.query(AIBOMDocument).all()

                generated_reports = []
                overall_violations = 0
                critical_violations = 0

                for model in models:
                    # 2. Run compliance checks / Generate Report
                    # We'll generate a compliance certificate for each model

                    model_data = {
                        "name": model.name,
                        "version": model.version,
                        "model_type": model.model_type,
                        "author": model.author or "Unknown"
                    }

                    # Mock compliance data - in real world this comes from recent tests
                    compliance_data = {
                        "framework": schedule.framework,
                        "status": "Compliant" if (model.fairness_score or 0) > 0.8 else "Non-Compliant",
                        "requirements": [
                            {"name": "Bias Assessment", "status": "Pass" if (model.bias_score or 1) < 0.2 else "Fail", "evidence": True},
                            {"name": "Data Privacy", "status": "Pass", "evidence": True},
                            {"name": "Transparency", "status": "Pass", "evidence": True}
                        ]
                    }

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
                        overall_score = (
                            sum((m.fairness_score or 0) for m in models) / len(models) * 100
                            if models else 0
                        )

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
                                ComplianceViolation.framework == schedule.framework,
                                ComplianceViolation.resolved == False
                            ).all()),
                            critical_count=len(db.query(ComplianceViolation).filter(
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

    async def check_compliance_violations(self, db: Session, model_id: str) -> List[ComplianceViolation]:
        """Check for compliance violations for a specific model"""
        logger.info(f"Checking compliance violations for model {model_id}")
        
        violations = []
        
        # 1. Run Bias Test to get latest metrics
        # We'll use the ModelTestService to run a fresh test
        try:
            test_results = await self.model_test_service.run_bias_test(model_id=model_id)
            metrics = test_results.get("metrics", {})
            overall_score = test_results.get("score", 0.0)
            
            # 2. Check against thresholds
            # Threshold: Fairness Score < 0.8 is a violation
            if overall_score < 0.8:
                violation = ComplianceViolation(
                    id=str(uuid.uuid4()),
                    model_id=model_id,
                    framework="General Fairness",
                    violation_type="Low Fairness Score",
                    severity="high",
                    description=f"Model fairness score {overall_score:.2f} is below threshold of 0.8",
                    detected_at=datetime.utcnow(),
                    resolved=False
                )
                db.add(violation)
                violations.append(violation)
                
            # Check specific metrics if available
            # Example: Disparate Impact < 0.8
            for metric_name, metric_data in metrics.items():
                # This depends on the structure of metrics returned by bias service
                # Assuming simple structure for now
                pass

        except Exception as e:
            logger.error(f"Error checking compliance for model {model_id}: {e}")
            
        db.commit()
        return violations

    async def list_schedules(self, db: Session) -> List[ComplianceSchedule]:
        return db.query(ComplianceSchedule).all()

    async def list_violations(self, db: Session) -> List[ComplianceViolation]:
        return db.query(ComplianceViolation).filter(ComplianceViolation.resolved == False).all()

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

    async def get_automation_status(self, db: Session) -> Dict[str, Any]:
        """Get current status of compliance automation system"""
        try:
            active_schedules = db.query(ComplianceSchedule).filter(
                ComplianceSchedule.is_active == True
            ).count()

            pending_violations = db.query(ComplianceViolation).filter(
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
