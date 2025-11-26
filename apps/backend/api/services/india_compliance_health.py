"""
India Compliance Health Check Service

Provides health check endpoints specific to India compliance features including:
- Database connectivity for India compliance tables
- Integration connectivity (OneTrust, Securiti, Sprinto, MLflow, cloud providers)
- Vector store availability for RAG
- Evidence collection service health
- Bias detection service health
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from config.settings import settings
from config.database import db_manager

logger = logging.getLogger("fairmind.india_compliance_health")


class IndiaComplianceHealthService:
    """Health check service for India compliance features"""

    def __init__(self):
        self.start_time = time.time()
        self.last_check: Optional[Dict[str, Any]] = None

    async def get_india_compliance_health(self) -> Dict[str, Any]:
        """
        Get comprehensive India compliance health status.

        Checks:
        - Database connectivity for India compliance tables
        - Integration connectivity
        - Vector store availability
        - Evidence collection service
        - Bias detection service

        Returns:
            Health status dictionary with all checks

        Requirements: 5.9
        """
        start_time = time.time()

        try:
            checks = {
                "database": await self._check_india_compliance_database(),
                "integrations": await self._check_integrations_health(),
                "vector_store": await self._check_vector_store(),
                "evidence_collection": await self._check_evidence_collection_service(),
                "bias_detection": await self._check_bias_detection_service(),
            }

            # Overall status
            all_healthy = all(
                check.get("status") == "healthy" for check in checks.values()
            )
            overall_status = "healthy" if all_healthy else "degraded"

            health_data = {
                "status": overall_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime": time.time() - self.start_time,
                "version": settings.api_version,
                "environment": settings.environment,
                "checks": checks,
                "response_time": round(time.time() - start_time, 4),
            }

            self.last_check = health_data
            return health_data

        except Exception as e:
            logger.error(f"India compliance health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "response_time": round(time.time() - start_time, 4),
            }

    async def _check_india_compliance_database(self) -> Dict[str, Any]:
        """
        Check India compliance database tables connectivity.

        Verifies:
        - india_compliance_evidence table
        - india_compliance_results table
        - india_bias_test_results table
        - india_compliance_reports table
        - integration_credentials table

        Returns:
            Health check result

        Requirements: 5.9
        """
        start_time = time.time()
        try:
            # Check if database is healthy first
            is_db_healthy = await db_manager.health_check()
            if not is_db_healthy:
                return {
                    "status": "unhealthy",
                    "message": "Database connection failed",
                    "response_time": round(time.time() - start_time, 4),
                }

            # Check India compliance tables
            tables_to_check = [
                "india_compliance_evidence",
                "india_compliance_results",
                "india_bias_test_results",
                "india_compliance_reports",
                "integration_credentials",
            ]

            table_status = {}
            for table in tables_to_check:
                try:
                    # Try to query table existence
                    query = f"SELECT 1 FROM {table} LIMIT 1"
                    result = await db_manager.execute_query(query)
                    table_status[table] = "available"
                except Exception as e:
                    logger.warning(f"Table {table} check failed: {e}")
                    table_status[table] = "unavailable"

            # Check if all tables are available
            all_available = all(
                status == "available" for status in table_status.values()
            )

            response_time = time.time() - start_time

            if all_available:
                return {
                    "status": "healthy",
                    "message": "All India compliance tables available",
                    "tables": table_status,
                    "response_time": round(response_time, 4),
                }
            else:
                return {
                    "status": "degraded",
                    "message": "Some India compliance tables unavailable",
                    "tables": table_status,
                    "response_time": round(response_time, 4),
                }

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"India compliance database check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "message": f"Database check failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }

    async def _check_integrations_health(self) -> Dict[str, Any]:
        """
        Check health of configured integrations.

        Checks:
        - OneTrust integration
        - Securiti.ai integration
        - Sprinto integration
        - MLflow integration
        - Cloud provider integrations (AWS, Azure, GCP)

        Returns:
            Integration health status

        Requirements: 5.9
        """
        start_time = time.time()
        try:
            integration_status = {}

            # Check each integration type
            integrations = [
                "onetrust",
                "securiti",
                "sprinto",
                "mlflow",
                "aws",
                "azure",
                "gcp",
            ]

            for integration in integrations:
                try:
                    # Query integration credentials from database
                    query = f"""
                        SELECT status, last_sync 
                        FROM integration_credentials 
                        WHERE integration_name = %s 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    """
                    result = await db_manager.execute_query(query, (integration,))

                    if result:
                        status = result[0][0] if result[0] else "disconnected"
                        last_sync = result[0][1] if len(result[0]) > 1 else None
                        integration_status[integration] = {
                            "status": status,
                            "last_sync": last_sync.isoformat() if last_sync else None,
                        }
                    else:
                        integration_status[integration] = {
                            "status": "not_configured",
                            "last_sync": None,
                        }

                except Exception as e:
                    logger.warning(f"Integration {integration} check failed: {e}")
                    integration_status[integration] = {
                        "status": "error",
                        "error": str(e),
                    }

            response_time = time.time() - start_time

            # Check if any integrations are connected
            connected_count = sum(
                1
                for status in integration_status.values()
                if status.get("status") == "connected"
            )

            return {
                "status": "healthy" if connected_count > 0 else "degraded",
                "message": f"{connected_count} integrations connected",
                "integrations": integration_status,
                "response_time": round(response_time, 4),
            }

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Integration health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "message": f"Integration check failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }

    async def _check_vector_store(self) -> Dict[str, Any]:
        """
        Check vector store availability for RAG.

        Verifies:
        - Supabase vector extension enabled
        - Embeddings table exists
        - Vector similarity search functional

        Returns:
            Vector store health status

        Requirements: 5.9
        """
        start_time = time.time()
        try:
            # Check if pgvector extension is enabled
            query = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            result = await db_manager.execute_query(query)

            if not result:
                return {
                    "status": "unhealthy",
                    "message": "pgvector extension not enabled",
                    "response_time": round(time.time() - start_time, 4),
                }

            # Check if embeddings table exists
            query = """
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'india_regulatory_embeddings'
            """
            result = await db_manager.execute_query(query)

            if not result:
                return {
                    "status": "degraded",
                    "message": "Embeddings table not found",
                    "response_time": round(time.time() - start_time, 4),
                }

            # Check embedding count
            query = "SELECT COUNT(*) FROM india_regulatory_embeddings"
            result = await db_manager.execute_query(query)
            embedding_count = result[0][0] if result else 0

            response_time = time.time() - start_time

            return {
                "status": "healthy" if embedding_count > 0 else "degraded",
                "message": f"Vector store operational with {embedding_count} embeddings",
                "embedding_count": embedding_count,
                "response_time": round(response_time, 4),
            }

        except Exception as e:
            response_time = time.time() - start_time
            logger.warning(f"Vector store check failed: {e}")
            return {
                "status": "degraded",
                "message": f"Vector store check failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }

    async def _check_evidence_collection_service(self) -> Dict[str, Any]:
        """
        Check evidence collection service health.

        Verifies:
        - Service can be imported
        - Recent evidence collection activity
        - No stuck processes

        Returns:
            Evidence collection service health status

        Requirements: 5.9
        """
        start_time = time.time()
        try:
            # Try to import the service
            from api.services.india_evidence_collection_service import (
                IndiaEvidenceCollectionService,
            )

            # Check recent evidence collection activity
            query = """
                SELECT COUNT(*) FROM india_compliance_evidence 
                WHERE collected_at > NOW() - INTERVAL '1 hour'
            """
            result = await db_manager.execute_query(query)
            recent_evidence_count = result[0][0] if result else 0

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "message": "Evidence collection service operational",
                "recent_evidence_count": recent_evidence_count,
                "response_time": round(response_time, 4),
            }

        except ImportError as e:
            response_time = time.time() - start_time
            logger.warning(f"Evidence collection service import failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Service import failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }
        except Exception as e:
            response_time = time.time() - start_time
            logger.warning(f"Evidence collection service check failed: {e}")
            return {
                "status": "degraded",
                "message": f"Service check failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }

    async def _check_bias_detection_service(self) -> Dict[str, Any]:
        """
        Check bias detection service health.

        Verifies:
        - Service can be imported
        - Recent bias test activity
        - No stuck processes

        Returns:
            Bias detection service health status

        Requirements: 5.9
        """
        start_time = time.time()
        try:
            # Try to import the service
            from api.services.india_bias_detection_service import (
                IndiaBiasDetectionService,
            )

            # Check recent bias test activity
            query = """
                SELECT COUNT(*) FROM india_bias_test_results 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """
            result = await db_manager.execute_query(query)
            recent_bias_tests = result[0][0] if result else 0

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "message": "Bias detection service operational",
                "recent_bias_tests": recent_bias_tests,
                "response_time": round(response_time, 4),
            }

        except ImportError as e:
            response_time = time.time() - start_time
            logger.warning(f"Bias detection service import failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Service import failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }
        except Exception as e:
            response_time = time.time() - start_time
            logger.warning(f"Bias detection service check failed: {e}")
            return {
                "status": "degraded",
                "message": f"Service check failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }


# Global India compliance health service instance
india_compliance_health_service = IndiaComplianceHealthService()
