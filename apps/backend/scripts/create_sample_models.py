#!/usr/bin/env python3
"""
Create Sample AI Models Script
Generates actual model files for different frameworks and use cases
"""

import os
import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Try to import ML libraries
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("scikit-learn not available - skipping sklearn models")

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    print("joblib not available - using pickle")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("xgboost not available - skipping xgboost models")

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("tensorflow not available - skipping tensorflow models")

try:
    import torch
    import torch.nn as nn
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("pytorch not available - skipping pytorch models")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleModelGenerator:
    def __init__(self, output_dir: str = "storage/models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_credit_risk_model(self, org_id: str = "demo_org"):
        """Generate a credit risk assessment model"""
        if not SKLEARN_AVAILABLE:
            return self._create_mock_model("credit_risk", org_id)
        
        # Create synthetic credit data
        np.random.seed(42)
        n_samples = 1000
        
        # Features: age, income, credit_score, debt_ratio, payment_history
        age = np.random.normal(35, 10, n_samples)
        income = np.random.normal(50000, 20000, n_samples)
        credit_score = np.random.normal(700, 100, n_samples)
        debt_ratio = np.random.uniform(0, 0.8, n_samples)
        payment_history = np.random.randint(0, 100, n_samples)
        
        X = np.column_stack([age, income, credit_score, debt_ratio, payment_history])
        
        # Target: credit risk (0 = low risk, 1 = high risk)
        risk_score = (age * 0.1 + income * -0.00001 + credit_score * -0.01 + 
                     debt_ratio * 2 + payment_history * -0.02)
        y = (risk_score > np.median(risk_score)).astype(int)
        
        # Train model
        model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Save model
        model_path = self.output_dir / org_id / "credit_risk_v2.1.pkl"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        if JOBLIB_AVAILABLE:
            joblib.dump(model, model_path)
        else:
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        
        logger.info(f"Created credit risk model: {model_path}")
        return str(model_path)
    
    def generate_fraud_detection_model(self, org_id: str = "demo_org"):
        """Generate a fraud detection model"""
        if not TENSORFLOW_AVAILABLE:
            return self._create_mock_model("fraud_detection", org_id)
        
        # Create synthetic transaction data
        np.random.seed(42)
        n_samples = 2000
        
        # Features: amount, time_of_day, location_distance, device_type, user_age
        amount = np.random.exponential(100, n_samples)
        time_of_day = np.random.uniform(0, 24, n_samples)
        location_distance = np.random.exponential(50, n_samples)
        device_type = np.random.randint(0, 4, n_samples)  # 0=mobile, 1=desktop, 2=tablet, 3=unknown
        user_age = np.random.normal(35, 10, n_samples)
        
        X = np.column_stack([amount, time_of_day, location_distance, device_type, user_age])
        
        # Target: fraud (0 = legitimate, 1 = fraud)
        fraud_prob = (amount * 0.001 + (time_of_day - 12)**2 * 0.01 + 
                     location_distance * 0.01 + (device_type == 3) * 0.3)
        y = (np.random.random(n_samples) < fraud_prob).astype(int)
        
        # Create simple neural network
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(5,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X, y, epochs=10, batch_size=32, verbose=0)
        
        # Save model
        model_path = self.output_dir / org_id / "fraud_detection_v1.5.2.h5"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(model_path)
        
        logger.info(f"Created fraud detection model: {model_path}")
        return str(model_path)
    
    def generate_customer_segmentation_model(self, org_id: str = "demo_org"):
        """Generate a customer segmentation model"""
        if not SKLEARN_AVAILABLE:
            return self._create_mock_model("customer_segmentation", org_id)
        
        # Create synthetic customer data
        np.random.seed(42)
        n_samples = 1500
        
        # Features: age, income, spending_score, loyalty_years, purchase_frequency
        age = np.random.normal(40, 15, n_samples)
        income = np.random.normal(60000, 25000, n_samples)
        spending_score = np.random.uniform(0, 100, n_samples)
        loyalty_years = np.random.exponential(3, n_samples)
        purchase_frequency = np.random.poisson(5, n_samples)
        
        X = np.column_stack([age, income, spending_score, loyalty_years, purchase_frequency])
        
        # Train clustering model
        model = KMeans(n_clusters=5, random_state=42)
        model.fit(X)
        
        # Save model
        model_path = self.output_dir / org_id / "customer_segmentation_v1.0.pkl"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        if JOBLIB_AVAILABLE:
            joblib.dump(model, model_path)
        else:
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        
        logger.info(f"Created customer segmentation model: {model_path}")
        return str(model_path)
    
    def generate_sentiment_analysis_model(self, org_id: str = "demo_org"):
        """Generate a sentiment analysis model"""
        if not PYTORCH_AVAILABLE:
            return self._create_mock_model("sentiment_analysis", org_id)
        
        # Create simple neural network for sentiment analysis
        class SentimentModel(nn.Module):
            def __init__(self, vocab_size=1000, embedding_dim=128, hidden_dim=256):
                super(SentimentModel, self).__init__()
                self.embedding = nn.Embedding(vocab_size, embedding_dim)
                self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
                self.fc = nn.Linear(hidden_dim, 3)  # 3 classes: negative, neutral, positive
                self.dropout = nn.Dropout(0.5)
                
            def forward(self, x):
                embedded = self.embedding(x)
                lstm_out, _ = self.lstm(embedded)
                pooled = torch.mean(lstm_out, dim=1)
                dropped = self.dropout(pooled)
                output = self.fc(dropped)
                return output
        
        model = SentimentModel()
        
        # Save model
        model_path = self.output_dir / org_id / "sentiment_analysis_v1.2.1.pt"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), model_path)
        
        logger.info(f"Created sentiment analysis model: {model_path}")
        return str(model_path)
    
    def generate_loan_approval_model(self, org_id: str = "admin_org"):
        """Generate a loan approval model"""
        if not XGBOOST_AVAILABLE:
            return self._create_mock_model("loan_approval", org_id)
        
        # Create synthetic loan application data
        np.random.seed(42)
        n_samples = 1200
        
        # Features: income, credit_score, debt_to_income, employment_years, loan_amount
        income = np.random.normal(75000, 30000, n_samples)
        credit_score = np.random.normal(720, 80, n_samples)
        debt_to_income = np.random.uniform(0.1, 0.6, n_samples)
        employment_years = np.random.exponential(5, n_samples)
        loan_amount = np.random.uniform(10000, 500000, n_samples)
        
        X = np.column_stack([income, credit_score, debt_to_income, employment_years, loan_amount])
        
        # Target: loan approval (0 = denied, 1 = approved)
        approval_score = (income * 0.00001 + credit_score * 0.01 + 
                         (1 - debt_to_income) * 2 + employment_years * 0.1 + 
                         (loan_amount / income) * -0.5)
        y = (approval_score > np.median(approval_score)).astype(int)
        
        # Train XGBoost model
        model = xgb.XGBClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Save model
        model_path = self.output_dir / org_id / "loan_approval_v3.0.xgb"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(model_path))
        
        logger.info(f"Created loan approval model: {model_path}")
        return str(model_path)
    
    def generate_hiring_assistant_model(self, org_id: str = "admin_org"):
        """Generate a hiring assistant model"""
        if not TENSORFLOW_AVAILABLE:
            return self._create_mock_model("hiring_assistant", org_id)
        
        # Create synthetic resume data
        np.random.seed(42)
        n_samples = 800
        
        # Features: years_experience, education_level, skills_match, interview_score, references
        years_experience = np.random.exponential(5, n_samples)
        education_level = np.random.randint(1, 5, n_samples)  # 1=high school, 2=bachelor, 3=master, 4=phd
        skills_match = np.random.uniform(0.3, 1.0, n_samples)
        interview_score = np.random.normal(7, 1.5, n_samples)
        references = np.random.randint(0, 4, n_samples)
        
        X = np.column_stack([years_experience, education_level, skills_match, interview_score, references])
        
        # Target: hire recommendation (0 = not recommended, 1 = recommended)
        hire_score = (years_experience * 0.1 + education_level * 0.2 + 
                     skills_match * 2 + interview_score * 0.3 + references * 0.1)
        y = (hire_score > np.median(hire_score)).astype(int)
        
        # Create neural network
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(5,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X, y, epochs=15, batch_size=32, verbose=0)
        
        # Save model
        model_path = self.output_dir / org_id / "hiring_assistant_v2.2.h5"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(model_path)
        
        logger.info(f"Created hiring assistant model: {model_path}")
        return str(model_path)
    
    def generate_llm_configs(self):
        """Generate LLM configuration files"""
        # Customer Support Chatbot (GPT-4)
        chatbot_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 500,
            "system_prompt": "You are a helpful customer support assistant for FairMind. Provide accurate, helpful responses to customer inquiries.",
            "fine_tuned": True,
            "training_data": "customer_support_conversations.json",
            "version": "1.0.0"
        }
        
        chatbot_path = self.output_dir / "demo_org" / "chatbot_gpt4_finetuned.json"
        chatbot_path.parent.mkdir(parents=True, exist_ok=True)
        with open(chatbot_path, 'w') as f:
            json.dump(chatbot_config, f, indent=2)
        
        # Marketing Content Generator (Claude)
        content_config = {
            "model": "claude-3-sonnet",
            "temperature": 0.8,
            "max_tokens": 1000,
            "system_prompt": "You are a marketing content specialist. Create engaging, brand-consistent content for various marketing channels.",
            "fine_tuned": True,
            "training_data": "marketing_content_samples.json",
            "version": "1.1.0"
        }
        
        content_path = self.output_dir / "demo_org" / "claude_content_gen_v1.1.json"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with open(content_path, 'w') as f:
            json.dump(content_config, f, indent=2)
        
        # Legal Document Assistant (GPT-4)
        legal_config = {
            "model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 2000,
            "system_prompt": "You are a legal document analysis assistant. Review and analyze legal documents for compliance and risk assessment.",
            "fine_tuned": True,
            "training_data": "legal_documents.json",
            "version": "1.0.0"
        }
        
        legal_path = self.output_dir / "admin_org" / "legal_assistant_gpt4.json"
        legal_path.parent.mkdir(parents=True, exist_ok=True)
        with open(legal_path, 'w') as f:
            json.dump(legal_config, f, indent=2)
        
        # Code Reviewer (Claude)
        code_config = {
            "model": "claude-3-sonnet",
            "temperature": 0.2,
            "max_tokens": 1500,
            "system_prompt": "You are a code review assistant. Analyze code for security vulnerabilities, best practices, and potential improvements.",
            "fine_tuned": True,
            "training_data": "code_review_samples.json",
            "version": "1.2.0"
        }
        
        code_path = self.output_dir / "admin_org" / "code_reviewer_claude.json"
        code_path.parent.mkdir(parents=True, exist_ok=True)
        with open(code_path, 'w') as f:
            json.dump(code_config, f, indent=2)
        
        logger.info("Created LLM configuration files")
        return [str(chatbot_path), str(content_path), str(legal_path), str(code_path)]
    
    def _create_mock_model(self, model_type: str, org_id: str):
        """Create a mock model file when ML libraries are not available"""
        mock_data = {
            "model_type": model_type,
            "framework": "mock",
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "description": f"Mock {model_type} model for testing"
        }
        
        model_path = self.output_dir / org_id / f"{model_type}_mock.json"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'w') as f:
            json.dump(mock_data, f, indent=2)
        
        logger.info(f"Created mock model: {model_path}")
        return str(model_path)
    
    def generate_all_models(self):
        """Generate all sample models"""
        logger.info("Starting model generation...")
        
        models_created = []
        
        # Demo Organization Models
        models_created.append(self.generate_credit_risk_model("demo_org"))
        models_created.append(self.generate_fraud_detection_model("demo_org"))
        models_created.append(self.generate_customer_segmentation_model("demo_org"))
        models_created.append(self.generate_sentiment_analysis_model("demo_org"))
        
        # Admin Organization Models
        models_created.append(self.generate_loan_approval_model("admin_org"))
        models_created.append(self.generate_hiring_assistant_model("admin_org"))
        
        # LLM Configurations
        llm_configs = self.generate_llm_configs()
        models_created.extend(llm_configs)
        
        logger.info(f"Generated {len(models_created)} model files")
        return models_created

def main():
    """Main function to generate all sample models"""
    generator = SampleModelGenerator()
    models = generator.generate_all_models()
    
    print("\n" + "="*50)
    print("MODEL GENERATION COMPLETE")
    print("="*50)
    print(f"Generated {len(models)} model files:")
    
    for model_path in models:
        print(f"  ✓ {model_path}")
    
    print("\nModels are ready for use in the FairMind platform!")
    print("Storage location:", generator.output_dir)

if __name__ == "__main__":
    main()
