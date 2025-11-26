"""
Tests for security and encryption features.

Tests cover:
- Credential encryption and decryption
- RBAC (Role-Based Access Control)
- Audit logging
- Permission checking
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from api.services.compliance_integration_service import CredentialEncryption
from api.middleware.rbac import (
    RBACManager,
    ComplianceRole,
    CompliancePermission,
    ROLE_PERMISSIONS,
)
from api.middleware.audit_logging import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
)


# ============================================================================
# Credential Encryption Tests
# ============================================================================

class TestCredentialEncryption:
    """Tests for credential encryption utility"""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are inverse operations"""
        encryption = CredentialEncryption()
        original_data = {
            "api_key": "test-api-key-12345",
            "org_id": "org-123",
            "secret": "super-secret-value",
        }

        # Encrypt
        encrypted = encryption.encrypt(original_data)
        assert isinstance(encrypted, str)
        assert encrypted != json.dumps(original_data)

        # Decrypt
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original_data

    def test_encrypt_produces_different_output_each_time(self):
        """Test that encryption produces different output for same input"""
        encryption = CredentialEncryption()
        data = {"api_key": "test-key"}

        encrypted1 = encryption.encrypt(data)
        encrypted2 = encryption.encrypt(data)

        # Fernet includes timestamp, so outputs should differ
        assert encrypted1 != encrypted2

        # But both should decrypt to same value
        assert encryption.decrypt(encrypted1) == data
        assert encryption.decrypt(encrypted2) == data

    def test_decrypt_invalid_data_raises_error(self):
        """Test that decrypting invalid data raises error"""
        encryption = CredentialEncryption()

        with pytest.raises(Exception):
            encryption.decrypt("invalid-encrypted-data")

    def test_encrypt_complex_nested_structure(self):
        """Test encryption of complex nested data structures"""
        encryption = CredentialEncryption()
        complex_data = {
            "credentials": {
                "api_key": "key-123",
                "secret": "secret-456",
                "nested": {
                    "deep": {
                        "value": "test",
                        "list": [1, 2, 3],
                    }
                }
            },
            "metadata": {
                "created_at": "2025-01-01T00:00:00Z",
                "tags": ["production", "critical"],
            }
        }

        encrypted = encryption.encrypt(complex_data)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == complex_data

    def test_encrypt_empty_dict(self):
        """Test encryption of empty dictionary"""
        encryption = CredentialEncryption()
        data = {}

        encrypted = encryption.encrypt(data)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == data

    def test_encrypt_with_special_characters(self):
        """Test encryption of data with special characters"""
        encryption = CredentialEncryption()
        data = {
            "api_key": "key-with-!@#$%^&*()",
            "secret": "secret-with-unicode-🔐",
            "url": "https://api.example.com/path?query=value&other=123",
        }

        encrypted = encryption.encrypt(data)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == data


# ============================================================================
# RBAC Tests
# ============================================================================

class TestRBACManager:
    """Tests for Role-Based Access Control"""

    def test_assign_role_to_user(self):
        """Test assigning role to user"""
        rbac = RBACManager()
        user_id = "user-123"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_ADMIN)

        assert ComplianceRole.COMPLIANCE_ADMIN in rbac.get_user_roles(user_id)

    def test_revoke_role_from_user(self):
        """Test revoking role from user"""
        rbac = RBACManager()
        user_id = "user-123"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_ADMIN)
        rbac.revoke_role(user_id, ComplianceRole.COMPLIANCE_ADMIN)

        assert ComplianceRole.COMPLIANCE_ADMIN not in rbac.get_user_roles(user_id)

    def test_user_permissions_updated_on_role_assignment(self):
        """Test that user permissions are updated when role is assigned"""
        rbac = RBACManager()
        user_id = "user-123"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_ADMIN)

        # Admin should have all permissions
        admin_permissions = ROLE_PERMISSIONS[ComplianceRole.COMPLIANCE_ADMIN]
        user_permissions = rbac.get_user_permissions(user_id)

        assert user_permissions == admin_permissions

    def test_compliance_admin_has_all_permissions(self):
        """Test that compliance admin has all permissions"""
        rbac = RBACManager()
        user_id = "admin-user"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_ADMIN)

        # Check all permissions
        for permission in CompliancePermission:
            assert rbac.has_permission(user_id, permission)

    def test_compliance_viewer_has_limited_permissions(self):
        """Test that compliance viewer has limited permissions"""
        rbac = RBACManager()
        user_id = "viewer-user"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_VIEWER)

        # Viewer should have view permissions
        assert rbac.has_permission(user_id, CompliancePermission.VIEW_EVIDENCE)
        assert rbac.has_permission(user_id, CompliancePermission.VIEW_REPORTS)

        # Viewer should not have modify permissions
        assert not rbac.has_permission(user_id, CompliancePermission.MODIFY_EVIDENCE)
        assert not rbac.has_permission(user_id, CompliancePermission.DELETE_EVIDENCE)

    def test_compliance_auditor_has_audit_permissions(self):
        """Test that compliance auditor has audit permissions"""
        rbac = RBACManager()
        user_id = "auditor-user"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_AUDITOR)

        # Auditor should have view and audit permissions
        assert rbac.has_permission(user_id, CompliancePermission.VIEW_EVIDENCE)
        assert rbac.has_permission(user_id, CompliancePermission.VIEW_AUDIT_LOGS)

        # Auditor should not have modify permissions
        assert not rbac.has_permission(user_id, CompliancePermission.MODIFY_EVIDENCE)

    def test_user_with_multiple_roles(self):
        """Test user with multiple roles"""
        rbac = RBACManager()
        user_id = "multi-role-user"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_MANAGER)
        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_AUDITOR)

        # User should have permissions from both roles
        manager_perms = ROLE_PERMISSIONS[ComplianceRole.COMPLIANCE_MANAGER]
        auditor_perms = ROLE_PERMISSIONS[ComplianceRole.COMPLIANCE_AUDITOR]
        combined_perms = manager_perms | auditor_perms

        user_perms = rbac.get_user_permissions(user_id)
        assert user_perms == combined_perms

    def test_has_any_permission(self):
        """Test checking if user has any of multiple permissions"""
        rbac = RBACManager()
        user_id = "user-123"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_VIEWER)

        # User should have any of these permissions
        assert rbac.has_any_permission(
            user_id,
            [
                CompliancePermission.VIEW_EVIDENCE,
                CompliancePermission.MODIFY_EVIDENCE,
            ]
        )

        # User should not have any of these permissions
        assert not rbac.has_any_permission(
            user_id,
            [
                CompliancePermission.MODIFY_EVIDENCE,
                CompliancePermission.DELETE_EVIDENCE,
            ]
        )

    def test_has_all_permissions(self):
        """Test checking if user has all permissions"""
        rbac = RBACManager()
        user_id = "user-123"

        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_ADMIN)

        # Admin should have all these permissions
        assert rbac.has_all_permissions(
            user_id,
            [
                CompliancePermission.VIEW_EVIDENCE,
                CompliancePermission.MODIFY_EVIDENCE,
                CompliancePermission.DELETE_EVIDENCE,
            ]
        )

        # Viewer should not have all these permissions
        rbac2 = RBACManager()
        viewer_id = "viewer-123"
        rbac2.assign_role(viewer_id, ComplianceRole.COMPLIANCE_VIEWER)

        assert not rbac2.has_all_permissions(
            viewer_id,
            [
                CompliancePermission.VIEW_EVIDENCE,
                CompliancePermission.MODIFY_EVIDENCE,
            ]
        )

    def test_rbac_disabled_allows_all_permissions(self):
        """Test that when RBAC is disabled, all permissions are allowed"""
        rbac = RBACManager()
        rbac.enabled = False
        user_id = "user-123"

        # User has no roles
        assert len(rbac.get_user_roles(user_id)) == 0

        # But all permissions are allowed
        assert rbac.has_permission(user_id, CompliancePermission.VIEW_EVIDENCE)
        assert rbac.has_permission(user_id, CompliancePermission.MODIFY_EVIDENCE)
        assert rbac.has_permission(user_id, CompliancePermission.DELETE_EVIDENCE)


# ============================================================================
# Audit Logging Tests
# ============================================================================

class TestAuditLogger:
    """Tests for audit logging"""

    def test_log_compliance_check_event(self):
        """Test logging compliance check event"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_compliance_check(
            user_id="user-123",
            system_id="system-456",
            framework="dpdp_act_2023",
            status="success",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert result["event_type"] == AuditEventType.COMPLIANCE_CHECK.value
        assert result["user_id"] == "user-123"
        assert result["resource_id"] == "system-456"
        assert result["status"] == "success"
        assert result["details"]["framework"] == "dpdp_act_2023"

    def test_log_evidence_access_event(self):
        """Test logging evidence access event"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_evidence_access(
            user_id="user-123",
            evidence_id="evidence-789",
            system_id="system-456",
            access_type="read",
            ip_address="192.168.1.1",
        )

        assert result["event_type"] == AuditEventType.EVIDENCE_ACCESS.value
        assert result["user_id"] == "user-123"
        assert result["resource_id"] == "evidence-789"
        assert result["details"]["access_type"] == "read"

    def test_log_credential_access_event(self):
        """Test logging credential access event"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_credential_access(
            user_id="user-123",
            integration_name="onetrust",
            access_type="read",
            ip_address="192.168.1.1",
        )

        assert result["event_type"] == AuditEventType.CREDENTIAL_ACCESS.value
        assert result["severity"] == AuditSeverity.WARNING.value
        assert result["details"]["integration_name"] == "onetrust"

    def test_log_credential_modification_event(self):
        """Test logging credential modification event"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_credential_modification(
            user_id="user-123",
            integration_name="securiti",
            modification_type="update",
            ip_address="192.168.1.1",
        )

        assert result["event_type"] == AuditEventType.CREDENTIAL_MODIFICATION.value
        assert result["severity"] == AuditSeverity.CRITICAL.value
        assert result["details"]["modification_type"] == "update"

    def test_log_rbac_change_event(self):
        """Test logging RBAC change event"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_rbac_change(
            user_id="admin-123",
            target_user_id="user-456",
            role="compliance_admin",
            action="assign",
            ip_address="192.168.1.1",
        )

        assert result["event_type"] == AuditEventType.RBAC_CHANGE.value
        assert result["user_id"] == "admin-123"
        assert result["resource_id"] == "user-456"
        assert result["details"]["role"] == "compliance_admin"
        assert result["details"]["action"] == "assign"

    def test_log_security_event(self):
        """Test logging security event"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_security_event(
            event_name="unauthorized_access_attempt",
            details={"endpoint": "/api/v1/compliance/evidence"},
            user_id="user-123",
            ip_address="192.168.1.1",
            severity=AuditSeverity.CRITICAL,
        )

        assert result["event_type"] == AuditEventType.SECURITY_EVENT.value
        assert result["action"] == "unauthorized_access_attempt"
        assert result["severity"] == AuditSeverity.CRITICAL.value

    def test_audit_logging_disabled(self):
        """Test that audit logging can be disabled"""
        audit = AuditLogger()
        audit.enabled = False

        result = audit.log_compliance_check(
            user_id="user-123",
            system_id="system-456",
            framework="dpdp_act_2023",
        )

        assert result == {}

    def test_log_event_includes_timestamp(self):
        """Test that logged events include timestamp"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            user_id="user-123",
            resource_type="compliance",
            action="check",
        )

        assert "timestamp" in result
        # Verify timestamp is ISO format
        datetime.fromisoformat(result["timestamp"])

    def test_log_event_with_error_message(self):
        """Test logging event with error message"""
        audit = AuditLogger()
        audit.enabled = True

        result = audit.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            user_id="user-123",
            resource_type="compliance",
            action="check",
            status="failure",
            error_message="Database connection failed",
        )

        assert result["status"] == "failure"
        assert result["error_message"] == "Database connection failed"


# ============================================================================
# Integration Tests
# ============================================================================

class TestSecurityIntegration:
    """Integration tests for security features"""

    def test_credential_encryption_with_rbac(self):
        """Test credential encryption with RBAC"""
        encryption = CredentialEncryption()
        rbac = RBACManager()

        # Setup user with limited permissions
        user_id = "user-123"
        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_VIEWER)

        # Viewer should not have permission to modify credentials
        assert not rbac.has_permission(
            user_id,
            CompliancePermission.MODIFY_INTEGRATION_CREDENTIALS
        )

        # But admin should
        admin_id = "admin-123"
        rbac.assign_role(admin_id, ComplianceRole.COMPLIANCE_ADMIN)
        assert rbac.has_permission(
            admin_id,
            CompliancePermission.MODIFY_INTEGRATION_CREDENTIALS
        )

    def test_audit_logging_with_rbac_changes(self):
        """Test audit logging of RBAC changes"""
        audit = AuditLogger()
        audit.enabled = True
        rbac = RBACManager()

        admin_id = "admin-123"
        user_id = "user-456"

        # Log RBAC change
        audit_entry = audit.log_rbac_change(
            user_id=admin_id,
            target_user_id=user_id,
            role="compliance_manager",
            action="assign",
        )

        # Verify audit entry
        assert audit_entry["event_type"] == AuditEventType.RBAC_CHANGE.value
        assert audit_entry["user_id"] == admin_id
        assert audit_entry["resource_id"] == user_id

        # Apply the role change
        rbac.assign_role(user_id, ComplianceRole.COMPLIANCE_MANAGER)

        # Verify user now has manager permissions
        assert rbac.has_permission(
            user_id,
            CompliancePermission.MANAGE_INTEGRATIONS
        )
