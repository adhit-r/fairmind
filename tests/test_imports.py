import pytest
from core.container import ServiceContainer
from api.registry import RouteRegistry

def test_core_imports():
    """Test that core modules can be imported."""
    from core.container import ServiceContainer
    from core.exceptions import AppException
    from core.interfaces import IService
    from core.logging import get_logger
    
    assert ServiceContainer is not None
    assert AppException is not None
    assert IService is not None
    assert get_logger is not None

def test_domain_imports():
    """Test that domain services can be imported."""
    # Dataset
    from domain.dataset.services.dataset_service import DatasetService
    assert DatasetService is not None
    
    # Bias Detection
    from domain.bias_detection.services.bias_detection_service import BiasDetectionService
    assert BiasDetectionService is not None
    
    # Compliance
    from domain.compliance.services.compliance_service import ComplianceService
    from domain.compliance.services.india_compliance_service import IndiaComplianceService
    assert ComplianceService is not None
    assert IndiaComplianceService is not None
    
    # Monitoring
    from domain.monitoring.services.monitoring_service import MonitoringService
    from domain.monitoring.services.alert_service import AlertService
    assert MonitoringService is not None
    assert AlertService is not None
    
    # MLOps
    from domain.mlops.services.tool_integration_service import ToolIntegrationService
    from domain.mlops.services.model_training_service import ModelTrainingService
    from domain.mlops.services.mlops_service import MLOpsService
    assert ToolIntegrationService is not None
    assert ModelTrainingService is not None
    assert MLOpsService is not None

def test_route_registry_discovery():
    """Test that route registry can discover routes."""
    from api.registry import RouteRegistry
    from pathlib import Path
    
    registry = RouteRegistry()
    # Point to the actual backend directory
    backend_path = Path(__file__).parent.parent / "apps" / "backend"
    
    # We expect discovery to work without errors
    registry.discover_routes(backend_path, fail_fast=True)
    
    routes = registry.get_route_listing()
    assert len(routes) > 0
    
    # Check for specific domains
    domains = {r["domain"] for r in routes}
    assert "bias_detection" in domains
    assert "compliance" in domains
    assert "monitoring" in domains
    assert "mlops" in domains
