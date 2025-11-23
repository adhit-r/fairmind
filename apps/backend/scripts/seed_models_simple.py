#!/usr/bin/env python3
"""
Simple script to seed real ML and LLM models directly into SQLite database
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "fairmind.db"

# Real ML and LLM models data
REAL_MODELS = [
    {
        "id": "xgboost-credit-scoring-v2.3.1",
        "name": "XGBoost Credit Scoring",
        "description": "Gradient boosting model for credit risk assessment using financial features. Trained on 500K loan applications with 95% accuracy.",
        "model_type": "classification",
        "version": "2.3.1",
        "status": "active",
        "tags": json.dumps(["credit", "finance", "xgboost", "production"]),
        "metadata": json.dumps({
            "framework": "XGBoost",
            "accuracy": 0.947,
            "training_samples": 500000,
            "features": 45
        })
    },
    {
        "id": "random-forest-fraud-v1.8.5",
        "name": "Random Forest Fraud Detection",
        "description": "Ensemble model for detecting fraudulent transactions in real-time payment processing. Handles 10M+ transactions daily.",
        "model_type": "classification",
        "version": "1.8.5",
        "status": "active",
        "tags": json.dumps(["fraud", "security", "random-forest", "real-time"]),
        "metadata": json.dumps({
            "framework": "Scikit-learn",
            "accuracy": 0.989,
            "training_samples": 2000000,
            "latency_ms": 12
        })
    },
    {
        "id": "linear-regression-pricing-v3.1.0",
        "name": "Linear Regression Price Prediction",
        "description": "Linear regression model for predicting real estate prices based on location, size, and amenities.",
        "model_type": "regression",
        "version": "3.1.0",
        "status": "active",
        "tags": json.dumps(["real-estate", "pricing", "regression"]),
        "metadata": json.dumps({
            "framework": "Scikit-learn",
            "r2_score": 0.876,
            "training_samples": 150000
        })
    },
    {
        "id": "gpt4-customer-support-v4.0.3",
        "name": "GPT-4 Fine-tuned Customer Support",
        "description": "Fine-tuned GPT-4 model for customer support automation. Trained on 2M support tickets. Handles 50K+ queries daily.",
        "model_type": "llm",
        "version": "4.0.3",
        "status": "active",
        "tags": json.dumps(["llm", "gpt", "customer-support", "chatbot"]),
        "metadata": json.dumps({
            "base_model": "gpt-4",
            "parameters": "1.7T",
            "accuracy": 0.934,
            "fine_tuning_samples": 2000000
        })
    },
    {
        "id": "bert-document-classifier-v2.1.0",
        "name": "BERT-based Document Classifier",
        "description": "BERT model fine-tuned for document classification in legal tech. Classifies contracts and legal documents into 50+ categories.",
        "model_type": "nlp",
        "version": "2.1.0",
        "status": "active",
        "tags": json.dumps(["bert", "nlp", "document", "legal"]),
        "metadata": json.dumps({
            "base_model": "bert-base-uncased",
            "parameters": "110M",
            "accuracy": 0.956,
            "fine_tuning_samples": 150000
        })
    },
    {
        "id": "llama2-code-assistant-v7.0.2",
        "name": "Llama-2 7B Code Assistant",
        "description": "Fine-tuned Llama-2 7B model for code generation and review. Trained on 1M code examples across Python, JavaScript, and TypeScript.",
        "model_type": "llm",
        "version": "7.0.2",
        "status": "active",
        "tags": json.dumps(["llm", "llama", "code", "generation"]),
        "metadata": json.dumps({
            "base_model": "llama-2-7b-chat",
            "parameters": "7B",
            "code_accuracy": 0.872,
            "fine_tuning_samples": 1000000
        })
    },
    {
        "id": "claude3-summarization-v3.1.0",
        "name": "Claude-3 Opus Summarization",
        "description": "Claude-3 Opus fine-tuned for long-form document summarization. Processes research papers, reports, and technical documentation.",
        "model_type": "llm",
        "version": "3.1.0",
        "status": "active",
        "tags": json.dumps(["llm", "claude", "summarization", "document"]),
        "metadata": json.dumps({
            "base_model": "claude-3-opus",
            "context_length": 200000,
            "rouge_l": 0.891,
            "fine_tuning_samples": 500000
        })
    },
    {
        "id": "resnet50-medical-v4.2.1",
        "name": "ResNet-50 Image Classification",
        "description": "Deep convolutional neural network for image classification. Pre-trained on ImageNet, fine-tuned for medical imaging.",
        "model_type": "computer_vision",
        "version": "4.2.1",
        "status": "active",
        "tags": json.dumps(["vision", "medical", "resnet", "cnn"]),
        "metadata": json.dumps({
            "framework": "PyTorch",
            "algorithm": "ResNet-50",
            "accuracy": 0.967,
            "training_samples": 50000
        })
    },
    {
        "id": "yolov8-autonomous-v8.0.5",
        "name": "YOLOv8 Object Detection",
        "description": "Real-time object detection model for autonomous vehicle perception. Detects vehicles, pedestrians, and traffic signs.",
        "model_type": "computer_vision",
        "version": "8.0.5",
        "status": "active",
        "tags": json.dumps(["object-detection", "autonomous", "yolo"]),
        "metadata": json.dumps({
            "framework": "PyTorch",
            "mAP_50": 0.892,
            "fps": 45,
            "training_samples": 200000
        })
    },
    {
        "id": "stable-diffusion-v2.1.0",
        "name": "Stable Diffusion Image Generation",
        "description": "Stable Diffusion v2.1 model for text-to-image generation. Used for marketing content creation and design automation.",
        "model_type": "computer_vision",
        "version": "2.1.0",
        "status": "active",
        "tags": json.dumps(["diffusion", "image-generation", "stable-diffusion"]),
        "metadata": json.dumps({
            "base_model": "stable-diffusion-v2-1",
            "parameters": "860M",
            "fid_score": 12.8,
            "training_samples": 2000000
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
    print("✓ Created models table")

def seed_models():
    """Insert models into database"""
    print(f"Connecting to database: {DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    create_tables(conn)
    
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    
    for model in REAL_MODELS:
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
            print(f"  ✓ Inserted: {model['name']} ({model['model_type']})")
            inserted += 1
        except Exception as e:
            print(f"  ✗ Error: {model['name']} - {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Complete! Inserted: {inserted}, Skipped: {skipped}, Total: {len(REAL_MODELS)}")

if __name__ == "__main__":
    seed_models()

