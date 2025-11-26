"""
India Compliance Metrics Collection Service

Collects and tracks metrics for India compliance features:
- Compliance check latency
- Integration success/failure rates
- AI automation usage
- Evidence collection counts
- Bias detection metrics

Metrics are stored in database for monitoring and alerting.

Requirements: 7.7, 8.6
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

from config.database import db_manager

logger = logging.getLogger("fairmind.india_compliance_metrics")


class MetricType(str, Enum):
    """Types of metrics collected"""
    COMPLIANCE_CHECK_LATENCY = "compliance_check_latency"
    INTEGRATION_SUCCESS_RATE = "integration_success_rate"
    INTEGRATION_FAILURE_RATE = "integration_failure_rate"
    AI_AUTOMATION_USAGE = "ai_automation_usage"
    EVIDENCE_COLLECTION_COUNT = "evidence_collection_count"
    BIAS_DETECTION_COUNT = "bias_detection_count"
    COMPLIANCE_SCORE = "compliance_score"
    FRAMEWORK_EVALUATION_TIME = "framework_evaluation_time"


class IndiaComplianceMetricsService:
    """Service for collecting and tracking India compliance metrics"""

    def __init__(self):
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.buffer_size = 100
        self.last_flush = time.time()
        self.flush_interval = 60  # Flush every 60 seconds

    async def record_compliance_check(
        self,
        system_id: str,
        framework: str,
        latency_ms: float,
        status: str,
        requirements_met: int,
        total_requirements: int,
        compliance_score: float,
    ) -> None:
        """
        Record compliance check metrics.

        Args:
            system_id: System being checked
            framework: Framework used (DPDP, NITI Aayog, etc.)
            latency_ms: Check latency in milliseconds
            status: Check status (passed, failed, degraded)
            requirements_met: Number of requirements met
            total_requirements: Total requirements
            compliance_score: Overall compliance score

        Requirements: 7.7
        """
        try:
            metrics = {
                "metric_type": MetricType.COMPLIANCE_CHECK_LATENCY,
                "system_id": system_id,
                "framework": framework,
                "latency_ms": latency_ms,
                "status": status,
                "requirements_met": requirements_met,
                "total_requirements": total_requirements,
                "compliance_score": compliance_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self._record_metric(metrics)

            logger.info(
                f"Recorded compliance check: {framework} for {system_id} "
                f"(latency: {latency_ms}ms, score: {compliance_score})"
            )

        except Exception as e:
            logger.error(f"Failed to record compliance check metric: {e}", exc_info=True)

    async def record_integration_sync(
        self,
        integration_name: str,
        success: bool,
        latency_ms: float,
        evidence_count: int,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record integration sync metrics.

        Args:
            integration_name: Name of integration (onetrust, securiti, etc.)
            success: Whether sync was successful
            latency_ms: Sync latency in milliseconds
            evidence_count: Number of evidence items collected
            error_message: Error message if sync failed

        Requirements: 7.7, 8.6
        """
        try:
            metric_type = (
                MetricType.INTEGRATION_SUCCESS_RATE
                if success
                else MetricType.INTEGRATION_FAILURE_RATE
            )

            metrics = {
                "metric_type": metric_type,
                "integration_name": integration_name,
                "success": success,
                "latency_ms": latency_ms,
                "evidence_count": evidence_count,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self._record_metric(metrics)

            status = "successful" if success else "failed"
            logger.info(
                f"Recorded integration sync: {integration_name} {status} "
                f"(latency: {latency_ms}ms, evidence: {evidence_count})"
            )

        except Exception as e:
            logger.error(f"Failed to record integration sync metric: {e}", exc_info=True)

    async def record_ai_automation_usage(
        self,
        system_id: str,
        automation_type: str,
        latency_ms: float,
        tokens_used: int,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record AI automation usage metrics.

        Tracks:
        - Gap analysis
        - Remediation plan generation
        - Policy generation
        - Compliance Q&A

        Args:
            system_id: System using automation
            automation_type: Type of automation (gap_analysis, remediation, policy, qa)
            latency_ms: Automation latency in milliseconds
            tokens_used: LLM tokens used
            success: Whether automation succeeded
            error_message: Error message if failed

        Requirements: 8.6
        """
        try:
            metrics = {
                "metric_type": MetricType.AI_AUTOMATION_USAGE,
                "system_id": system_id,
                "automation_type": automation_type,
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
                "success": success,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self._record_metric(metrics)

            logger.info(
                f"Recorded AI automation: {automation_type} for {system_id} "
                f"(latency: {latency_ms}ms, tokens: {tokens_used})"
            )

        except Exception as e:
            logger.error(f"Failed to record AI automation metric: {e}", exc_info=True)

    async def record_evidence_collection(
        self,
        system_id: str,
        control_id: str,
        evidence_count: int,
        latency_ms: float,
        success: bool,
    ) -> None:
        """
        Record evidence collection metrics.

        Args:
            system_id: System collecting evidence
            control_id: Control being executed
            evidence_count: Number of evidence items collected
            latency_ms: Collection latency in milliseconds
            success: Whether collection succeeded

        Requirements: 7.7
        """
        try:
            metrics = {
                "metric_type": MetricType.EVIDENCE_COLLECTION_COUNT,
                "system_id": system_id,
                "control_id": control_id,
                "evidence_count": evidence_count,
                "latency_ms": latency_ms,
                "success": success,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self._record_metric(metrics)

            logger.info(
                f"Recorded evidence collection: {control_id} for {system_id} "
                f"(count: {evidence_count}, latency: {latency_ms}ms)"
            )

        except Exception as e:
            logger.error(f"Failed to record evidence collection metric: {e}", exc_info=True)

    async def record_bias_detection(
        self,
        system_id: str,
        model_id: str,
        bias_type: str,
        bias_detected: bool,
        latency_ms: float,
        affected_groups: int,
    ) -> None:
        """
        Record bias detection metrics.

        Args:
            system_id: System running bias detection
            model_id: Model being tested
            bias_type: Type of bias (caste, religion, linguistic, regional, intersectional)
            bias_detected: Whether bias was detected
            latency_ms: Detection latency in milliseconds
            affected_groups: Number of affected demographic groups

        Requirements: 7.7
        """
        try:
            metrics = {
                "metric_type": MetricType.BIAS_DETECTION_COUNT,
                "system_id": system_id,
                "model_id": model_id,
                "bias_type": bias_type,
                "bias_detected": bias_detected,
                "latency_ms": latency_ms,
                "affected_groups": affected_groups,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self._record_metric(metrics)

            logger.info(
                f"Recorded bias detection: {bias_type} for {model_id} "
                f"(detected: {bias_detected}, latency: {latency_ms}ms)"
            )

        except Exception as e:
            logger.error(f"Failed to record bias detection metric: {e}", exc_info=True)

    async def get_compliance_check_metrics(
        self,
        system_id: Optional[str] = None,
        framework: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get compliance check metrics.

        Args:
            system_id: Filter by system ID
            framework: Filter by framework
            hours: Time window in hours

        Returns:
            Compliance check metrics

        Requirements: 7.7
        """
        try:
            query = """
                SELECT 
                    metric_type,
                    system_id,
                    framework,
                    AVG(latency_ms) as avg_latency,
                    MIN(latency_ms) as min_latency,
                    MAX(latency_ms) as max_latency,
                    AVG(compliance_score) as avg_score,
                    COUNT(*) as check_count,
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed_count
                FROM india_compliance_metrics
                WHERE metric_type = %s
                AND timestamp > NOW() - INTERVAL '%s hours'
            """

            params = [MetricType.COMPLIANCE_CHECK_LATENCY.value, hours]

            if system_id:
                query += " AND system_id = %s"
                params.append(system_id)

            if framework:
                query += " AND framework = %s"
                params.append(framework)

            query += " GROUP BY metric_type, system_id, framework"

            result = await db_manager.execute_query(query, tuple(params))

            if not result:
                return {
                    "metric_type": "compliance_check_latency",
                    "data": [],
                    "summary": {
                        "total_checks": 0,
                        "avg_latency_ms": 0,
                        "passed_checks": 0,
                    },
                }

            # Format results
            metrics_data = []
            total_checks = 0
            total_latency = 0
            passed_checks = 0

            for row in result:
                metrics_data.append({
                    "system_id": row[1],
                    "framework": row[2],
                    "avg_latency_ms": float(row[3]) if row[3] else 0,
                    "min_latency_ms": float(row[4]) if row[4] else 0,
                    "max_latency_ms": float(row[5]) if row[5] else 0,
                    "avg_score": float(row[6]) if row[6] else 0,
                    "check_count": int(row[7]) if row[7] else 0,
                    "passed_count": int(row[8]) if row[8] else 0,
                })
                total_checks += int(row[7]) if row[7] else 0
                total_latency += float(row[3]) * int(row[7]) if row[3] and row[7] else 0
                passed_checks += int(row[8]) if row[8] else 0

            avg_latency = total_latency / total_checks if total_checks > 0 else 0

            return {
                "metric_type": "compliance_check_latency",
                "time_window_hours": hours,
                "data": metrics_data,
                "summary": {
                    "total_checks": total_checks,
                    "avg_latency_ms": round(avg_latency, 2),
                    "passed_checks": passed_checks,
                    "success_rate": round(
                        (passed_checks / total_checks * 100) if total_checks > 0 else 0, 2
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get compliance check metrics: {e}", exc_info=True)
            return {
                "error": str(e),
                "metric_type": "compliance_check_latency",
            }

    async def get_integration_metrics(
        self,
        integration_name: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get integration sync metrics.

        Args:
            integration_name: Filter by integration name
            hours: Time window in hours

        Returns:
            Integration metrics

        Requirements: 7.7
        """
        try:
            query = """
                SELECT 
                    integration_name,
                    success,
                    AVG(latency_ms) as avg_latency,
                    MIN(latency_ms) as min_latency,
                    MAX(latency_ms) as max_latency,
                    AVG(evidence_count) as avg_evidence,
                    COUNT(*) as sync_count
                FROM india_compliance_metrics
                WHERE metric_type IN (%s, %s)
                AND timestamp > NOW() - INTERVAL '%s hours'
            """

            params = [
                MetricType.INTEGRATION_SUCCESS_RATE.value,
                MetricType.INTEGRATION_FAILURE_RATE.value,
                hours,
            ]

            if integration_name:
                query += " AND integration_name = %s"
                params.append(integration_name)

            query += " GROUP BY integration_name, success"

            result = await db_manager.execute_query(query, tuple(params))

            if not result:
                return {
                    "metric_type": "integration_metrics",
                    "data": [],
                    "summary": {
                        "total_syncs": 0,
                        "success_rate": 0,
                        "avg_latency_ms": 0,
                    },
                }

            # Format results
            metrics_data = []
            total_syncs = 0
            successful_syncs = 0

            for row in result:
                metrics_data.append({
                    "integration_name": row[0],
                    "success": bool(row[1]),
                    "avg_latency_ms": float(row[2]) if row[2] else 0,
                    "min_latency_ms": float(row[3]) if row[3] else 0,
                    "max_latency_ms": float(row[4]) if row[4] else 0,
                    "avg_evidence_count": float(row[5]) if row[5] else 0,
                    "sync_count": int(row[6]) if row[6] else 0,
                })
                total_syncs += int(row[6]) if row[6] else 0
                if row[1]:  # success = True
                    successful_syncs += int(row[6]) if row[6] else 0

            success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0

            return {
                "metric_type": "integration_metrics",
                "time_window_hours": hours,
                "data": metrics_data,
                "summary": {
                    "total_syncs": total_syncs,
                    "successful_syncs": successful_syncs,
                    "success_rate": round(success_rate, 2),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get integration metrics: {e}", exc_info=True)
            return {
                "error": str(e),
                "metric_type": "integration_metrics",
            }

    async def get_ai_automation_metrics(
        self,
        system_id: Optional[str] = None,
        automation_type: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get AI automation usage metrics.

        Args:
            system_id: Filter by system ID
            automation_type: Filter by automation type
            hours: Time window in hours

        Returns:
            AI automation metrics

        Requirements: 8.6
        """
        try:
            query = """
                SELECT 
                    automation_type,
                    system_id,
                    success,
                    AVG(latency_ms) as avg_latency,
                    SUM(tokens_used) as total_tokens,
                    AVG(tokens_used) as avg_tokens,
                    COUNT(*) as usage_count
                FROM india_compliance_metrics
                WHERE metric_type = %s
                AND timestamp > NOW() - INTERVAL '%s hours'
            """

            params = [MetricType.AI_AUTOMATION_USAGE.value, hours]

            if system_id:
                query += " AND system_id = %s"
                params.append(system_id)

            if automation_type:
                query += " AND automation_type = %s"
                params.append(automation_type)

            query += " GROUP BY automation_type, system_id, success"

            result = await db_manager.execute_query(query, tuple(params))

            if not result:
                return {
                    "metric_type": "ai_automation_usage",
                    "data": [],
                    "summary": {
                        "total_usage": 0,
                        "total_tokens": 0,
                        "success_rate": 0,
                    },
                }

            # Format results
            metrics_data = []
            total_usage = 0
            total_tokens = 0
            successful_usage = 0

            for row in result:
                metrics_data.append({
                    "automation_type": row[0],
                    "system_id": row[1],
                    "success": bool(row[2]),
                    "avg_latency_ms": float(row[3]) if row[3] else 0,
                    "total_tokens": int(row[4]) if row[4] else 0,
                    "avg_tokens": float(row[5]) if row[5] else 0,
                    "usage_count": int(row[6]) if row[6] else 0,
                })
                total_usage += int(row[6]) if row[6] else 0
                total_tokens += int(row[4]) if row[4] else 0
                if row[2]:  # success = True
                    successful_usage += int(row[6]) if row[6] else 0

            success_rate = (successful_usage / total_usage * 100) if total_usage > 0 else 0

            return {
                "metric_type": "ai_automation_usage",
                "time_window_hours": hours,
                "data": metrics_data,
                "summary": {
                    "total_usage": total_usage,
                    "successful_usage": successful_usage,
                    "success_rate": round(success_rate, 2),
                    "total_tokens": total_tokens,
                    "avg_tokens_per_usage": round(
                        total_tokens / total_usage if total_usage > 0 else 0, 2
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get AI automation metrics: {e}", exc_info=True)
            return {
                "error": str(e),
                "metric_type": "ai_automation_usage",
            }

    async def _record_metric(self, metric_data: Dict[str, Any]) -> None:
        """
        Record a metric to the database.

        Args:
            metric_data: Metric data to record
        """
        try:
            # Add to buffer
            self.metrics_buffer.append(metric_data)

            # Flush if buffer is full or interval has passed
            if (
                len(self.metrics_buffer) >= self.buffer_size
                or time.time() - self.last_flush > self.flush_interval
            ):
                await self._flush_metrics()

        except Exception as e:
            logger.error(f"Failed to record metric: {e}", exc_info=True)

    async def _flush_metrics(self) -> None:
        """Flush buffered metrics to database."""
        if not self.metrics_buffer:
            return

        try:
            # Insert metrics into database
            for metric in self.metrics_buffer:
                query = """
                    INSERT INTO india_compliance_metrics (
                        metric_type, system_id, framework, latency_ms, status,
                        requirements_met, total_requirements, compliance_score,
                        integration_name, success, evidence_count, error_message,
                        automation_type, tokens_used, control_id, model_id,
                        bias_type, bias_detected, affected_groups, timestamp
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """

                params = (
                    metric.get("metric_type"),
                    metric.get("system_id"),
                    metric.get("framework"),
                    metric.get("latency_ms"),
                    metric.get("status"),
                    metric.get("requirements_met"),
                    metric.get("total_requirements"),
                    metric.get("compliance_score"),
                    metric.get("integration_name"),
                    metric.get("success"),
                    metric.get("evidence_count"),
                    metric.get("error_message"),
                    metric.get("automation_type"),
                    metric.get("tokens_used"),
                    metric.get("control_id"),
                    metric.get("model_id"),
                    metric.get("bias_type"),
                    metric.get("bias_detected"),
                    metric.get("affected_groups"),
                    metric.get("timestamp"),
                )

                await db_manager.execute_query(query, params)

            # Clear buffer
            self.metrics_buffer.clear()
            self.last_flush = time.time()

            logger.debug(f"Flushed {len(self.metrics_buffer)} metrics to database")

        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}", exc_info=True)


# Global metrics service instance
india_compliance_metrics_service = IndiaComplianceMetricsService()
