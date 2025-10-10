"""
Supabase client for backend operations
"""

import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase database"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            logger.warning("Supabase credentials not found. Using mock data.")
            self.client = None
            return
            
        try:
            self.client: Client = create_client(self.url, self.service_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Supabase client is connected"""
        return self.client is not None
    
    # Models operations
    async def get_models(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get models from database"""
        if not self.is_connected():
            return self._get_mock_models()
        
        try:
            response = self.client.table("models").select("*").range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return self._get_mock_models()
    
    async def create_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new model"""
        if not self.is_connected():
            return {**model_data, "id": f"mock-{datetime.now().timestamp()}"}
        
        try:
            model_data["created_at"] = datetime.now(timezone.utc).isoformat()
            response = self.client.table("models").insert(model_data).execute()
            return response.data[0] if response.data else model_data
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            raise
    
    async def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific model by ID"""
        if not self.is_connected():
            return self._get_mock_model(model_id)
        
        try:
            response = self.client.table("models").select("*").eq("id", model_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching model {model_id}: {e}")
            return None
    
    # Datasets operations
    async def get_datasets(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get datasets from database"""
        if not self.is_connected():
            return self._get_mock_datasets()
        
        try:
            response = self.client.table("datasets").select("*").range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching datasets: {e}")
            return self._get_mock_datasets()
    
    async def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dataset"""
        if not self.is_connected():
            return {**dataset_data, "id": f"mock-dataset-{datetime.now().timestamp()}"}
        
        try:
            dataset_data["created_at"] = datetime.now(timezone.utc).isoformat()
            response = self.client.table("datasets").insert(dataset_data).execute()
            return response.data[0] if response.data else dataset_data
        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            raise
    
    # Simulation runs operations
    async def get_simulation_runs(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get simulation runs from database"""
        if not self.is_connected():
            return self._get_mock_simulation_runs()
        
        try:
            response = self.client.table("simulation_runs").select("*").range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching simulation runs: {e}")
            return self._get_mock_simulation_runs()
    
    async def create_simulation_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new simulation run"""
        if not self.is_connected():
            return {**run_data, "id": f"mock-run-{datetime.now().timestamp()}"}
        
        try:
            run_data["started_at"] = datetime.now(timezone.utc).isoformat()
            response = self.client.table("simulation_runs").insert(run_data).execute()
            return response.data[0] if response.data else run_data
        except Exception as e:
            logger.error(f"Error creating simulation run: {e}")
            raise
    
    async def update_simulation_run(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a simulation run"""
        if not self.is_connected():
            return {**updates, "id": run_id}
        
        try:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            response = self.client.table("simulation_runs").update(updates).eq("id", run_id).execute()
            return response.data[0] if response.data else updates
        except Exception as e:
            logger.error(f"Error updating simulation run {run_id}: {e}")
            raise
    
    # Dashboard metrics
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics from database"""
        if not self.is_connected():
            return self._get_mock_dashboard_metrics()
        
        try:
            # Get counts from different tables
            models_response = self.client.table("models").select("id", count="exact").execute()
            datasets_response = self.client.table("datasets").select("id", count="exact").execute()
            runs_response = self.client.table("simulation_runs").select("id", count="exact").execute()
            
            return {
                "total_models": models_response.count or 0,
                "total_datasets": datasets_response.count or 0,
                "total_simulations": runs_response.count or 0,
                "active_models": models_response.count or 0,  # Simplified for now
                "bias_alerts": 3,  # This would come from a bias_alerts table
                "fairness_score": 87,  # This would be calculated from recent runs
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard metrics: {e}")
            return self._get_mock_dashboard_metrics()
    
    # Mock data fallbacks
    def _get_mock_models(self) -> List[Dict[str, Any]]:
        """Mock models data"""
        return [
            {
                "id": "model-1",
                "name": "Credit Risk Model",
                "description": "ML model for credit risk assessment",
                "model_type": "classification",
                "version": "1.0.0",
                "created_at": "2024-01-15T10:00:00Z",
                "file_path": "/uploads/credit_risk_model.pkl",
                "file_size": 1024000,
                "tags": ["finance", "risk", "classification"],
                "metadata": {"accuracy": 0.85, "precision": 0.82},
                "status": "active"
            },
            {
                "id": "model-2", 
                "name": "Fraud Detection Model",
                "description": "AI model for detecting fraudulent transactions",
                "model_type": "classification",
                "version": "2.1.0",
                "created_at": "2024-01-16T14:30:00Z",
                "file_path": "/uploads/fraud_detection_model.pkl",
                "file_size": 2048000,
                "tags": ["security", "fraud", "classification"],
                "metadata": {"accuracy": 0.92, "recall": 0.89},
                "status": "active"
            }
        ]
    
    def _get_mock_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Mock single model data"""
        models = self._get_mock_models()
        return next((m for m in models if m["id"] == model_id), None)
    
    def _get_mock_datasets(self) -> List[Dict[str, Any]]:
        """Mock datasets data"""
        return [
            {
                "id": "dataset-1",
                "name": "Adult Income Dataset",
                "description": "Census income dataset for bias analysis",
                "file_path": "/datasets/adult_income.csv",
                "file_size": 2048000,
                "file_type": "csv",
                "row_count": 48842,
                "column_count": 15,
                "created_at": "2024-01-10T09:00:00Z",
                "schema_json": {
                    "columns": ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status", "occupation", "relationship", "race", "sex", "capital-gain", "capital-loss", "hours-per-week", "native-country", "income"]
                }
            },
            {
                "id": "dataset-2",
                "name": "German Credit Dataset",
                "description": "Credit scoring dataset for fairness analysis",
                "file_path": "/datasets/german_credit.csv",
                "file_size": 512000,
                "file_type": "csv",
                "row_count": 1000,
                "column_count": 21,
                "created_at": "2024-01-12T11:30:00Z",
                "schema_json": {
                    "columns": ["checking_status", "duration", "credit_history", "purpose", "credit_amount", "savings_status", "employment", "installment_commitment", "personal_status", "other_parties", "residence_since", "property_magnitude", "age", "other_payment_plans", "housing", "existing_credits", "job", "num_dependents", "own_telephone", "foreign_worker", "class"]
                }
            }
        ]
    
    def _get_mock_simulation_runs(self) -> List[Dict[str, Any]]:
        """Mock simulation runs data"""
        return [
            {
                "id": "run-1",
                "name": "Credit Risk Bias Analysis",
                "description": "Comprehensive bias analysis on credit risk model",
                "model_id": "model-1",
                "dataset_id": "dataset-1",
                "status": "completed",
                "started_at": "2024-01-20T10:00:00Z",
                "completed_at": "2024-01-20T10:15:00Z",
                "execution_time_ms": 900000,
                "config_json": {
                    "bias_metrics": ["demographic_parity", "equalized_odds", "calibration"],
                    "protected_attributes": ["race", "sex"],
                    "threshold": 0.8
                },
                "results_json": {
                    "demographic_parity": 0.85,
                    "equalized_odds": 0.78,
                    "calibration": 0.92,
                    "overall_fairness_score": 0.85
                }
            }
        ]
    
    def _get_mock_dashboard_metrics(self) -> Dict[str, Any]:
        """Mock dashboard metrics"""
        return {
            "total_models": 24,
            "total_datasets": 8,
            "total_simulations": 156,
            "active_models": 18,
            "bias_alerts": 3,
            "fairness_score": 87
        }

# Global instance
supabase_service = SupabaseService()