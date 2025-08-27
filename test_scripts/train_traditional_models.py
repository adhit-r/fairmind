#!/usr/bin/env python3
"""
Traditional ML Model Trainer for FairMind Testing
Trains models on downloaded datasets for comprehensive testing
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
import xgboost as xgb

class ModelTrainer:
    def __init__(self, base_dir="test_models"):
        self.base_dir = Path(base_dir)
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
    def load_dataset(self, dataset_path):
        """Load dataset from path"""
        try:
            # Try different file formats
            for ext in ['.csv', '.parquet', '.json']:
                file_path = Path(dataset_path) / f"*{ext}"
                files = list(Path(dataset_path).glob(f"*{ext}"))
                if files:
                    file_path = files[0]
                    if ext == '.csv':
                        return pd.read_csv(file_path)
                    elif ext == '.parquet':
                        return pd.read_parquet(file_path)
                    elif ext == '.json':
                        return pd.read_json(file_path)
            
            # If no standard format found, look for any data file
            data_files = list(Path(dataset_path).glob("*"))
            if data_files:
                print(f"Found files: {[f.name for f in data_files]}")
                # Try to read the first file as CSV
                return pd.read_csv(data_files[0])
                
        except Exception as e:
            print(f"Error loading dataset from {dataset_path}: {e}")
            return None
    
    def prepare_credit_risk_data(self, df):
        """Prepare credit card fraud dataset"""
        print("Preparing credit risk data...")
        
        # For credit card fraud, we'll use 'Class' as target if it exists
        if 'Class' in df.columns:
            target_col = 'Class'
        else:
            # Create synthetic target based on amount
            df['Class'] = (df['Amount'] > df['Amount'].quantile(0.95)).astype(int)
            target_col = 'Class'
        
        # Select features (exclude target and non-numeric columns)
        feature_cols = [col for col in df.columns if col != target_col and df[col].dtype in ['int64', 'float64']]
        
        # Limit features to avoid memory issues
        if len(feature_cols) > 20:
            feature_cols = feature_cols[:20]
        
        X = df[feature_cols].fillna(0)
        y = df[target_col]
        
        return X, y, feature_cols
    
    def prepare_healthcare_data(self, df):
        """Prepare diabetes prediction dataset"""
        print("Preparing healthcare data...")
        
        # For diabetes dataset, look for common target columns
        target_candidates = ['Outcome', 'Diabetes', 'target', 'class']
        target_col = None
        
        for candidate in target_candidates:
            if candidate in df.columns:
                target_col = candidate
                break
        
        if target_col is None:
            # Create synthetic target based on glucose levels
            df['Outcome'] = (df['Glucose'] > df['Glucose'].quantile(0.8)).astype(int)
            target_col = 'Outcome'
        
        # Select numeric features
        feature_cols = [col for col in df.columns if col != target_col and df[col].dtype in ['int64', 'float64']]
        
        X = df[feature_cols].fillna(df[feature_cols].median())
        y = df[target_col]
        
        return X, y, feature_cols
    
    def prepare_hr_data(self, df):
        """Prepare HR analytics dataset"""
        print("Preparing HR analytics data...")
        
        # For HR dataset, look for attrition or similar target
        target_candidates = ['Attrition', 'target', 'class', 'left']
        target_col = None
        
        for candidate in target_candidates:
            if candidate in df.columns:
                target_col = candidate
                break
        
        if target_col is None:
            # Create synthetic target based on performance
            if 'PerformanceRating' in df.columns:
                df['Attrition'] = (df['PerformanceRating'] < 3).astype(int)
            else:
                df['Attrition'] = np.random.randint(0, 2, len(df))
            target_col = 'Attrition'
        
        # Handle categorical variables
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col != target_col:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.encoders[col] = le
        
        # Select features
        feature_cols = [col for col in df.columns if col != target_col]
        
        X = df[feature_cols].fillna(df[feature_cols].median())
        y = df[target_col]
        
        return X, y, feature_cols
    
    def train_model(self, X, y, model_type="random_forest"):
        """Train a model on the given data"""
        print(f"Training {model_type} model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        if model_type == "random_forest":
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == "logistic_regression":
            model = LogisticRegression(random_state=42, max_iter=1000)
        elif model_type == "svm":
            model = SVC(random_state=42, probability=True)
        elif model_type == "xgboost":
            model = xgb.XGBClassifier(random_state=42)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model accuracy: {accuracy:.4f}")
        
        return model, scaler, accuracy
    
    def train_credit_risk_model(self):
        """Train credit risk model"""
        print("\n🏦 Training Credit Risk Model")
        print("=" * 40)
        
        dataset_path = self.base_dir / "traditional_ml" / "credit_risk"
        df = self.load_dataset(dataset_path)
        
        if df is None:
            print("❌ Could not load credit risk dataset")
            return False
        
        X, y, feature_cols = self.prepare_credit_risk_data(df)
        
        # Train multiple models
        models = {}
        for model_type in ["random_forest", "logistic_regression", "xgboost"]:
            model, scaler, accuracy = self.train_model(X, y, model_type)
            models[model_type] = {
                "model": model,
                "scaler": scaler,
                "accuracy": accuracy,
                "features": feature_cols
            }
        
        # Save best model
        best_model_type = max(models.keys(), key=lambda k: models[k]["accuracy"])
        best_model = models[best_model_type]
        
        # Save model and metadata
        model_path = dataset_path / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(best_model, f)
        
        # Save metadata
        metadata = {
            "model_type": best_model_type,
            "accuracy": best_model["accuracy"],
            "features": feature_cols,
            "dataset_shape": df.shape,
            "target_distribution": y.value_counts().to_dict()
        }
        
        with open(dataset_path / "model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Credit risk model saved: {model_path}")
        print(f"   Best model: {best_model_type}")
        print(f"   Accuracy: {best_model['accuracy']:.4f}")
        
        return True
    
    def train_healthcare_model(self):
        """Train healthcare model"""
        print("\n🏥 Training Healthcare Model")
        print("=" * 40)
        
        dataset_path = self.base_dir / "traditional_ml" / "healthcare"
        df = self.load_dataset(dataset_path)
        
        if df is None:
            print("❌ Could not load healthcare dataset")
            return False
        
        X, y, feature_cols = self.prepare_healthcare_data(df)
        
        # Train model
        model, scaler, accuracy = self.train_model(X, y, "logistic_regression")
        
        # Save model
        model_data = {
            "model": model,
            "scaler": scaler,
            "accuracy": accuracy,
            "features": feature_cols
        }
        
        model_path = dataset_path / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Save metadata
        metadata = {
            "model_type": "logistic_regression",
            "accuracy": accuracy,
            "features": feature_cols,
            "dataset_shape": df.shape,
            "target_distribution": y.value_counts().to_dict()
        }
        
        with open(dataset_path / "model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Healthcare model saved: {model_path}")
        print(f"   Accuracy: {accuracy:.4f}")
        
        return True
    
    def train_hr_model(self):
        """Train HR analytics model"""
        print("\n👥 Training HR Analytics Model")
        print("=" * 40)
        
        dataset_path = self.base_dir / "traditional_ml" / "hiring"
        df = self.load_dataset(dataset_path)
        
        if df is None:
            print("❌ Could not load HR analytics dataset")
            return False
        
        X, y, feature_cols = self.prepare_hr_data(df)
        
        # Train model
        model, scaler, accuracy = self.train_model(X, y, "random_forest")
        
        # Save model
        model_data = {
            "model": model,
            "scaler": scaler,
            "accuracy": accuracy,
            "features": feature_cols,
            "encoders": self.encoders
        }
        
        model_path = dataset_path / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Save metadata
        metadata = {
            "model_type": "random_forest",
            "accuracy": accuracy,
            "features": feature_cols,
            "dataset_shape": df.shape,
            "target_distribution": y.value_counts().to_dict()
        }
        
        with open(dataset_path / "model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ HR analytics model saved: {model_path}")
        print(f"   Accuracy: {accuracy:.4f}")
        
        return True
    
    def train_all_models(self):
        """Train all traditional ML models"""
        print("🚀 Training All Traditional ML Models")
        print("=" * 50)
        
        results = {
            "credit_risk": self.train_credit_risk_model(),
            "healthcare": self.train_healthcare_model(),
            "hr_analytics": self.train_hr_model()
        }
        
        success_count = sum(results.values())
        total_count = len(results)
        
        print(f"\n📊 Training Summary:")
        print(f"   Successfully trained: {success_count}/{total_count} models")
        
        if success_count == total_count:
            print("🎉 All models trained successfully!")
            print("\nNext steps:")
            print("1. Review model performance")
            print("2. Upload models to FairMind")
            print("3. Run comprehensive bias testing")
        else:
            print("⚠️  Some models failed to train. Please check the errors above.")
        
        return results

def main():
    """Main function"""
    trainer = ModelTrainer()
    trainer.train_all_models()

if __name__ == "__main__":
    main()
