#!/usr/bin/env python3
"""
Create Simple AI Models Script
Generates actual model files for different frameworks without heavy dependencies
"""

import os
import pickle
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleModelGenerator:
    def __init__(self, output_dir: str = "storage/models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def create_sklearn_model(self, model_name: str, org_id: str):
        """Create a simple sklearn-compatible model"""
        # Create a simple model structure
        model_data = {
            "model_type": "sklearn_classifier",
            "features": ["feature1", "feature2", "feature3", "feature4", "feature5"],
            "classes": [0, 1],
            "coef": np.random.randn(5).tolist(),
            "intercept": float(np.random.randn()),
            "feature_importance": np.random.rand(5).tolist(),
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        model_path = self.output_dir / org_id / f"{model_name}.pkl"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Created sklearn model: {model_path}")
        return str(model_path)
    
    def create_tensorflow_model(self, model_name: str, org_id: str):
        """Create a simple tensorflow-compatible model"""
        # Create model architecture and weights
        model_data = {
            "model_type": "tensorflow_sequential",
            "layers": [
                {"type": "dense", "units": 64, "activation": "relu", "input_shape": [5]},
                {"type": "dropout", "rate": 0.2},
                {"type": "dense", "units": 32, "activation": "relu"},
                {"type": "dropout", "rate": 0.2},
                {"type": "dense", "units": 1, "activation": "sigmoid"}
            ],
            "weights": [np.random.randn(5, 64).tolist(), np.random.randn(64).tolist()],
            "optimizer": "adam",
            "loss": "binary_crossentropy",
            "metrics": ["accuracy"],
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        model_path = self.output_dir / org_id / f"{model_name}.h5"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON since we can't use tensorflow
        json_path = model_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Created tensorflow model: {json_path}")
        return str(json_path)
    
    def create_pytorch_model(self, model_name: str, org_id: str):
        """Create a simple pytorch-compatible model"""
        # Create model architecture
        model_data = {
            "model_type": "pytorch_nn",
            "layers": [
                {"type": "embedding", "vocab_size": 1000, "embedding_dim": 128},
                {"type": "lstm", "input_size": 128, "hidden_size": 256, "batch_first": True},
                {"type": "linear", "in_features": 256, "out_features": 3},
                {"type": "dropout", "p": 0.5}
            ],
            "state_dict": {
                "embedding.weight": np.random.randn(1000, 128).tolist(),
                "lstm.weight_ih_l0": np.random.randn(1024, 128).tolist(),
                "lstm.weight_hh_l0": np.random.randn(1024, 256).tolist(),
                "linear.weight": np.random.randn(3, 256).tolist(),
                "linear.bias": np.random.randn(3).tolist()
            },
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        model_path = self.output_dir / org_id / f"{model_name}.pt"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON since we can't use pytorch
        json_path = model_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Created pytorch model: {json_path}")
        return str(json_path)
    
    def create_xgboost_model(self, model_name: str, org_id: str):
        """Create a simple xgboost-compatible model"""
        # Create model structure
        model_data = {
            "model_type": "xgboost_classifier",
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "objective": "binary:logistic",
            "feature_names": ["feature1", "feature2", "feature3", "feature4", "feature5"],
            "feature_importance": np.random.rand(5).tolist(),
            "booster": {
                "trees": [{"tree_id": i, "depth": np.random.randint(3, 8)} for i in range(100)]
            },
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        model_path = self.output_dir / org_id / f"{model_name}.xgb"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON since we can't use xgboost
        json_path = model_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Created xgboost model: {json_path}")
        return str(json_path)
    
    def create_llm_config(self, model_name: str, org_id: str, llm_type: str = "gpt-4"):
        """Create LLM configuration files"""
        configs = {
            "gpt-4": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500,
                "system_prompt": "You are a helpful AI assistant for FairMind.",
                "fine_tuned": True,
                "training_data": f"{model_name}_training_data.json",
                "version": "1.0.0"
            },
            "claude": {
                "model": "claude-3-sonnet",
                "temperature": 0.8,
                "max_tokens": 1000,
                "system_prompt": "You are a specialized AI assistant for FairMind.",
                "fine_tuned": True,
                "training_data": f"{model_name}_training_data.json",
                "version": "1.0.0"
            }
        }
        
        config = configs.get(llm_type, configs["gpt-4"])
        config["model_name"] = model_name
        config["created_at"] = datetime.now().isoformat()
        
        model_path = self.output_dir / org_id / f"{model_name}.json"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Created LLM config: {model_path}")
        return str(model_path)
    
    def create_prophet_model(self, model_name: str, org_id: str):
        """Create a simple prophet-compatible model"""
        # Create time series model structure
        model_data = {
            "model_type": "prophet",
            "changepoints": np.random.randn(10).tolist(),
            "seasonality": {
                "yearly": True,
                "weekly": True,
                "daily": False
            },
            "holidays": [],
            "forecast_periods": 30,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        model_path = self.output_dir / org_id / f"{model_name}.json"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Created prophet model: {model_path}")
        return str(model_path)
    
    def generate_all_models(self):
        """Generate all sample models"""
        logger.info("Starting model generation...")
        
        models_created = []
        
        # Demo Organization Models
        models_created.append(self.create_sklearn_model("credit_risk_v2.1", "demo_org"))
        models_created.append(self.create_tensorflow_model("fraud_detection_v1.5.2", "demo_org"))
        models_created.append(self.create_sklearn_model("customer_segmentation_v1.0", "demo_org"))
        models_created.append(self.create_pytorch_model("sentiment_analysis_v1.2.1", "demo_org"))
        models_created.append(self.create_llm_config("chatbot_gpt4_finetuned", "demo_org", "gpt-4"))
        models_created.append(self.create_llm_config("claude_content_gen_v1.1", "demo_org", "claude"))
        models_created.append(self.create_tensorflow_model("medical_diagnosis_v1.0", "demo_org"))
        models_created.append(self.create_sklearn_model("recommendation_engine_v1.4", "demo_org"))
        
        # Admin Organization Models
        models_created.append(self.create_xgboost_model("loan_approval_v3.0", "admin_org"))
        models_created.append(self.create_tensorflow_model("hiring_assistant_v2.2", "admin_org"))
        models_created.append(self.create_sklearn_model("price_optimization_v1.3", "admin_org"))
        models_created.append(self.create_prophet_model("inventory_forecast_v1.1", "admin_org"))
        models_created.append(self.create_llm_config("legal_assistant_gpt4", "admin_org", "gpt-4"))
        models_created.append(self.create_llm_config("code_reviewer_claude", "admin_org", "claude"))
        
        logger.info(f"Generated {len(models_created)} model files")
        return models_created

def main():
    """Main function to generate all sample models"""
    generator = SimpleModelGenerator()
    models = generator.generate_all_models()
    
    print("\n" + "="*50)
    print("MODEL GENERATION COMPLETE")
    print("="*50)
    print(f"Generated {len(models)} model files:")
    
    for model_path in models:
        print(f"  ✓ {model_path}")
    
    print("\nModels are ready for use in the FairMind platform!")
    print("Storage location:", generator.output_dir)
    
    # Create a summary file
    summary = {
        "total_models": len(models),
        "models": models,
        "generated_at": datetime.now().isoformat(),
        "storage_location": str(generator.output_dir)
    }
    
    summary_path = generator.output_dir / "models_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_path}")

if __name__ == "__main__":
    main()
