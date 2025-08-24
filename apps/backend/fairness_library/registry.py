"""
Centralized Model & Data Registry
Single source of truth for all models, datasets, and their associated documentation.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"

class DatasetStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

@dataclass
class ModelCard:
    """Model Card for each model with comprehensive documentation"""
    model_id: str
    name: str
    version: str
    description: str
    intended_use: str
    training_data: Dict[str, Any]
    evaluation_data: Dict[str, Any]
    performance_metrics: Dict[str, float]
    fairness_metrics: Dict[str, Any]
    known_limitations: List[str]
    bias_analysis: Dict[str, Any]
    risk_assessment: str
    deployment_notes: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    status: ModelStatus
    tags: List[str]
    documentation_url: Optional[str] = None

@dataclass
class DatasetDatasheet:
    """Dataset Datasheet with comprehensive metadata"""
    dataset_id: str
    name: str
    version: str
    description: str
    collection_method: str
    data_sources: List[str]
    data_processing: Dict[str, Any]
    data_quality: Dict[str, Any]
    potential_biases: List[str]
    representational_gaps: List[str]
    privacy_considerations: List[str]
    usage_restrictions: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    status: DatasetStatus
    tags: List[str]
    documentation_url: Optional[str] = None

@dataclass
class FairnessReport:
    """Comprehensive fairness analysis report"""
    report_id: str
    model_id: str
    dataset_id: str
    analysis_timestamp: datetime
    fairness_metrics: Dict[str, Any]
    bias_detection_results: Dict[str, Any]
    statistical_tests: Dict[str, Any]
    recommendations: List[str]
    risk_level: str
    compliance_status: str
    auditor: str
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None

class ModelRegistry:
    """Centralized model registry with version control and audit trails"""
    
    def __init__(self, storage_path: str = "registry/models"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, ModelCard] = {}
        self._load_existing_models()
    
    def register_model(self, model_card: ModelCard) -> str:
        """Register a new model with comprehensive documentation"""
        try:
            # Validate model card
            self._validate_model_card(model_card)
            
            # Generate unique ID if not provided
            if not model_card.model_id:
                model_card.model_id = str(uuid.uuid4())
            
            # Set timestamps
            now = datetime.now()
            if not model_card.created_at:
                model_card.created_at = now
            model_card.updated_at = now
            
            # Store model card
            self.models[model_card.model_id] = model_card
            self._save_model_card(model_card)
            
            logger.info(f"Registered model: {model_card.name} v{model_card.version}")
            return model_card.model_id
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise
    
    def get_model(self, model_id: str) -> Optional[ModelCard]:
        """Retrieve model card by ID"""
        return self.models.get(model_id)
    
    def list_models(self, status: Optional[ModelStatus] = None) -> List[ModelCard]:
        """List all models, optionally filtered by status"""
        models = list(self.models.values())
        if status:
            models = [m for m in models if m.status == status]
        return models
    
    def update_model(self, model_id: str, updates: Dict[str, Any]) -> bool:
        """Update model card with new information"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model_card = self.models[model_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(model_card, key):
                    setattr(model_card, key, value)
            
            # Update timestamp
            model_card.updated_at = datetime.now()
            
            # Save updated model card
            self._save_model_card(model_card)
            
            logger.info(f"Updated model: {model_card.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            return False
    
    def add_fairness_report(self, model_id: str, fairness_report: FairnessReport) -> bool:
        """Add fairness report to model"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model_card = self.models[model_id]
            
            # Update fairness metrics in model card
            model_card.fairness_metrics.update(fairness_report.fairness_metrics)
            model_card.bias_analysis = fairness_report.bias_detection_results
            
            # Save updated model card
            self._save_model_card(model_card)
            
            # Save fairness report
            self._save_fairness_report(fairness_report)
            
            logger.info(f"Added fairness report to model: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding fairness report: {e}")
            return False
    
    def _validate_model_card(self, model_card: ModelCard) -> None:
        """Validate model card completeness"""
        required_fields = ['name', 'version', 'description', 'intended_use']
        for field in required_fields:
            if not getattr(model_card, field):
                raise ValueError(f"Missing required field: {field}")
    
    def _save_model_card(self, model_card: ModelCard) -> None:
        """Save model card to storage"""
        try:
            file_path = self.storage_path / f"{model_card.model_id}.json"
            with open(file_path, 'w') as f:
                json.dump(asdict(model_card), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving model card: {e}")
            raise
    
    def _load_existing_models(self) -> None:
        """Load existing models from storage"""
        try:
            for file_path in self.storage_path.glob("*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    model_card = ModelCard(**data)
                    self.models[model_card.model_id] = model_card
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
    
    def _save_fairness_report(self, report: FairnessReport) -> None:
        """Save fairness report to storage"""
        try:
            reports_path = self.storage_path / "fairness_reports"
            reports_path.mkdir(exist_ok=True)
            
            file_path = reports_path / f"{report.report_id}.json"
            with open(file_path, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving fairness report: {e}")
            raise

class DatasetRegistry:
    """Centralized dataset registry with comprehensive metadata"""
    
    def __init__(self, storage_path: str = "registry/datasets"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.datasets: Dict[str, DatasetDatasheet] = {}
        self._load_existing_datasets()
    
    def register_dataset(self, datasheet: DatasetDatasheet) -> str:
        """Register a new dataset with comprehensive documentation"""
        try:
            # Validate datasheet
            self._validate_datasheet(datasheet)
            
            # Generate unique ID if not provided
            if not datasheet.dataset_id:
                datasheet.dataset_id = str(uuid.uuid4())
            
            # Set timestamps
            now = datetime.now()
            if not datasheet.created_at:
                datasheet.created_at = now
            datasheet.updated_at = now
            
            # Store datasheet
            self.datasets[datasheet.dataset_id] = datasheet
            self._save_datasheet(datasheet)
            
            logger.info(f"Registered dataset: {datasheet.name} v{datasheet.version}")
            return datasheet.dataset_id
            
        except Exception as e:
            logger.error(f"Error registering dataset: {e}")
            raise
    
    def get_dataset(self, dataset_id: str) -> Optional[DatasetDatasheet]:
        """Retrieve dataset datasheet by ID"""
        return self.datasets.get(dataset_id)
    
    def list_datasets(self, status: Optional[DatasetStatus] = None) -> List[DatasetDatasheet]:
        """List all datasets, optionally filtered by status"""
        datasets = list(self.datasets.values())
        if status:
            datasets = [d for d in datasets if d.status == status]
        return datasets
    
    def update_dataset(self, dataset_id: str, updates: Dict[str, Any]) -> bool:
        """Update dataset datasheet with new information"""
        try:
            if dataset_id not in self.datasets:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            datasheet = self.datasets[dataset_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(datasheet, key):
                    setattr(datasheet, key, value)
            
            # Update timestamp
            datasheet.updated_at = datetime.now()
            
            # Save updated datasheet
            self._save_datasheet(datasheet)
            
            logger.info(f"Updated dataset: {datasheet.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating dataset: {e}")
            return False
    
    def _validate_datasheet(self, datasheet: DatasetDatasheet) -> None:
        """Validate dataset datasheet completeness"""
        required_fields = ['name', 'version', 'description', 'collection_method']
        for field in required_fields:
            if not getattr(datasheet, field):
                raise ValueError(f"Missing required field: {field}")
    
    def _save_datasheet(self, datasheet: DatasetDatasheet) -> None:
        """Save dataset datasheet to storage"""
        try:
            file_path = self.storage_path / f"{datasheet.dataset_id}.json"
            with open(file_path, 'w') as f:
                json.dump(asdict(datasheet), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving datasheet: {e}")
            raise
    
    def _load_existing_datasets(self) -> None:
        """Load existing datasets from storage"""
        try:
            for file_path in self.storage_path.glob("*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    datasheet = DatasetDatasheet(**data)
                    self.datasets[datasheet.dataset_id] = datasheet
        except Exception as e:
            logger.error(f"Error loading existing datasets: {e}")

class RegistryManager:
    """High-level registry manager for coordinating model and dataset registries"""
    
    def __init__(self, base_path: str = "registry"):
        self.base_path = Path(base_path)
        self.model_registry = ModelRegistry(str(self.base_path / "models"))
        self.dataset_registry = DatasetRegistry(str(self.base_path / "datasets"))
    
    def create_fairness_report(
        self,
        model_id: str,
        dataset_id: str,
        fairness_metrics: Dict[str, Any],
        bias_detection_results: Dict[str, Any],
        statistical_tests: Dict[str, Any],
        recommendations: List[str],
        auditor: str
    ) -> FairnessReport:
        """Create a comprehensive fairness report"""
        try:
            # Validate model and dataset exist
            model = self.model_registry.get_model(model_id)
            dataset = self.dataset_registry.get_dataset(dataset_id)
            
            if not model:
                raise ValueError(f"Model {model_id} not found")
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            # Determine risk level
            risk_level = self._assess_risk_level(fairness_metrics, bias_detection_results)
            
            # Determine compliance status
            compliance_status = self._assess_compliance(fairness_metrics)
            
            # Create fairness report
            report = FairnessReport(
                report_id=str(uuid.uuid4()),
                model_id=model_id,
                dataset_id=dataset_id,
                analysis_timestamp=datetime.now(),
                fairness_metrics=fairness_metrics,
                bias_detection_results=bias_detection_results,
                statistical_tests=statistical_tests,
                recommendations=recommendations,
                risk_level=risk_level,
                compliance_status=compliance_status,
                auditor=auditor
            )
            
            # Add report to model
            self.model_registry.add_fairness_report(model_id, report)
            
            logger.info(f"Created fairness report: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error creating fairness report: {e}")
            raise
    
    def _assess_risk_level(self, fairness_metrics: Dict[str, Any], bias_results: Dict[str, Any]) -> str:
        """Assess overall risk level based on fairness metrics and bias detection"""
        risk_score = 0
        
        # Check fairness metrics
        for metric_name, metric_data in fairness_metrics.items():
            if isinstance(metric_data, dict) and 'is_fair' in metric_data:
                if not metric_data['is_fair']:
                    risk_score += 1
        
        # Check bias detection results
        for bias_type, bias_data in bias_results.items():
            if isinstance(bias_data, dict) and bias_data.get('is_biased', False):
                risk_score += 1
        
        # Determine risk level
        if risk_score >= 3:
            return "high"
        elif risk_score >= 1:
            return "medium"
        else:
            return "low"
    
    def _assess_compliance(self, fairness_metrics: Dict[str, Any]) -> str:
        """Assess compliance status based on fairness metrics"""
        compliance_issues = 0
        
        for metric_name, metric_data in fairness_metrics.items():
            if isinstance(metric_data, dict) and 'is_fair' in metric_data:
                if not metric_data['is_fair']:
                    compliance_issues += 1
        
        if compliance_issues == 0:
            return "compliant"
        elif compliance_issues <= 2:
            return "needs_review"
        else:
            return "non_compliant"
    
    def get_model_lineage(self, model_id: str) -> Dict[str, Any]:
        """Get complete model lineage including datasets and fairness reports"""
        try:
            model = self.model_registry.get_model(model_id)
            if not model:
                raise ValueError(f"Model {model_id} not found")
            
            # Get associated datasets
            datasets = []
            if hasattr(model, 'training_data') and 'dataset_id' in model.training_data:
                dataset = self.dataset_registry.get_dataset(model.training_data['dataset_id'])
                if dataset:
                    datasets.append(dataset)
            
            # Get fairness reports
            fairness_reports = []
            reports_path = self.model_registry.storage_path / "fairness_reports"
            if reports_path.exists():
                for file_path in reports_path.glob(f"*_{model_id}_*.json"):
                    with open(file_path, 'r') as f:
                        report_data = json.load(f)
                        fairness_reports.append(report_data)
            
            return {
                "model": asdict(model),
                "datasets": [asdict(d) for d in datasets],
                "fairness_reports": fairness_reports
            }
            
        except Exception as e:
            logger.error(f"Error getting model lineage: {e}")
            raise
