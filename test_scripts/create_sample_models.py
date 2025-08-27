#!/usr/bin/env python3
"""
Create Sample Models for FairMind Testing
Generates sample models when Kaggle datasets aren't available
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

class SampleModelCreator:
    def __init__(self, base_dir="test_models"):
        self.base_dir = Path(base_dir)
        
    def create_credit_risk_data(self):
        """Create synthetic credit risk data"""
        np.random.seed(42)
        n_samples = 1000
        
        # Generate synthetic features
        data = {
            'age': np.random.normal(35, 10, n_samples),
            'income': np.random.normal(50000, 20000, n_samples),
            'credit_score': np.random.normal(700, 100, n_samples),
            'debt_ratio': np.random.uniform(0, 1, n_samples),
            'payment_history': np.random.normal(0, 1, n_samples),
            'utilization_rate': np.random.uniform(0, 1, n_samples),
            'gender': np.random.choice([0, 1], n_samples),
            'education': np.random.choice([0, 1, 2, 3], n_samples)
        }
        
        # Create target based on features
        risk_score = (
            -0.1 * data['age'] + 
            -0.00001 * data['income'] + 
            -0.01 * data['credit_score'] + 
            0.5 * data['debt_ratio'] + 
            0.3 * data['payment_history'] + 
            0.4 * data['utilization_rate'] +
            0.1 * data['gender'] +
            -0.1 * data['education']
        )
        
        data['fraud'] = (risk_score > np.median(risk_score)).astype(int)
        
        return pd.DataFrame(data)
    
    def create_healthcare_data(self):
        """Create synthetic healthcare data"""
        np.random.seed(42)
        n_samples = 800
        
        data = {
            'age': np.random.normal(45, 15, n_samples),
            'bmi': np.random.normal(25, 5, n_samples),
            'glucose': np.random.normal(120, 30, n_samples),
            'blood_pressure': np.random.normal(80, 10, n_samples),
            'insulin': np.random.normal(100, 50, n_samples),
            'skin_thickness': np.random.normal(20, 10, n_samples),
            'pregnancies': np.random.poisson(2, n_samples),
            'gender': np.random.choice([0, 1], n_samples)
        }
        
        # Create diabetes risk
        diabetes_risk = (
            0.02 * data['age'] + 
            0.05 * data['bmi'] + 
            0.01 * data['glucose'] + 
            0.01 * data['blood_pressure'] + 
            0.005 * data['insulin'] +
            0.01 * data['skin_thickness'] +
            0.1 * data['pregnancies']
        )
        
        data['diabetes'] = (diabetes_risk > np.median(diabetes_risk)).astype(int)
        
        return pd.DataFrame(data)
    
    def create_hr_data(self):
        """Create synthetic HR analytics data"""
        np.random.seed(42)
        n_samples = 600
        
        data = {
            'age': np.random.normal(35, 8, n_samples),
            'years_at_company': np.random.exponential(3, n_samples),
            'salary': np.random.normal(60000, 20000, n_samples),
            'performance_rating': np.random.normal(3, 0.5, n_samples),
            'satisfaction_level': np.random.uniform(0, 1, n_samples),
            'work_accident': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
            'promotion_last_5years': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
            'gender': np.random.choice([0, 1], n_samples),
            'department': np.random.choice([0, 1, 2, 3], n_samples)
        }
        
        # Create attrition risk
        attrition_risk = (
            -0.02 * data['age'] + 
            -0.1 * data['years_at_company'] + 
            -0.000001 * data['salary'] + 
            -0.3 * data['performance_rating'] + 
            -0.5 * data['satisfaction_level'] +
            0.2 * data['work_accident'] +
            -0.3 * data['promotion_last_5years']
        )
        
        data['attrition'] = (attrition_risk > np.median(attrition_risk)).astype(int)
        
        return pd.DataFrame(data)
    
    def train_and_save_model(self, df, model_name, target_col, model_type="random_forest"):
        """Train and save a model"""
        print(f"Training {model_name} model...")
        
        # Prepare features and target
        feature_cols = [col for col in df.columns if col != target_col]
        X = df[feature_cols]
        y = df[target_col]
        
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
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Save model
        model_dir = self.base_dir / "traditional_ml" / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": model,
            "scaler": scaler,
            "accuracy": accuracy,
            "features": feature_cols
        }
        
        with open(model_dir / "model.pkl", 'wb') as f:
            pickle.dump(model_data, f)
        
        # Save metadata
        metadata = {
            "model_name": model_name,
            "model_type": model_type,
            "accuracy": accuracy,
            "features": feature_cols,
            "dataset_shape": df.shape,
            "target_distribution": y.value_counts().to_dict(),
            "synthetic": True
        }
        
        with open(model_dir / "model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save sample data
        df.to_csv(model_dir / "sample_data.csv", index=False)
        
        print(f"✅ {model_name} model saved (accuracy: {accuracy:.4f})")
        return model_data
    
    def create_all_sample_models(self):
        """Create all sample models"""
        print("🚀 Creating Sample Models for FairMind Testing")
        print("=" * 50)
        
        # Create credit risk model
        print("\n🏦 Creating Credit Risk Model")
        credit_data = self.create_credit_risk_data()
        self.train_and_save_model(credit_data, "credit_risk", "fraud", "random_forest")
        
        # Create healthcare model
        print("\n🏥 Creating Healthcare Model")
        healthcare_data = self.create_healthcare_data()
        self.train_and_save_model(healthcare_data, "healthcare", "diabetes", "logistic_regression")
        
        # Create HR analytics model
        print("\n👥 Creating HR Analytics Model")
        hr_data = self.create_hr_data()
        self.train_and_save_model(hr_data, "hiring", "attrition", "random_forest")
        
        print("\n🎉 All sample models created successfully!")
        print("\nNext steps:")
        print("1. Run comprehensive FairMind testing")
        print("2. Test bias detection features")
        print("3. Generate AI BOM reports")

def main():
    """Main function"""
    creator = SampleModelCreator()
    creator.create_all_sample_models()

if __name__ == "__main__":
    main()
