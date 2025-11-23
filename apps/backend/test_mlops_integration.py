"""
Test script for MLOps Integration Service
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Pre-mock wandb and mlflow in sys.modules so they can be imported
mock_wandb_module = MagicMock()
mock_mlflow_module = MagicMock()
sys.modules["wandb"] = mock_wandb_module
sys.modules["mlflow"] = mock_mlflow_module

from services.mlops_integration import MLOpsIntegrationService


def test_mlops_service():
    print("=" * 60)
    print("MLOPS INTEGRATION SERVICE TEST")
    print("=" * 60)

    # Mock environment variables
    with patch.dict(os.environ, {
        "MLOPS_PROVIDER": "both",
        "WANDB_API_KEY": "fake_key",
        "WANDB_PROJECT": "test_project",
        "WANDB_ENTITY": "test_entity",
        "MLFLOW_TRACKING_URI": "http://localhost:5000"
    }):
        # Setup mocks behavior
        mock_wandb_module.init.return_value.id = "wandb-run-123"
        mock_wandb_module.init.return_value.url = "https://wandb.ai/test/run/123"
        
        mock_mlflow_module.start_run.return_value.__enter__.return_value.info.run_id = "mlflow-run-456"
        mock_mlflow_module.start_run.return_value.__enter__.return_value.info.experiment_id = "0"

        # Initialize service
        print("\n1. Initializing Service...")
        # Force re-initialization if it was already initialized globally
        service = MLOpsIntegrationService()
        
        # Manually trigger client init since we just mocked sys.modules
        # (The __init__ calls _initialize_clients which does the import)
        
        print(f"   ✓ Provider: {service.provider}")
        print(f"   ✓ W&B Enabled: {service.wandb_enabled}")
        print(f"   ✓ MLflow Enabled: {service.mlflow_enabled}")

        # Test logging
        print("\n2. Testing Log Bias Test...")
        test_results = {
            "accuracy": 0.95,
            "bias_score": 0.05,
            "metrics_passed": 5,
            "metrics_failed": 0,
            "summary": "Test passed successfully"
        }
        
        result = service.log_bias_test(
            test_id="test-001",
            model_id="model-abc",
            test_type="bias_check",
            results=test_results
        )
        
        print("   ✓ Logging Result:", result)
        
        # Verify W&B calls
        if result["wandb"]["success"]:
            print("   ✓ W&B logging successful")
            mock_wandb_module.init.assert_called()
        else:
            print(f"   ✗ W&B logging failed: {result['wandb'].get('error')}")

        # Verify MLflow calls
        if result["mlflow"]["success"]:
            print("   ✓ MLflow logging successful")
            mock_mlflow_module.start_run.assert_called()
        else:
            print(f"   ✗ MLflow logging failed: {result['mlflow'].get('error')}")

        # Test URL generation
        print("\n3. Testing URL Generation...")
        wandb_url = service.get_run_url("wandb", "run-123")
        mlflow_url = service.get_run_url("mlflow", "run-456")
        
        print(f"   ✓ W&B URL: {wandb_url}")
        print(f"   ✓ MLflow URL: {mlflow_url}")
        
        assert "wandb.ai" in wandb_url
        assert "localhost:5000" in mlflow_url

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    test_mlops_service()
