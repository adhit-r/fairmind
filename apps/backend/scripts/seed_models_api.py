#!/usr/bin/env python3
"""
Seed script to add real ML and LLM models via API endpoint
This uses the actual API registration endpoint to ensure proper data insertion
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Real ML and LLM models data
REAL_MODELS = [
    # Traditional ML Models
    {
        "model_id": "xgboost-credit-scoring-v2.3.1",
        "name": "XGBoost Credit Scoring",
        "model_type": "classification",
        "version": "2.3.1",
        "description": "Gradient boosting model for credit risk assessment using financial features. Trained on 500K loan applications with 95% accuracy.",
        "capabilities": ["credit_scoring", "risk_assessment", "financial_analysis"],
        "input_format": "JSON with financial features",
        "output_format": "Credit score (0-1000) and risk probability"
    },
    {
        "model_id": "random-forest-fraud-v1.8.5",
        "name": "Random Forest Fraud Detection",
        "model_type": "classification",
        "version": "1.8.5",
        "description": "Ensemble model for detecting fraudulent transactions in real-time payment processing. Handles 10M+ transactions daily.",
        "capabilities": ["fraud_detection", "anomaly_detection", "real_time_processing"],
        "input_format": "JSON with transaction features",
        "output_format": "Fraud probability and risk level"
    },
    {
        "model_id": "linear-regression-pricing-v3.1.0",
        "name": "Linear Regression Price Prediction",
        "model_type": "regression",
        "version": "3.1.0",
        "description": "Linear regression model for predicting real estate prices based on location, size, and amenities. Used in property valuation platform.",
        "capabilities": ["price_prediction", "regression", "real_estate"],
        "input_format": "JSON with property features",
        "output_format": "Predicted price in USD"
    },
    {
        "model_id": "svm-churn-v1.5.2",
        "name": "SVM Customer Churn Prediction",
        "model_type": "classification",
        "version": "1.5.2",
        "description": "Support Vector Machine model for predicting customer churn in subscription services. Helps retention teams prioritize interventions.",
        "capabilities": ["churn_prediction", "customer_analytics", "retention"],
        "input_format": "JSON with customer features",
        "output_format": "Churn probability and risk category"
    },
    {
        "model_id": "kmeans-segmentation-v2.0.0",
        "name": "K-Means Customer Segmentation",
        "model_type": "clustering",
        "version": "2.0.0",
        "description": "Unsupervised clustering model for segmenting customers into distinct groups based on purchasing behavior and demographics.",
        "capabilities": ["customer_segmentation", "clustering", "marketing"],
        "input_format": "JSON with customer behavior features",
        "output_format": "Cluster assignment and segment characteristics"
    },
    
    # Deep Learning Models
    {
        "model_id": "resnet50-medical-v4.2.1",
        "name": "ResNet-50 Image Classification",
        "model_type": "computer_vision",
        "version": "4.2.1",
        "description": "Deep convolutional neural network for image classification. Pre-trained on ImageNet, fine-tuned for medical imaging. Used in radiology workflow.",
        "capabilities": ["image_classification", "medical_imaging", "cnn"],
        "input_format": "Image file (PNG/JPEG) or base64 encoded",
        "output_format": "Classification probabilities and top predictions"
    },
    {
        "model_id": "yolov8-autonomous-v8.0.5",
        "name": "YOLOv8 Object Detection",
        "model_type": "computer_vision",
        "version": "8.0.5",
        "description": "Real-time object detection model for autonomous vehicle perception. Detects vehicles, pedestrians, and traffic signs with high precision.",
        "capabilities": ["object_detection", "autonomous_vehicles", "real_time"],
        "input_format": "Image file (PNG/JPEG) or video frame",
        "output_format": "Bounding boxes, class labels, and confidence scores"
    },
    
    # LLM Models
    {
        "model_id": "gpt4-customer-support-v4.0.3",
        "name": "GPT-4 Fine-tuned Customer Support",
        "model_type": "llm",
        "version": "4.0.3",
        "description": "Fine-tuned GPT-4 model for customer support automation. Trained on 2M support tickets with company-specific knowledge base. Handles 50K+ queries daily.",
        "capabilities": ["customer_support", "chatbot", "text_generation", "qa"],
        "input_format": "Text prompt or conversation history",
        "output_format": "Generated response text"
    },
    {
        "model_id": "bert-document-classifier-v2.1.0",
        "name": "BERT-based Document Classifier",
        "model_type": "nlp",
        "version": "2.1.0",
        "description": "BERT model fine-tuned for document classification in legal tech. Classifies contracts, agreements, and legal documents into 50+ categories.",
        "capabilities": ["document_classification", "nlp", "legal_tech"],
        "input_format": "Text document or PDF",
        "output_format": "Category probabilities and classification"
    },
    {
        "model_id": "llama2-code-assistant-v7.0.2",
        "name": "Llama-2 7B Code Assistant",
        "model_type": "llm",
        "version": "7.0.2",
        "description": "Fine-tuned Llama-2 7B model for code generation and review. Trained on 1M code examples across Python, JavaScript, and TypeScript.",
        "capabilities": ["code_generation", "code_review", "programming_assistant"],
        "input_format": "Code prompt or code snippet",
        "output_format": "Generated code or review comments"
    },
    {
        "model_id": "claude3-summarization-v3.1.0",
        "name": "Claude-3 Opus Summarization",
        "model_type": "llm",
        "version": "3.1.0",
        "description": "Claude-3 Opus fine-tuned for long-form document summarization. Processes research papers, reports, and technical documentation.",
        "capabilities": ["summarization", "document_processing", "text_analysis"],
        "input_format": "Long text document or PDF",
        "output_format": "Summarized text"
    },
    {
        "model_id": "gpt35-sentiment-v3.5.2",
        "name": "GPT-3.5 Turbo Sentiment Analysis",
        "model_type": "nlp",
        "version": "3.5.2",
        "description": "GPT-3.5 Turbo fine-tuned for multi-language sentiment analysis. Analyzes customer reviews, social media posts, and feedback across 20+ languages.",
        "capabilities": ["sentiment_analysis", "multilingual", "text_analysis"],
        "input_format": "Text in any supported language",
        "output_format": "Sentiment score and category (positive/negative/neutral)"
    },
    {
        "model_id": "mistral7b-instruction-v7.0.1",
        "name": "Mistral-7B Instruction Following",
        "model_type": "llm",
        "version": "7.0.1",
        "description": "Mistral-7B model fine-tuned for instruction following and task completion. Optimized for enterprise workflow automation.",
        "capabilities": ["instruction_following", "task_automation", "workflow"],
        "input_format": "Instruction text or structured task",
        "output_format": "Task completion result or response"
    },
    {
        "model_id": "t5-transformer-v1.1.0",
        "name": "T5 Text-to-Text Transformer",
        "model_type": "nlp",
        "version": "1.1.0",
        "description": "T5 model for text-to-text transformations including translation, summarization, and question answering. Supports 100+ languages.",
        "capabilities": ["translation", "summarization", "qa", "multilingual"],
        "input_format": "Text with task prefix (translate, summarize, etc.)",
        "output_format": "Transformed text"
    },
    {
        "model_id": "roberta-ner-v1.3.0",
        "name": "RoBERTa Named Entity Recognition",
        "model_type": "nlp",
        "version": "1.3.0",
        "description": "RoBERTa model fine-tuned for named entity recognition in financial documents. Extracts companies, dates, amounts, and legal entities.",
        "capabilities": ["ner", "entity_extraction", "financial_analysis"],
        "input_format": "Text document or financial statement",
        "output_format": "Extracted entities with labels and positions"
    },
    {
        "model_id": "stable-diffusion-v2.1.0",
        "name": "Stable Diffusion Image Generation",
        "model_type": "computer_vision",
        "version": "2.1.0",
        "description": "Stable Diffusion v2.1 model for text-to-image generation. Used for marketing content creation and design automation.",
        "capabilities": ["image_generation", "text_to_image", "creative"],
        "input_format": "Text prompt describing desired image",
        "output_format": "Generated image (PNG/JPEG)"
    },
    {
        "model_id": "whisper-large-v2",
        "name": "Whisper Large-v2 Speech Recognition",
        "model_type": "nlp",
        "version": "large-v2",
        "description": "OpenAI Whisper model for multilingual speech-to-text transcription. Supports 99 languages with high accuracy.",
        "capabilities": ["speech_to_text", "transcription", "multilingual"],
        "input_format": "Audio file (WAV, MP3, etc.) or audio stream",
        "output_format": "Transcribed text with timestamps"
    }
]

async def register_model(session: aiohttp.ClientSession, base_url: str, model: dict):
    """Register a single model via API"""
    url = f"{base_url}/api/v1/ai-governance/ai-models/register"
    
    try:
        async with session.post(url, json=model) as response:
            if response.status == 200:
                data = await response.json()
                return True, data
            else:
                error_text = await response.text()
                return False, f"HTTP {response.status}: {error_text}"
    except Exception as e:
        return False, str(e)

async def seed_models():
    """Register all models via API"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print(f"Registering models via API at {base_url}...")
    print(f"Total models to register: {len(REAL_MODELS)}\n")
    
    registered_count = 0
    failed_count = 0
    
    async with aiohttp.ClientSession() as session:
        for model in REAL_MODELS:
            success, result = await register_model(session, base_url, model)
            
            if success:
                print(f"  ✓ Registered: {model['name']} ({model['model_type']})")
                registered_count += 1
            else:
                print(f"  ✗ Failed: {model['name']} - {result}")
                failed_count += 1
    
    print(f"\nRegistration complete!")
    print(f"  Registered: {registered_count} models")
    print(f"  Failed: {failed_count} models")
    print(f"  Total: {len(REAL_MODELS)} models")
    
    return registered_count > 0

if __name__ == "__main__":
    import os
    asyncio.run(seed_models())

