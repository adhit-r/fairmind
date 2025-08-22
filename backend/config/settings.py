"""
Configuration settings for the Fairmind backend
"""

import os
from pathlib import Path
from typing import List

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# API Settings
API_TITLE = "Fairmind ML Service"
API_DESCRIPTION = "AI Governance and Bias Detection ML Service"
API_VERSION = "1.0.0"

# CORS Settings - FIXED: Use environment variables
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# File Upload Settings
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
DATASET_DIR = Path(os.getenv("DATASET_DIR", BASE_DIR / "datasets"))
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = [".pkl", ".joblib", ".h5", ".onnx", ".pb"]

# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fairmind.db")

# Supabase Settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Security Settings - FIXED: Use environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Logging Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Model Settings
DEFAULT_MODEL_TYPE = "classification"
SUPPORTED_MODEL_TYPES = ["classification", "regression", "clustering", "nlp"]

# Bias Detection Settings
DEFAULT_BIAS_METRICS = [
    "statistical_parity",
    "equal_opportunity", 
    "demographic_parity",
    "equalized_odds"
]

# Security Testing Settings
OWASP_CATEGORIES = [
    "prompt_injection",
    "insecure_output_handling",
    "training_data_poisoning",
    "model_denial_of_service",
    "supply_chain_vulnerabilities",
    "sensitive_information_disclosure",
    "insecure_plugin_design",
    "excessive_agency",
    "overreliance",
    "model_theft"
]

# Provenance Settings
PROVENANCE_KEY_PATH = BASE_DIR / "keys" / "provenance_key.pem"
PROVENANCE_PUBLIC_KEY_PATH = BASE_DIR / "keys" / "provenance_public_key.pem"

# Email Settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Monitoring Settings
ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
MONITORING_INTERVAL = int(os.getenv("MONITORING_INTERVAL", "300"))  # 5 minutes

# Cache Settings
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
REDIS_URL = os.getenv("REDIS_URL")

# Development Settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
RELOAD = os.getenv("RELOAD", "false").lower() == "true"

