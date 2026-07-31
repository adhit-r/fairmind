"""
Model Test Service - Handles model testing and bias analysis.
"""

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from core.base_service import BaseService
from core.container import service, ServiceLifetime, inject
from core.interfaces import ILogger
from database.connection import db_manager
from sqlalchemy import text

try:
    from domain.bias_detection.services.bias_detection_service import BiasDetectionService
except Exception:
    BiasDetectionService = None  # type: ignore
from domain.dataset.services.dataset_service import DatasetService

logger = logging.getLogger(__name__)

@service(lifetime=ServiceLifetime.SINGLETON)
class ModelTestService(BaseService):
    """Service for running tests on models."""
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.bias_service = inject(BiasDetectionService) if BiasDetectionService else None
        self.dataset_service = inject(DatasetService)
        
    async def run_bias_test(
        self, 
        model_id: str, 
        dataset_id: Optional[str] = None,
        target_column: Optional[str] = None,
        sensitive_attributes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run a bias test on a model.
        
        If dataset_id is provided, uses that dataset.
        Otherwise, uses a synthetic dataset for demonstration.
        """
        self._log_operation(
            "run_bias_test", 
            model_id=model_id, 
            dataset_id=dataset_id,
            target_column=target_column,
            sensitive_attributes=sensitive_attributes
        )

        if self.bias_service is None:
            raise RuntimeError("BiasDetectionService is not available in this runtime")
        
        # 1. Fetch model metadata
        with db_manager.get_session() as session:
            result = session.execute(
                text("SELECT name, model_type FROM models WHERE id = :id"),
                {"id": model_id}
            ).fetchone()
            
            if not result:
                raise ValueError(f"Model {model_id} not found")
            
            model_name = result.name
            model_type = result.model_type

        # 2. Prepare Test Data
        df = None
        
        if dataset_id:
            # Use real dataset
            try:
                df = await self.dataset_service.get_dataframe(dataset_id)
                
                # Validate columns
                if target_column and target_column not in df.columns:
                    raise ValueError(f"Target column '{target_column}' not found in dataset")
                
                if sensitive_attributes:
                    missing = [col for col in sensitive_attributes if col not in df.columns]
                    if missing:
                        raise ValueError(f"Sensitive attributes not found: {missing}")
                
                # If target_column not provided, try to guess
                if not target_column:
                    # Simple heuristic: look for 'target', 'label', 'class', 'prediction'
                    candidates = ['target', 'label', 'class', 'prediction', 'outcome']
                    for c in candidates:
                        if c in df.columns:
                            target_column = c
                            break
                    if not target_column:
                        # Fallback to last column
                        target_column = df.columns[-1]
                
                # If sensitive_attributes not provided, try to guess or use empty
                if not sensitive_attributes:
                    # Simple heuristic: look for common sensitive attrs
                    common_sensitive = ['gender', 'sex', 'race', 'ethnicity', 'age', 'religion', 'disability']
                    sensitive_attributes = [col for col in df.columns if col.lower() in common_sensitive]
                    if not sensitive_attributes:
                        # If we can't find any, we can't run bias analysis effectively
                        # But let's allow it to run with empty list to show general stats
                        sensitive_attributes = []
                        
            except Exception as e:
                logger.error(f"Failed to load dataset {dataset_id}: {e}")
                raise ValueError(f"Failed to load dataset: {str(e)}")
        else:
            # Generate synthetic dataframe
            np.random.seed(42)
            n_samples = 1000
            
            # Sensitive attributes
            gender = np.random.choice(['Male', 'Female'], n_samples)
            ethnicity = np.random.choice(['Group A', 'Group B', 'Group C'], n_samples)
            age_group = np.random.choice(['Young', 'Middle', 'Senior'], n_samples)
            
            # Target/Ground Truth (simulated)
            base_prob = 0.5
            y_true = []
            for g, e in zip(gender, ethnicity):
                prob = base_prob
                if e == 'Group B':
                    prob -= 0.2
                if g == 'Female':
                    prob -= 0.05
                y_true.append(1 if np.random.random() < prob else 0)
                
            # Model Predictions (simulated)
            y_pred = []
            for y, g, e in zip(y_true, gender, ethnicity):
                prob = 0.8 if y == 1 else 0.2
                if e == 'Group B':
                    prob -= 0.1
                y_pred.append(1 if np.random.random() < prob else 0)
                
            df = pd.DataFrame({
                'gender': gender,
                'ethnicity': ethnicity,
                'age_group': age_group,
                'target': y_pred,
                'ground_truth': y_true
            })
            
            sensitive_attributes = ['gender', 'ethnicity', 'age_group']
            target_column = 'target'
        
        # 3. Run Analysis using BiasDetectionService
        # Ensure sensitive_attributes is a list
        if sensitive_attributes is None:
            sensitive_attributes = []
            
        analysis_result = await self.bias_service.analyze_dataset_bias(
            dataset_or_df=dataset_id if dataset_id else df,
            sensitive_attributes=sensitive_attributes,
            target_column=target_column
        )
        
        # 4. Save Results
        analysis_id = str(uuid.uuid4())
        
        # Extract metrics and results
        metrics_data = analysis_result.fairness_metrics
        
        # Calculate overall score
        total_checks = 0
        passed_checks = 0
        
        for attr, metrics in metrics_data.items():
            if 'demographic_parity' in metrics:
                total_checks += 1
                if metrics['demographic_parity'].get('fair', False):
                    passed_checks += 1
            if 'equality_of_opportunity' in metrics:
                total_checks += 1
                if metrics['equality_of_opportunity'].get('fair', False):
                    passed_checks += 1
        
        overall_score = passed_checks / total_checks if total_checks > 0 else 0.0
        metrics_data['overall_score'] = overall_score
        
        results_data = {
            "dataset_info": analysis_result.dataset_info,
            "data_quality": analysis_result.data_quality,
            "bias_detection": analysis_result.bias_detection,
            "recommendations": analysis_result.recommendations
        }
        
        with db_manager.get_session() as session:
            # Save analysis record
            insert_query = text("""
                INSERT INTO bias_analyses (
                    id, model_id, dataset_id, analysis_type, status,
                    results, metrics, created_at, completed_at
                ) VALUES (
                    :id, :model_id, :dataset_id, :analysis_type, :status,
                    :results, :metrics, :created_at, :completed_at
                )
            """)
            
            session.execute(insert_query, {
                "id": analysis_id,
                "model_id": model_id,
                "dataset_id": dataset_id or "synthetic-demo",
                "analysis_type": "model_bias_test",
                "status": "completed",
                "results": json.dumps(results_data),
                "metrics": json.dumps(metrics_data),
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc)
            })
            
            # Update model with latest scores
            update_model_query = text("""
                UPDATE models 
                SET bias_score = :bias_score,
                    fairness_score = :fairness_score,
                    updated_at = :updated_at,
                    last_test_date = :updated_at
                WHERE id = :id
            """)
            
            bias_score = 1.0 - overall_score
            
            session.execute(update_model_query, {
                "id": model_id,
                "bias_score": bias_score,
                "fairness_score": overall_score,
                "updated_at": datetime.now(timezone.utc)
            })
            
            session.commit()
            
        return {
            "analysis_id": analysis_id,
            "model_id": model_id,
            "score": overall_score,
            "metrics": metrics_data,
            "recommendations": analysis_result.recommendations
        }
