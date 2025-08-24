#!/usr/bin/env python3
"""
Seed the model registry with sample models for testing
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Sample models to register
SAMPLE_MODELS = [
    {
        "id": "diabetes_model_001",
        "name": "Diabetes Prediction Model",
        "version": "1.0.0",
        "type": "classification",
        "framework": "scikit-learn",
        "tags": ["healthcare", "diabetes", "classification"],
        "company": "axonome.xyz",
        "org_id": "axonome.xyz",
        "risk_level": "MEDIUM",
        "deployment_environment": "development",
        "path": "sim_test/assets/models/diabetes_model.pkl",
        "sha256": "sample_sha256_diabetes",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "titanic_model_001", 
        "name": "Titanic Survival Model",
        "version": "1.0.0",
        "type": "classification",
        "framework": "scikit-learn",
        "tags": ["survival", "titanic", "classification"],
        "company": "axonome.xyz",
        "org_id": "axonome.xyz",
        "risk_level": "LOW",
        "deployment_environment": "development",
        "path": "sim_test/assets/models/titanic_model.pkl",
        "sha256": "sample_sha256_titanic",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "credit_fraud_model_001",
        "name": "Credit Card Fraud Detection",
        "version": "1.0.0", 
        "type": "classification",
        "framework": "scikit-learn",
        "tags": ["fraud", "finance", "classification"],
        "company": "axonome.xyz",
        "org_id": "axonome.xyz",
        "risk_level": "HIGH",
        "deployment_environment": "development",
        "path": "/Users/adhi/Desktop/Documents/learn/fairmind-ethical-sandbox/sim_test/assets/models/credit_fraud_model.pkl",
        "sha256": "sample_sha256_credit_fraud",
        "created_at": datetime.now().isoformat()
    }
]

def seed_model_registry():
    """Seed the model registry with sample models"""
    registry_file = Path("models_registry.json")
    
    # Create registry if it doesn't exist
    if not registry_file.exists():
        registry_file.write_text("[]")
    
    # Read existing registry
    try:
        with open(registry_file, 'r') as f:
            existing_models = json.load(f)
    except json.JSONDecodeError:
        existing_models = []
    
    # Add sample models (avoid duplicates)
    existing_ids = {model.get("id") for model in existing_models}
    
    for model in SAMPLE_MODELS:
        if model["id"] not in existing_ids:
            existing_models.append(model)
            print(f"Added model: {model['name']}")
        else:
            print(f"Model {model['name']} already exists, skipping")
    
    # Write back to registry
    with open(registry_file, 'w') as f:
        json.dump(existing_models, f, indent=2)
    
    print(f"Model registry updated with {len(existing_models)} models")

if __name__ == "__main__":
    seed_model_registry()
