#!/usr/bin/env python3
"""
Realistic seed script - models that companies would actually register in FairMind
Companies register:
1. Models they've trained themselves
2. Models they've fine-tuned from base models
3. Models they're using via APIs (for governance tracking)
4. Models deployed in production
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "fairmind.db"

# REALISTIC models - what companies actually register
REALISTIC_MODELS = [
    # Company-trained models (most common)
    {
        "id": "acme-loan-approval-v3.2",
        "name": "ACME Bank Loan Approval Model",
        "description": "Internal credit scoring model trained on ACME Bank's historical loan data. Used for automated loan approval decisions. Requires bias monitoring for regulatory compliance (Fair Lending Act).",
        "model_type": "classification",
        "version": "3.2.0",
        "status": "active",
        "tags": json.dumps(["credit", "finance", "production", "regulatory"]),
        "metadata": json.dumps({
            "company": "ACME Bank",
            "framework": "XGBoost",
            "trained_by": "ACME ML Team",
            "training_data": "500K loan applications (2020-2024)",
            "accuracy": 0.947,
            "deployment": "production",
            "regulatory_requirements": ["Fair Lending Act", "ECOA"],
            "bias_monitoring_required": True
        })
    },
    {
        "id": "techcorp-hr-screening-v2.1",
        "name": "TechCorp Resume Screening Model",
        "description": "Fine-tuned BERT model for initial resume screening. Trained on TechCorp's successful hires. Must comply with EEOC guidelines and prevent demographic bias.",
        "model_type": "nlp",
        "version": "2.1.0",
        "status": "active",
        "tags": json.dumps(["hr", "recruiting", "nlp", "bert", "fine-tuned"]),
        "metadata": json.dumps({
            "company": "TechCorp",
            "base_model": "bert-base-uncased",
            "fine_tuned_by": "TechCorp AI Team",
            "training_data": "50K resumes from TechCorp hiring (2022-2024)",
            "accuracy": 0.892,
            "deployment": "production",
            "regulatory_requirements": ["EEOC", "Title VII"],
            "bias_monitoring_required": True,
            "protected_attributes": ["gender", "race", "age"]
        })
    },
    {
        "id": "healthcare-diagnosis-assistant-v1.5",
        "name": "MedCare Diagnosis Support System",
        "description": "Fine-tuned ResNet-50 for medical imaging analysis. Trained on MedCare's radiology dataset. Used to assist radiologists in detecting abnormalities. Requires FDA compliance tracking.",
        "model_type": "computer_vision",
        "version": "1.5.0",
        "status": "active",
        "tags": json.dumps(["medical", "imaging", "healthcare", "resnet", "fine-tuned"]),
        "metadata": json.dumps({
            "company": "MedCare Health Systems",
            "base_model": "resnet-50",
            "fine_tuned_by": "MedCare AI Lab",
            "training_data": "100K medical images (anonymized, IRB approved)",
            "accuracy": 0.967,
            "deployment": "production",
            "regulatory_requirements": ["FDA", "HIPAA"],
            "bias_monitoring_required": True,
            "protected_attributes": ["age", "sex", "ethnicity"]
        })
    },
    
    # API-based models (companies track these for governance)
    {
        "id": "acme-customer-support-gpt4",
        "name": "ACME Customer Support (GPT-4 API)",
        "description": "GPT-4 API integration for customer support chatbot. Fine-tuned with ACME's product knowledge base. Tracked in FairMind for bias monitoring and compliance with customer service regulations.",
        "model_type": "llm",
        "version": "gpt-4-turbo",
        "status": "active",
        "tags": json.dumps(["customer-support", "api", "gpt-4", "chatbot", "governance"]),
        "metadata": json.dumps({
            "company": "ACME Corp",
            "model_provider": "OpenAI",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
            "fine_tuning": "Custom fine-tune on 2M support tickets",
            "usage": "50K queries/day",
            "governance_tracking": True,
            "bias_monitoring_required": True,
            "regulatory_requirements": ["GDPR", "CCPA"]
        })
    },
    {
        "id": "techcorp-code-review-claude",
        "name": "TechCorp Code Review Assistant (Claude API)",
        "description": "Claude-3 Opus API for automated code review. Integrated into TechCorp's CI/CD pipeline. Monitored for bias in code review suggestions across different programming languages and developer demographics.",
        "model_type": "llm",
        "version": "claude-3-opus",
        "status": "active",
        "tags": json.dumps(["code-review", "api", "claude", "ci-cd", "governance"]),
        "metadata": json.dumps({
            "company": "TechCorp",
            "model_provider": "Anthropic",
            "api_endpoint": "https://api.anthropic.com/v1/messages",
            "integration": "GitHub Actions, GitLab CI",
            "usage": "10K reviews/day",
            "governance_tracking": True,
            "bias_monitoring_required": True
        })
    },
    
    # Fine-tuned models (companies fine-tune base models)
    {
        "id": "retailcorp-sentiment-llama2",
        "name": "RetailCorp Sentiment Analyzer (Fine-tuned Llama-2)",
        "description": "Llama-2 7B fine-tuned on RetailCorp's customer reviews. Analyzes sentiment across 20+ languages for global product feedback. Trained internally on RetailCorp's review dataset.",
        "model_type": "llm",
        "version": "7b-finetuned-v1.2",
        "status": "active",
        "tags": json.dumps(["sentiment", "fine-tuned", "llama-2", "multilingual"]),
        "metadata": json.dumps({
            "company": "RetailCorp",
            "base_model": "llama-2-7b-chat",
            "fine_tuned_by": "RetailCorp ML Team",
            "training_data": "5M customer reviews (2020-2024)",
            "languages": 23,
            "accuracy": 0.923,
            "deployment": "production",
            "bias_monitoring_required": True
        })
    },
    {
        "id": "fintech-fraud-detection-xgboost",
        "name": "FinTech Fraud Detection System",
        "description": "XGBoost model trained on FinTech's transaction data. Detects fraudulent transactions in real-time. Critical for compliance with financial regulations and preventing discriminatory fraud detection.",
        "model_type": "classification",
        "version": "4.1.0",
        "status": "active",
        "tags": json.dumps(["fraud", "finance", "xgboost", "real-time", "regulatory"]),
        "metadata": json.dumps({
            "company": "FinTech Payments",
            "framework": "XGBoost",
            "trained_by": "FinTech Risk Team",
            "training_data": "10M transactions (2021-2024)",
            "accuracy": 0.989,
            "latency_ms": 12,
            "deployment": "production",
            "regulatory_requirements": ["PCI-DSS", "Fair Lending"],
            "bias_monitoring_required": True
        })
    },
    
    # Production deployment models
    {
        "id": "autonomous-vehicle-perception-yolo",
        "name": "AutoDrive Object Detection (YOLOv8)",
        "description": "YOLOv8 model fine-tuned for autonomous vehicle perception. Detects vehicles, pedestrians, and traffic signs. Deployed in AutoDrive's self-driving fleet. Requires continuous bias monitoring for safety and fairness.",
        "model_type": "computer_vision",
        "version": "8.0-custom",
        "status": "active",
        "tags": json.dumps(["autonomous", "vehicle", "yolo", "safety", "production"]),
        "metadata": json.dumps({
            "company": "AutoDrive Technologies",
            "base_model": "yolov8",
            "fine_tuned_by": "AutoDrive Perception Team",
            "training_data": "500K driving scenes (diverse conditions)",
            "mAP_50": 0.892,
            "deployment": "production (fleet of 1000 vehicles)",
            "regulatory_requirements": ["NHTSA", "Safety Standards"],
            "bias_monitoring_required": True,
            "protected_attributes": ["pedestrian_demographics", "vehicle_types"]
        })
    },
    {
        "id": "legal-doc-classifier-roberta",
        "name": "LawFirm Document Classifier (RoBERTa)",
        "description": "RoBERTa model fine-tuned for legal document classification. Classifies contracts, agreements, and legal documents. Used by LawFirm for document management. Must ensure no bias in classification across document types.",
        "model_type": "nlp",
        "version": "1.3.0",
        "status": "active",
        "tags": json.dumps(["legal", "document", "roberta", "classification"]),
        "metadata": json.dumps({
            "company": "LawFirm Legal Services",
            "base_model": "roberta-base",
            "fine_tuned_by": "LawFirm Tech Team",
            "training_data": "200K legal documents (anonymized)",
            "accuracy": 0.956,
            "deployment": "production",
            "bias_monitoring_required": True
        })
    },
    {
        "id": "ecommerce-price-prediction-linear",
        "name": "ShopMart Price Optimization Model",
        "description": "Linear regression model for dynamic pricing. Predicts optimal prices based on demand, competition, and customer segments. Must ensure pricing fairness across customer demographics.",
        "model_type": "regression",
        "version": "2.0.0",
        "status": "active",
        "tags": json.dumps(["pricing", "ecommerce", "regression", "optimization"]),
        "metadata": json.dumps({
            "company": "ShopMart E-commerce",
            "framework": "Scikit-learn",
            "trained_by": "ShopMart Pricing Team",
            "training_data": "1M price points (2022-2024)",
            "r2_score": 0.876,
            "deployment": "production",
            "regulatory_requirements": ["Price Discrimination Laws"],
            "bias_monitoring_required": True
        })
    }
]

def create_tables(conn):
    """Create models table if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            model_type VARCHAR(100) NOT NULL,
            version VARCHAR(50) DEFAULT '1.0.0',
            file_path VARCHAR(500),
            file_size BIGINT,
            status VARCHAR(50) DEFAULT 'active',
            tags TEXT,
            metadata TEXT,
            created_by VARCHAR(255),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def seed_models():
    """Insert realistic models into database"""
    print(f"Seeding realistic company models into: {DB_PATH}\n")
    
    conn = sqlite3.connect(str(DB_PATH))
    create_tables(conn)
    
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    
    for model in REALISTIC_MODELS:
        try:
            # Check if exists
            cursor.execute("SELECT id FROM models WHERE id = ?", (model["id"],))
            if cursor.fetchone():
                print(f"  ⊘ Skipped: {model['name']} (already exists)")
                skipped += 1
                continue
            
            # Insert
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO models (
                    id, name, description, model_type, version, status,
                    tags, metadata, file_path, file_size, upload_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model["id"],
                model["name"],
                model["description"],
                model["model_type"],
                model["version"],
                model["status"],
                model["tags"],
                model["metadata"],
                f"/models/{model['id']}.pkl",
                50000000,
                now,
                now
            ))
            print(f"  ✓ {model['name']}")
            inserted += 1
        except Exception as e:
            print(f"  ✗ Error: {model['name']} - {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Complete! Inserted: {inserted}, Skipped: {skipped}, Total: {len(REALISTIC_MODELS)}")
    print("\nThese models represent what companies actually register in FairMind:")
    print("  • Company-trained models (credit scoring, fraud detection)")
    print("  • Fine-tuned models (BERT, Llama-2, ResNet)")
    print("  • API-based models (GPT-4, Claude) tracked for governance")
    print("  • Production deployment models requiring bias monitoring")

if __name__ == "__main__":
    seed_models()

