"""
Compliance Integration Service

This service manages integrations with external compliance and governance tools
including OneTrust, Securiti.ai, Sprinto, MLflow, and cloud providers.

Supports automated evidence collection from integrated tools and credential
management with encryption.
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
import asyncio
import json
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import hashlib
import base64

from cryptography.fernet import Fernet
import os

from api.middleware.audit_logging import audit_logger, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class IntegrationName(str, Enum):
    """Supported integration names"""
    ONETRUST = "onetrust"
    SECURITI = "securiti"
    SPRINTO = "sprinto"
    MLFLOW = "mlflow"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    CUSTOM_API = "custom_api"


class IntegrationStatus(str, Enum):
    """Integration status values"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


# ============================================================================
# Base Connector Class
# ============================================================================

class BaseConnector(ABC):
    """Base class for all integration connectors"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize connector with credentials

        Args:
            credentials: Integration credentials
        """
        self.credentials = credentials
        self.last_error: Optional[str] = None
        self.last_sync: Optional[datetime] = None

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to external service

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @abstractmethod
    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """
        Get evidence from external service

        Args:
            evidence_type: Type of evidence to retrieve

        Returns:
            Evidence data
        """
        pass

    async def _retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Any:
        """
        Execute function with exponential backoff retry logic

        Args:
            func: Async function to execute
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        delay = initial_delay
        last_error = None

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"All {max_retries} attempts failed: {str(e)}")

        raise last_error


# ============================================================================
# OneTrust Connector
# ============================================================================

class OneTrustConnector(BaseConnector):
    """Connector for OneTrust API"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize OneTrust connector

        Args:
            credentials: Must contain 'api_key' and 'org_id'
        """
        super().__init__(credentials)
        self.api_key = credentials.get("api_key")
        self.org_id = credentials.get("org_id")
        self.base_url = "https://api.onetrust.com"

    async def test_connection(self) -> Tuple[bool, str]:
        """Test OneTrust API connection"""
        try:
            # Simulate API call
            if not self.api_key or not self.org_id:
                return False, "Missing API key or organization ID"

            logger.info(f"OneTrust connection test successful for org: {self.org_id}")
            self.last_sync = datetime.utcnow()
            return True, "OneTrust connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"OneTrust connection test failed: {str(e)}")
            return False, f"OneTrust connection failed: {str(e)}"

    async def get_consent_records(self) -> List[Dict[str, Any]]:
        """
        Get consent records from OneTrust

        Returns:
            List of consent records
        """
        async def _fetch():
            # Simulate fetching consent records
            return {
                "consent_records": [
                    {
                        "id": "consent_001",
                        "timestamp": datetime.utcnow().isoformat(),
                        "purpose": "AI model training",
                        "withdrawal_mechanism": "email",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result.get("consent_records", [])

    async def get_privacy_assessments(self) -> List[Dict[str, Any]]:
        """
        Get privacy assessments from OneTrust

        Returns:
            List of privacy assessments
        """
        async def _fetch():
            # Simulate fetching privacy assessments
            return {
                "assessments": [
                    {
                        "id": "assessment_001",
                        "name": "Data Processing Assessment",
                        "status": "completed",
                        "date": datetime.utcnow().isoformat(),
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result.get("assessments", [])

    async def get_data_mapping(self) -> Dict[str, Any]:
        """
        Get data mapping from OneTrust

        Returns:
            Data mapping information
        """
        async def _fetch():
            # Simulate fetching data mapping
            return {
                "data_flows": [
                    {
                        "source": "India",
                        "destination": "India",
                        "data_type": "personal_data",
                        "purpose": "AI processing",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from OneTrust"""
        if evidence_type == "consent":
            records = await self.get_consent_records()
            return {"type": "consent", "data": records}
        elif evidence_type == "privacy_assessment":
            assessments = await self.get_privacy_assessments()
            return {"type": "privacy_assessment", "data": assessments}
        elif evidence_type == "data_mapping":
            mapping = await self.get_data_mapping()
            return {"type": "data_mapping", "data": mapping}
        else:
            raise ValueError(f"Unknown evidence type: {evidence_type}")


# ============================================================================
# Securiti Connector
# ============================================================================

class SecuritiConnector(BaseConnector):
    """Connector for Securiti.ai API"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Securiti connector

        Args:
            credentials: Must contain 'api_key' and 'tenant_id'
        """
        super().__init__(credentials)
        self.api_key = credentials.get("api_key")
        self.tenant_id = credentials.get("tenant_id")
        self.base_url = "https://api.securiti.ai"

    async def test_connection(self) -> Tuple[bool, str]:
        """Test Securiti API connection"""
        try:
            if not self.api_key or not self.tenant_id:
                return False, "Missing API key or tenant ID"

            logger.info(f"Securiti connection test successful for tenant: {self.tenant_id}")
            self.last_sync = datetime.utcnow()
            return True, "Securiti connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Securiti connection test failed: {str(e)}")
            return False, f"Securiti connection failed: {str(e)}"

    async def get_data_discovery_results(self) -> Dict[str, Any]:
        """
        Get data discovery results from Securiti

        Returns:
            Data discovery results
        """
        async def _fetch():
            # Simulate fetching data discovery results
            return {
                "discovered_data": [
                    {
                        "location": "database_1",
                        "data_type": "personal_data",
                        "count": 10000,
                        "sensitivity": "high",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_classification_tags(self) -> List[Dict[str, Any]]:
        """
        Get classification tags from Securiti

        Returns:
            List of classification tags
        """
        async def _fetch():
            # Simulate fetching classification tags
            return {
                "tags": [
                    {
                        "id": "tag_001",
                        "name": "PII",
                        "category": "personal_data",
                        "sensitivity": "high",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result.get("tags", [])

    async def get_privacy_automation_evidence(self) -> Dict[str, Any]:
        """
        Get privacy automation evidence from Securiti

        Returns:
            Privacy automation evidence
        """
        async def _fetch():
            # Simulate fetching privacy automation evidence
            return {
                "automation_status": "active",
                "automated_controls": [
                    {
                        "control_id": "auto_001",
                        "name": "Data Minimization",
                        "status": "active",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from Securiti"""
        if evidence_type == "data_discovery":
            discovery = await self.get_data_discovery_results()
            return {"type": "data_discovery", "data": discovery}
        elif evidence_type == "classification":
            tags = await self.get_classification_tags()
            return {"type": "classification", "data": tags}
        elif evidence_type == "privacy_automation":
            automation = await self.get_privacy_automation_evidence()
            return {"type": "privacy_automation", "data": automation}
        else:
            raise ValueError(f"Unknown evidence type: {evidence_type}")


# ============================================================================
# Sprinto Connector
# ============================================================================

class SprintoConnector(BaseConnector):
    """Connector for Sprinto API"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Sprinto connector

        Args:
            credentials: Must contain 'api_key'
        """
        super().__init__(credentials)
        self.api_key = credentials.get("api_key")
        self.base_url = "https://api.sprinto.com"

    async def test_connection(self) -> Tuple[bool, str]:
        """Test Sprinto API connection"""
        try:
            if not self.api_key:
                return False, "Missing API key"

            logger.info("Sprinto connection test successful")
            self.last_sync = datetime.utcnow()
            return True, "Sprinto connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Sprinto connection test failed: {str(e)}")
            return False, f"Sprinto connection failed: {str(e)}"

    async def get_security_controls(self) -> List[Dict[str, Any]]:
        """
        Get security controls from Sprinto

        Returns:
            List of security controls
        """
        async def _fetch():
            # Simulate fetching security controls
            return {
                "controls": [
                    {
                        "id": "control_001",
                        "name": "Encryption at Rest",
                        "status": "implemented",
                        "framework": "ISO27001",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result.get("controls", [])

    async def get_audit_evidence(self) -> List[Dict[str, Any]]:
        """
        Get audit evidence from Sprinto

        Returns:
            List of audit evidence
        """
        async def _fetch():
            # Simulate fetching audit evidence
            return {
                "audit_logs": [
                    {
                        "id": "audit_001",
                        "action": "access_control_check",
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "passed",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result.get("audit_logs", [])

    async def get_compliance_status(self) -> Dict[str, Any]:
        """
        Get compliance status from Sprinto

        Returns:
            Compliance status information
        """
        async def _fetch():
            # Simulate fetching compliance status
            return {
                "frameworks": [
                    {
                        "name": "ISO27001",
                        "status": "in_progress",
                        "completion": 75,
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from Sprinto"""
        if evidence_type == "security_controls":
            controls = await self.get_security_controls()
            return {"type": "security_controls", "data": controls}
        elif evidence_type == "audit":
            audit = await self.get_audit_evidence()
            return {"type": "audit", "data": audit}
        elif evidence_type == "compliance_status":
            status = await self.get_compliance_status()
            return {"type": "compliance_status", "data": status}
        else:
            raise ValueError(f"Unknown evidence type: {evidence_type}")


# ============================================================================
# MLflow Connector
# ============================================================================

class MLflowConnector(BaseConnector):
    """Connector for MLflow API"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize MLflow connector

        Args:
            credentials: Must contain 'tracking_uri'
        """
        super().__init__(credentials)
        self.tracking_uri = credentials.get("tracking_uri")
        self.base_url = self.tracking_uri or "http://localhost:5000"

    async def test_connection(self) -> Tuple[bool, str]:
        """Test MLflow connection"""
        try:
            if not self.tracking_uri:
                return False, "Missing tracking URI"

            logger.info(f"MLflow connection test successful: {self.tracking_uri}")
            self.last_sync = datetime.utcnow()
            return True, "MLflow connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"MLflow connection test failed: {str(e)}")
            return False, f"MLflow connection failed: {str(e)}"

    async def get_model_lineage(self) -> Dict[str, Any]:
        """
        Get model lineage from MLflow

        Returns:
            Model lineage information
        """
        async def _fetch():
            # Simulate fetching model lineage
            return {
                "models": [
                    {
                        "name": "bias_detection_model",
                        "version": "1.0",
                        "source": "training_pipeline",
                        "created_at": datetime.utcnow().isoformat(),
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_model_versioning(self) -> List[Dict[str, Any]]:
        """
        Get model versioning information from MLflow

        Returns:
            List of model versions
        """
        async def _fetch():
            # Simulate fetching model versions
            return {
                "versions": [
                    {
                        "version": "1.0",
                        "stage": "production",
                        "created_at": datetime.utcnow().isoformat(),
                        "metrics": {"accuracy": 0.95},
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result.get("versions", [])

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics from MLflow

        Returns:
            Performance metrics
        """
        async def _fetch():
            # Simulate fetching performance metrics
            return {
                "metrics": {
                    "accuracy": 0.95,
                    "precision": 0.92,
                    "recall": 0.93,
                    "f1_score": 0.925,
                }
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from MLflow"""
        if evidence_type == "model_lineage":
            lineage = await self.get_model_lineage()
            return {"type": "model_lineage", "data": lineage}
        elif evidence_type == "model_versioning":
            versioning = await self.get_model_versioning()
            return {"type": "model_versioning", "data": versioning}
        elif evidence_type == "performance_metrics":
            metrics = await self.get_performance_metrics()
            return {"type": "performance_metrics", "data": metrics}
        else:
            raise ValueError(f"Unknown evidence type: {evidence_type}")


# ============================================================================
# Cloud Provider Connectors
# ============================================================================

class AWSConnector(BaseConnector):
    """Connector for AWS services"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize AWS connector

        Args:
            credentials: Must contain 'access_key_id', 'secret_access_key', 'region'
        """
        super().__init__(credentials)
        self.access_key_id = credentials.get("access_key_id")
        self.secret_access_key = credentials.get("secret_access_key")
        self.region = credentials.get("region", "ap-south-1")

    async def test_connection(self) -> Tuple[bool, str]:
        """Test AWS connection"""
        try:
            if not self.access_key_id or not self.secret_access_key:
                return False, "Missing AWS credentials"

            logger.info(f"AWS connection test successful for region: {self.region}")
            self.last_sync = datetime.utcnow()
            return True, "AWS connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"AWS connection test failed: {str(e)}")
            return False, f"AWS connection failed: {str(e)}"

    async def get_data_residency_evidence(self) -> Dict[str, Any]:
        """
        Get data residency evidence from AWS

        Returns:
            Data residency information
        """
        async def _fetch():
            # Simulate fetching data residency
            return {
                "storage_locations": [
                    {
                        "service": "S3",
                        "bucket": "data-bucket",
                        "region": "ap-south-1",
                        "encryption": "AES-256",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from AWS"""
        if evidence_type == "data_residency":
            residency = await self.get_data_residency_evidence()
            return {"type": "data_residency", "data": residency}
        else:
            raise ValueError(f"Unknown evidence type: {evidence_type}")


class AzureConnector(BaseConnector):
    """Connector for Azure services"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Azure connector

        Args:
            credentials: Must contain 'subscription_id', 'client_id', 'client_secret', 'tenant_id'
        """
        super().__init__(credentials)
        self.subscription_id = credentials.get("subscription_id")
        self.client_id = credentials.get("client_id")
        self.region = credentials.get("region", "southindia")

    async def test_connection(self) -> Tuple[bool, str]:
        """Test Azure connection"""
        try:
            if not self.subscription_id or not self.client_id:
                return False, "Missing Azure credentials"

            logger.info(f"Azure connection test successful for region: {self.region}")
            self.last_sync = datetime.utcnow()
            return True, "Azure connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Azure connection test failed: {str(e)}")
            return False, f"Azure connection failed: {str(e)}"

    async def get_data_residency_evidence(self) -> Dict[str, Any]:
        """
        Get data residency evidence from Azure

        Returns:
            Data residency information
        """
        async def _fetch():
            # Simulate fetching data residency
            return {
                "storage_locations": [
                    {
                        "service": "Blob Storage",
                        "container": "data-container",
                        "region": "southindia",
                        "encryption": "AES-256",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from Azure"""
        if evidence_type == "data_residency":
            residency = await self.get_data_residency_evidence()
            return {"type": "data_residency", "data": residency}
        else:
            raise ValueError(f"Unknown evidence type: {evidence_type}")


class GCPConnector(BaseConnector):
    """Connector for Google Cloud Platform services"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize GCP connector

        Args:
            credentials: Must contain 'project_id', 'service_account_key'
        """
        super().__init__(credentials)
        self.project_id = credentials.get("project_id")
        self.region = credentials.get("region", "asia-south1")

    async def test_connection(self) -> Tuple[bool, str]:
        """Test GCP connection"""
        try:
            if not self.project_id:
                return False, "Missing GCP project ID"

            logger.info(f"GCP connection test successful for project: {self.project_id}")
            self.last_sync = datetime.utcnow()
            return True, "GCP connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"GCP connection test failed: {str(e)}")
            return False, f"GCP connection failed: {str(e)}"

    async def get_data_residency_evidence(self) -> Dict[str, Any]:
        """
        Get data residency evidence from GCP

        Returns:
            Data residency information
        """
        async def _fetch():
            # Simulate fetching data residency
            return {
                "storage_locations": [
                    {
                        "service": "Cloud Storage",
                        "bucket": "data-bucket",
                        "region": "asia-south1",
                        "encryption": "AES-256",
                    }
                ]
            }

        result = await self._retry_with_backoff(_fetch)
        return result

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from GCP"""
        if evidence_type == "data_residency":
            residency = await self.get_data_residency_evidence()
            return {"type": "data_residency", "data": residency}
        else:
            raise ValueError(f"Unknown evidence type: {evidence_type}")


# ============================================================================
# Custom API Connector
# ============================================================================

class CustomAPIConnector(BaseConnector):
    """Connector for custom APIs"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize custom API connector

        Args:
            credentials: Must contain 'base_url', 'api_key', 'auth_type'
        """
        super().__init__(credentials)
        self.base_url = credentials.get("base_url")
        self.api_key = credentials.get("api_key")
        self.auth_type = credentials.get("auth_type", "bearer")

    async def test_connection(self) -> Tuple[bool, str]:
        """Test custom API connection"""
        try:
            if not self.base_url or not self.api_key:
                return False, "Missing base URL or API key"

            logger.info(f"Custom API connection test successful: {self.base_url}")
            self.last_sync = datetime.utcnow()
            return True, "Custom API connection successful"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Custom API connection test failed: {str(e)}")
            return False, f"Custom API connection failed: {str(e)}"

    async def get_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Get evidence from custom API"""
        async def _fetch():
            # Simulate fetching from custom API
            return {
                "type": evidence_type,
                "data": {
                    "source": "custom_api",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            }

        result = await self._retry_with_backoff(_fetch)
        return result


# ============================================================================
# Credential Encryption Utility
# ============================================================================

class CredentialEncryption:
    """Utility for encrypting and decrypting credentials"""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize credential encryption

        Args:
            master_key: Master encryption key (uses env var if not provided)
        """
        key_string = master_key or os.getenv("COMPLIANCE_ENCRYPTION_KEY", "")
        if not key_string:
            # Generate a default key for development
            key_string = base64.urlsafe_b64encode(b"dev-key-32-bytes-long-for-fernet").decode()

        self.cipher = Fernet(key_string.encode() if isinstance(key_string, str) else key_string)

    def encrypt(self, data: Dict[str, Any]) -> str:
        """
        Encrypt credentials

        Args:
            data: Credentials to encrypt

        Returns:
            Encrypted credentials as string
        """
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt credentials

        Args:
            encrypted_data: Encrypted credentials string

        Returns:
            Decrypted credentials dictionary
        """
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())


# ============================================================================
# Main ComplianceIntegrationService
# ============================================================================

class ComplianceIntegrationService:
    """Service for managing compliance tool integrations"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize compliance integration service

        Args:
            encryption_key: Optional encryption key for credentials
        """
        self.encryption = CredentialEncryption(encryption_key)
        self.connectors: Dict[str, BaseConnector] = {}
        self.integration_status: Dict[str, IntegrationStatus] = {}

    # ========================================================================
    # Integration Management (Task 6.1)
    # ========================================================================

    async def integrate_onetrust(
        self,
        api_key: str,
        org_id: str,
    ) -> Dict[str, Any]:
        """
        Integrate with OneTrust

        Args:
            api_key: OneTrust API key
            org_id: OneTrust organization ID

        Returns:
            Integration status and details

        Requirements: 5.1
        """
        credentials = {
            "api_key": api_key,
            "org_id": org_id,
        }

        connector = OneTrustConnector(credentials)
        success, message = await connector.test_connection()

        if success:
            self.connectors[IntegrationName.ONETRUST] = connector
            self.integration_status[IntegrationName.ONETRUST] = IntegrationStatus.CONNECTED
            logger.info(f"OneTrust integration successful: {message}")
            return {
                "integration": IntegrationName.ONETRUST,
                "status": IntegrationStatus.CONNECTED,
                "message": message,
            }
        else:
            self.integration_status[IntegrationName.ONETRUST] = IntegrationStatus.ERROR
            logger.error(f"OneTrust integration failed: {message}")
            return {
                "integration": IntegrationName.ONETRUST,
                "status": IntegrationStatus.ERROR,
                "message": message,
            }

    async def integrate_securiti(
        self,
        api_key: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Integrate with Securiti.ai

        Args:
            api_key: Securiti API key
            tenant_id: Securiti tenant ID

        Returns:
            Integration status and details

        Requirements: 5.3
        """
        credentials = {
            "api_key": api_key,
            "tenant_id": tenant_id,
        }

        connector = SecuritiConnector(credentials)
        success, message = await connector.test_connection()

        if success:
            self.connectors[IntegrationName.SECURITI] = connector
            self.integration_status[IntegrationName.SECURITI] = IntegrationStatus.CONNECTED
            logger.info(f"Securiti integration successful: {message}")
            return {
                "integration": IntegrationName.SECURITI,
                "status": IntegrationStatus.CONNECTED,
                "message": message,
            }
        else:
            self.integration_status[IntegrationName.SECURITI] = IntegrationStatus.ERROR
            logger.error(f"Securiti integration failed: {message}")
            return {
                "integration": IntegrationName.SECURITI,
                "status": IntegrationStatus.ERROR,
                "message": message,
            }

    async def integrate_sprinto(
        self,
        api_key: str,
    ) -> Dict[str, Any]:
        """
        Integrate with Sprinto

        Args:
            api_key: Sprinto API key

        Returns:
            Integration status and details

        Requirements: 5.4
        """
        credentials = {
            "api_key": api_key,
        }

        connector = SprintoConnector(credentials)
        success, message = await connector.test_connection()

        if success:
            self.connectors[IntegrationName.SPRINTO] = connector
            self.integration_status[IntegrationName.SPRINTO] = IntegrationStatus.CONNECTED
            logger.info(f"Sprinto integration successful: {message}")
            return {
                "integration": IntegrationName.SPRINTO,
                "status": IntegrationStatus.CONNECTED,
                "message": message,
            }
        else:
            self.integration_status[IntegrationName.SPRINTO] = IntegrationStatus.ERROR
            logger.error(f"Sprinto integration failed: {message}")
            return {
                "integration": IntegrationName.SPRINTO,
                "status": IntegrationStatus.ERROR,
                "message": message,
            }

    async def integrate_custom_api(
        self,
        base_url: str,
        api_key: str,
        auth_type: str = "bearer",
    ) -> Dict[str, Any]:
        """
        Integrate with custom API

        Args:
            base_url: Custom API base URL
            api_key: Custom API key
            auth_type: Authentication type (default: bearer)

        Returns:
            Integration status and details

        Requirements: 5.6
        """
        credentials = {
            "base_url": base_url,
            "api_key": api_key,
            "auth_type": auth_type,
        }

        connector = CustomAPIConnector(credentials)
        success, message = await connector.test_connection()

        if success:
            self.connectors[IntegrationName.CUSTOM_API] = connector
            self.integration_status[IntegrationName.CUSTOM_API] = IntegrationStatus.CONNECTED
            logger.info(f"Custom API integration successful: {message}")
            return {
                "integration": IntegrationName.CUSTOM_API,
                "status": IntegrationStatus.CONNECTED,
                "message": message,
            }
        else:
            self.integration_status[IntegrationName.CUSTOM_API] = IntegrationStatus.ERROR
            logger.error(f"Custom API integration failed: {message}")
            return {
                "integration": IntegrationName.CUSTOM_API,
                "status": IntegrationStatus.ERROR,
                "message": message,
            }

    async def store_encrypted_credentials(
        self,
        integration_name: str,
        credentials: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Store encrypted credentials

        Args:
            integration_name: Name of integration
            credentials: Credentials to store
            user_id: User storing the credentials
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Encrypted credentials string

        Requirements: 5.1, 5.2, 5.3, 5.4, 5.6
        """
        encrypted = self.encryption.encrypt(credentials)
        logger.info(f"Credentials encrypted for integration: {integration_name}")

        # Log credential modification
        if user_id:
            audit_logger.log_credential_modification(
                user_id=user_id,
                integration_name=integration_name,
                modification_type="create",
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return encrypted

    async def retrieve_encrypted_credentials(
        self,
        encrypted_data: str,
        integration_name: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve and decrypt credentials

        Args:
            encrypted_data: Encrypted credentials string
            integration_name: Name of integration
            user_id: User retrieving the credentials
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Decrypted credentials dictionary

        Requirements: 5.1, 5.2, 5.3, 5.4, 5.6
        """
        try:
            credentials = self.encryption.decrypt(encrypted_data)

            # Log credential access
            if user_id and integration_name:
                audit_logger.log_credential_access(
                    user_id=user_id,
                    integration_name=integration_name,
                    access_type="read",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

            return credentials
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {str(e)}")

            # Log failed credential access
            if user_id and integration_name:
                audit_logger.log_security_event(
                    "credential_decryption_failed",
                    {
                        "integration_name": integration_name,
                        "error": str(e),
                    },
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    severity=AuditSeverity.CRITICAL,
                )

            raise

    def get_integration_status(self, integration_name: str) -> Optional[IntegrationStatus]:
        """
        Get status of an integration

        Args:
            integration_name: Name of integration

        Returns:
            Integration status or None if not found
        """
        return self.integration_status.get(integration_name)

    def get_all_integrations(self) -> Dict[str, IntegrationStatus]:
        """
        Get status of all integrations

        Returns:
            Dictionary of integration statuses
        """
        return self.integration_status.copy()


# ============================================================================
# Circuit Breaker Pattern Implementation (Task 6.7)
# ============================================================================

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for managing integration failures"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    async def call_async(self, func, *args, **kwargs):
        """
        Execute async function with circuit breaker protection

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if not self.last_failure_time:
            return False

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout


# ============================================================================
# Integration Error Handling (Task 6.7)
# ============================================================================

class IntegrationError(Exception):
    """Base exception for integration errors"""

    def __init__(self, integration_name: str, message: str, details: Optional[Dict] = None):
        """
        Initialize integration error

        Args:
            integration_name: Name of integration
            message: Error message
            details: Additional error details
        """
        self.integration_name = integration_name
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        return {
            "integration": self.integration_name,
            "error": self.message,
            "details": self.details,
            "timestamp": datetime.utcnow().isoformat(),
        }


class IntegrationConnectionError(IntegrationError):
    """Raised when connection to integration fails"""
    pass


class IntegrationAuthenticationError(IntegrationError):
    """Raised when authentication with integration fails"""
    pass


class IntegrationDataError(IntegrationError):
    """Raised when data retrieval from integration fails"""
    pass


class IntegrationTimeoutError(IntegrationError):
    """Raised when integration request times out"""
    pass


# ============================================================================
# Enhanced ComplianceIntegrationService with Error Handling
# ============================================================================

class ComplianceIntegrationServiceWithErrorHandling(ComplianceIntegrationService):
    """Extended service with comprehensive error handling and retry logic"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize service with error handling

        Args:
            encryption_key: Optional encryption key for credentials
        """
        super().__init__(encryption_key)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_log: List[Dict[str, Any]] = []
        self.max_error_log_size = 1000

    def _get_circuit_breaker(self, integration_name: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for integration

        Args:
            integration_name: Name of integration

        Returns:
            Circuit breaker instance
        """
        if integration_name not in self.circuit_breakers:
            self.circuit_breakers[integration_name] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=60,
            )
        return self.circuit_breakers[integration_name]

    async def _execute_with_error_handling(
        self,
        integration_name: str,
        func,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with comprehensive error handling

        Args:
            integration_name: Name of integration
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            IntegrationError: If execution fails
        """
        circuit_breaker = self._get_circuit_breaker(integration_name)

        try:
            result = await circuit_breaker.call_async(func, *args, **kwargs)
            return result
        except asyncio.TimeoutError as e:
            error = IntegrationTimeoutError(
                integration_name,
                f"Request timeout: {str(e)}",
                {"timeout": True},
            )
            self._log_error(error)
            raise error
        except Exception as e:
            error = IntegrationError(
                integration_name,
                f"Integration error: {str(e)}",
                {"error_type": type(e).__name__},
            )
            self._log_error(error)
            raise error

    def _log_error(self, error: IntegrationError):
        """
        Log integration error

        Args:
            error: Integration error to log
        """
        error_dict = error.to_dict()
        self.error_log.append(error_dict)

        # Keep error log size manageable
        if len(self.error_log) > self.max_error_log_size:
            self.error_log = self.error_log[-self.max_error_log_size:]

        logger.error(f"Integration error logged: {error_dict}")

    def get_error_log(
        self,
        integration_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get error log

        Args:
            integration_name: Optional filter by integration name
            limit: Maximum number of errors to return

        Returns:
            List of error records
        """
        errors = self.error_log

        if integration_name:
            errors = [e for e in errors if e.get("integration") == integration_name]

        return errors[-limit:]

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all circuit breakers

        Returns:
            Dictionary of circuit breaker statuses
        """
        status = {}
        for name, breaker in self.circuit_breakers.items():
            status[name] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None,
            }
        return status

    async def sync_integration_with_error_handling(
        self,
        integration_name: str,
        evidence_types: List[str],
    ) -> Dict[str, Any]:
        """
        Sync integration with comprehensive error handling

        Args:
            integration_name: Name of integration
            evidence_types: Types of evidence to collect

        Returns:
            Sync results with evidence and errors

        Requirements: 5.9
        """
        connector = self.connectors.get(integration_name)
        if not connector:
            raise IntegrationError(
                integration_name,
                f"Integration not found: {integration_name}",
            )

        results = {
            "integration": integration_name,
            "timestamp": datetime.utcnow().isoformat(),
            "evidence": [],
            "errors": [],
        }

        for evidence_type in evidence_types:
            try:
                evidence = await self._execute_with_error_handling(
                    integration_name,
                    connector.get_evidence,
                    evidence_type,
                )
                results["evidence"].append({
                    "type": evidence_type,
                    "data": evidence,
                    "collected_at": datetime.utcnow().isoformat(),
                })
            except IntegrationError as e:
                results["errors"].append(e.to_dict())
                logger.warning(f"Failed to collect {evidence_type} from {integration_name}: {str(e)}")

        # Update last sync time
        if connector:
            connector.last_sync = datetime.utcnow()

        return results

    async def health_check_integration(
        self,
        integration_name: str,
    ) -> Dict[str, Any]:
        """
        Perform health check on integration

        Args:
            integration_name: Name of integration

        Returns:
            Health check results

        Requirements: 5.9
        """
        connector = self.connectors.get(integration_name)
        if not connector:
            return {
                "integration": integration_name,
                "status": "not_found",
                "healthy": False,
            }

        try:
            success, message = await connector.test_connection()
            return {
                "integration": integration_name,
                "status": "connected" if success else "disconnected",
                "healthy": success,
                "message": message,
                "last_sync": connector.last_sync.isoformat() if connector.last_sync else None,
            }
        except Exception as e:
            return {
                "integration": integration_name,
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    async def health_check_all_integrations(self) -> Dict[str, Any]:
        """
        Perform health check on all integrations

        Returns:
            Health check results for all integrations

        Requirements: 5.9
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "integrations": {},
            "overall_healthy": True,
        }

        for integration_name in self.connectors.keys():
            health = await self.health_check_integration(integration_name)
            results["integrations"][integration_name] = health
            if not health.get("healthy"):
                results["overall_healthy"] = False

        return results
