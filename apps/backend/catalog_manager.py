#!/usr/bin/env python3
"""
Catalog Manager for Public Datasets and Models
Downloads and manages real public datasets and pre-trained models
"""

import os
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import zipfile
import tempfile
import shutil

# Configuration
CATALOG_DIR = Path("catalog")
MODELS_DIR = CATALOG_DIR / "models"
DATASETS_DIR = CATALOG_DIR / "datasets"

# Public Dataset Sources
PUBLIC_DATASETS = {
    "diabetes": {
        "name": "Diabetes Prediction Dataset",
        "source": "UCI",
        "url": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
        "columns": ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome"],
        "target": "Outcome",
        "features": ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"],
        "protected_attributes": ["Age"],
        "description": "Pima Indians Diabetes Database for predicting diabetes onset",
        "has_header": False
    },
    "titanic": {
        "name": "Titanic Survival Dataset", 
        "source": "Kaggle",
        "url": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
        "columns": ["PassengerId", "Survived", "Pclass", "Name", "Sex", "Age", "SibSp", "Parch", "Ticket", "Fare", "Cabin", "Embarked"],
        "target": "Survived",
        "features": ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
        "protected_attributes": ["Sex", "Age"],
        "description": "Titanic passenger survival data for binary classification"
    },
    "credit_fraud": {
        "name": "Credit Card Fraud Detection",
        "source": "Kaggle",
        "url": "https://raw.githubusercontent.com/curiousily/Credit-Card-Fraud-Detection-using-Autoencoders-in-Keras/master/data/creditcard.csv",
        "columns": ["Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28", "Amount", "Class"],
        "target": "Class",
        "features": ["Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28", "Amount"],
        "protected_attributes": ["Amount"],
        "description": "Credit card transaction data for fraud detection"
    },
    "heart_disease": {
        "name": "Heart Disease Prediction",
        "source": "UCI",
        "url": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/heart-disease.data.csv",
        "columns": ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"],
        "target": "target",
        "features": ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"],
        "protected_attributes": ["age", "sex"],
        "description": "Heart disease prediction dataset from UCI repository"
    }
}

# Public Model Sources (GitHub repositories with pre-trained models)
PUBLIC_MODELS = {
    "diabetes_model": {
        "name": "Diabetes Prediction Model",
        "source": "scikit-learn",
        "type": "classification",
        "framework": "scikit-learn",
        "dataset": "diabetes",
        "url": None,  # Will be trained locally
        "description": "Logistic regression model for diabetes prediction",
        "tags": ["healthcare", "diabetes", "classification", "logistic-regression"]
    },
    "titanic_model": {
        "name": "Titanic Survival Model", 
        "source": "scikit-learn",
        "type": "classification",
        "framework": "scikit-learn",
        "dataset": "titanic",
        "url": None,  # Will be trained locally
        "description": "Random forest model for survival prediction",
        "tags": ["survival", "titanic", "classification", "random-forest"]
    },
    "credit_fraud_model": {
        "name": "Credit Card Fraud Detection Model",
        "source": "GitHub",
        "type": "classification", 
        "framework": "scikit-learn",
        "dataset": "credit_fraud",
        "url": "https://raw.githubusercontent.com/saarques/credit-card-fraud-detection/master/model.pkl",
        "description": "Pre-trained model for credit card fraud detection",
        "tags": ["fraud", "finance", "classification", "isolation-forest"]
    },
    "heart_disease_model": {
        "name": "Heart Disease Prediction Model",
        "source": "scikit-learn",
        "type": "classification",
        "framework": "scikit-learn", 
        "dataset": "heart_disease",
        "url": None,  # Will be trained locally
        "description": "Support vector machine for heart disease prediction",
        "tags": ["healthcare", "heart-disease", "classification", "svm"]
    }
}

class CatalogManager:
    def __init__(self):
        self.catalog_dir = CATALOG_DIR
        self.models_dir = MODELS_DIR
        self.datasets_dir = DATASETS_DIR
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        self.catalog_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.datasets_dir.mkdir(exist_ok=True)
    
    def download_dataset(self, dataset_key: str) -> Optional[str]:
        """Download a dataset from public sources"""
        if dataset_key not in PUBLIC_DATASETS:
            print(f"Dataset {dataset_key} not found in catalog")
            return None
        
        dataset_info = PUBLIC_DATASETS[dataset_key]
        output_path = self.datasets_dir / f"{dataset_key}.csv"
        
        if output_path.exists():
            print(f"Dataset {dataset_key} already exists at {output_path}")
            return str(output_path)
        
        try:
            print(f"Downloading {dataset_key} from {dataset_info['url']}")
            response = requests.get(dataset_info['url'], timeout=30)
            response.raise_for_status()
            
            # Save the dataset
            if dataset_info.get("has_header", True):
                output_path.write_text(response.text)
            else:
                # Add header row for datasets without headers
                header = ",".join(dataset_info["columns"])
                output_path.write_text(header + "\n" + response.text)
            print(f"Downloaded {dataset_key} to {output_path}")
            
            # Create metadata file
            metadata = {
                "name": dataset_info["name"],
                "source": dataset_info["source"],
                "url": dataset_info["url"],
                "target": dataset_info["target"],
                "features": dataset_info["features"],
                "protected_attributes": dataset_info["protected_attributes"],
                "description": dataset_info["description"],
                "downloaded_at": datetime.now().isoformat(),
                "rows": len(response.text.split('\n')) - 1,  # Approximate
                "columns": dataset_info["columns"]
            }
            
            metadata_path = self.datasets_dir / f"{dataset_key}_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            return str(output_path)
            
        except Exception as e:
            print(f"Failed to download {dataset_key}: {e}")
            return None
    
    def download_model(self, model_key: str) -> Optional[str]:
        """Download a pre-trained model from public sources"""
        if model_key not in PUBLIC_MODELS:
            print(f"Model {model_key} not found in catalog")
            return None
        
        model_info = PUBLIC_MODELS[model_key]
        output_path = self.models_dir / f"{model_key}.pkl"
        
        if output_path.exists():
            print(f"Model {model_key} already exists at {output_path}")
            return str(output_path)
        
        # If no URL, we'll train the model locally
        if not model_info.get("url"):
            print(f"Model {model_key} needs to be trained locally")
            return self._train_model_locally(model_key)
        
        try:
            print(f"Downloading {model_key} from {model_info['url']}")
            response = requests.get(model_info['url'], timeout=30)
            response.raise_for_status()
            
            # Save the model
            output_path.write_bytes(response.content)
            print(f"Downloaded {model_key} to {output_path}")
            
            # Create metadata file
            metadata = {
                "name": model_info["name"],
                "source": model_info["source"],
                "type": model_info["type"],
                "framework": model_info["framework"],
                "dataset": model_info["dataset"],
                "url": model_info["url"],
                "description": model_info["description"],
                "tags": model_info["tags"],
                "downloaded_at": datetime.now().isoformat()
            }
            
            metadata_path = self.models_dir / f"{model_key}_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            return str(output_path)
            
        except Exception as e:
            print(f"Failed to download {model_key}: {e}")
            return None
    
    def _train_model_locally(self, model_key: str) -> Optional[str]:
        """Train a model locally using the corresponding dataset"""
        model_info = PUBLIC_MODELS[model_key]
        dataset_key = model_info["dataset"]
        
        # Download dataset first
        dataset_path = self.download_dataset(dataset_key)
        if not dataset_path:
            print(f"Failed to download dataset {dataset_key} for model {model_key}")
            return None
        
        try:
            # Load dataset
            df = pd.read_csv(dataset_path)
            dataset_info = PUBLIC_DATASETS[dataset_key]
            
            # Prepare features and target
            X = df[dataset_info["features"]]
            y = df[dataset_info["target"]]
            
            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(0)
            
            # Train model based on type
            if model_key == "diabetes_model":
                from sklearn.linear_model import LogisticRegression
                model = LogisticRegression(random_state=42)
            elif model_key == "titanic_model":
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_key == "heart_disease_model":
                from sklearn.svm import SVC
                model = SVC(probability=True, random_state=42)
            else:
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Train the model
            model.fit(X, y)
            
            # Save the model
            output_path = self.models_dir / f"{model_key}.pkl"
            import joblib
            joblib.dump(model, output_path)
            
            print(f"Trained and saved {model_key} to {output_path}")
            
            # Create metadata
            metadata = {
                "name": model_info["name"],
                "source": "locally_trained",
                "type": model_info["type"],
                "framework": model_info["framework"],
                "dataset": model_info["dataset"],
                "description": model_info["description"],
                "tags": model_info["tags"],
                "trained_at": datetime.now().isoformat(),
                "accuracy": model.score(X, y)
            }
            
            metadata_path = self.models_dir / f"{model_key}_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            return str(output_path)
            
        except Exception as e:
            print(f"Failed to train {model_key}: {e}")
            return None
    
    def get_available_datasets(self) -> List[Dict]:
        """Get list of available datasets with metadata"""
        datasets = []
        for key, info in PUBLIC_DATASETS.items():
            dataset_path = self.datasets_dir / f"{key}.csv"
            metadata_path = self.datasets_dir / f"{key}_metadata.json"
            
            dataset_info = {
                "key": key,
                "name": info["name"],
                "source": info["source"],
                "description": info["description"],
                "target": info["target"],
                "features": info["features"],
                "protected_attributes": info["protected_attributes"],
                "available": dataset_path.exists(),
                "path": str(dataset_path) if dataset_path.exists() else None
            }
            
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text())
                    dataset_info.update(metadata)
                except:
                    pass
            
            datasets.append(dataset_info)
        
        return datasets
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available models with metadata"""
        models = []
        for key, info in PUBLIC_MODELS.items():
            model_path = self.models_dir / f"{key}.pkl"
            metadata_path = self.models_dir / f"{key}_metadata.json"
            
            model_info = {
                "key": key,
                "name": info["name"],
                "source": info["source"],
                "type": info["type"],
                "framework": info["framework"],
                "dataset": info["dataset"],
                "description": info["description"],
                "tags": info["tags"],
                "available": model_path.exists(),
                "path": str(model_path) if model_path.exists() else None
            }
            
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text())
                    model_info.update(metadata)
                except:
                    pass
            
            models.append(model_info)
        
        return models
    
    def setup_catalog(self):
        """Download all available datasets and models"""
        print("Setting up catalog with public datasets and models...")
        
        # Download datasets
        print("\nDownloading datasets...")
        for dataset_key in PUBLIC_DATASETS:
            self.download_dataset(dataset_key)
        
        # Download/train models
        print("\nDownloading/training models...")
        for model_key in PUBLIC_MODELS:
            self.download_model(model_key)
        
        print("\nCatalog setup complete!")
        print(f"Datasets: {len([d for d in self.get_available_datasets() if d['available']])} available")
        print(f"Models: {len([m for m in self.get_available_models() if m['available']])} available")

def main():
    """Main function to set up the catalog"""
    catalog = CatalogManager()
    catalog.setup_catalog()

if __name__ == "__main__":
    main()
