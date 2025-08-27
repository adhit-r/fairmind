#!/usr/bin/env python3
"""
Kaggle Dataset Downloader for FairMind Testing
Downloads datasets for comprehensive testing of FairMind features
"""

import os
import subprocess
import json
from pathlib import Path

# Test datasets configuration
DATASETS = {
    "credit_card_fraud": {
        "kaggle_url": "mlg-ulb/creditcardfraud",
        "description": "Credit card fraud detection dataset",
        "target_dir": "test_models/traditional_ml/credit_risk",
        "sensitive_features": ["gender", "age", "income_level"],
        "model_type": "classification"
    },
    "diabetes_prediction": {
        "kaggle_url": "uciml/diabetes-database",
        "description": "Diabetes prediction dataset",
        "target_dir": "test_models/traditional_ml/healthcare",
        "sensitive_features": ["age", "gender", "race", "socioeconomic_status"],
        "model_type": "classification"
    },
    "hr_analytics": {
        "kaggle_url": "vjchoudhary7/hr-analytics-case-study",
        "description": "HR analytics dataset for hiring bias testing",
        "target_dir": "test_models/traditional_ml/hiring",
        "sensitive_features": ["gender", "age", "education", "experience"],
        "model_type": "classification"
    },
    "news_articles": {
        "kaggle_url": "snapcrack/all-the-news",
        "description": "News articles for text generation bias testing",
        "target_dir": "test_models/llm_models/text_generation",
        "sensitive_features": ["topic", "source", "author"],
        "model_type": "text_generation"
    },
    "celeba": {
        "kaggle_url": "jessicali9530/celeba-dataset",
        "description": "CelebA dataset for image classification bias testing",
        "target_dir": "test_models/llm_models/image_classification",
        "sensitive_features": ["gender", "age", "ethnicity"],
        "model_type": "image_classification"
    },
    "fairface": {
        "kaggle_url": "datasmash/fair-face",
        "description": "FairFace dataset for demographic bias testing",
        "target_dir": "test_models/llm_models/image_classification",
        "sensitive_features": ["age", "gender", "race"],
        "model_type": "image_classification"
    }
}

def check_kaggle_installed():
    """Check if Kaggle CLI is installed"""
    try:
        subprocess.run(["kaggle", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_kaggle():
    """Install Kaggle CLI using UV"""
    print("Installing Kaggle CLI using UV...")
    try:
        subprocess.run(["uv", "pip", "install", "kaggle"], check=True)
        print("✅ Kaggle CLI installed successfully with UV")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Kaggle CLI with UV: {e}")
        return False

def setup_kaggle_credentials():
    """Set up Kaggle API credentials"""
    print("\n🔑 Setting up Kaggle API credentials...")
    print("Please follow these steps:")
    print("1. Go to https://www.kaggle.com/settings/account")
    print("2. Scroll down to 'API' section")
    print("3. Click 'Create New API Token'")
    print("4. Download the kaggle.json file")
    print("5. Place it in ~/.kaggle/kaggle.json")
    
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_file = kaggle_dir / "kaggle.json"
    
    if kaggle_file.exists():
        print("✅ Kaggle credentials found")
        return True
    else:
        print("❌ Kaggle credentials not found")
        print(f"Please place kaggle.json in {kaggle_dir}")
        return False

def download_dataset(dataset_name, dataset_config):
    """Download a specific dataset"""
    target_dir = Path(dataset_config["target_dir"])
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📥 Downloading {dataset_name}...")
    print(f"   Description: {dataset_config['description']}")
    print(f"   Target: {target_dir}")
    
    try:
        # Change to target directory
        os.chdir(target_dir)
        
        # Download dataset
        cmd = ["kaggle", "datasets", "download", "-d", dataset_config["kaggle_url"]]
        subprocess.run(cmd, check=True)
        
        # Unzip the downloaded file
        zip_file = list(Path(".").glob("*.zip"))[0]
        subprocess.run(["unzip", "-o", str(zip_file)], check=True)
        
        # Remove zip file
        zip_file.unlink()
        
        # Create metadata file
        metadata = {
            "dataset_name": dataset_name,
            "kaggle_url": dataset_config["kaggle_url"],
            "description": dataset_config["description"],
            "sensitive_features": dataset_config["sensitive_features"],
            "model_type": dataset_config["model_type"],
            "downloaded_at": str(Path.cwd()),
            "files": [f.name for f in Path(".").iterdir() if f.is_file()]
        }
        
        with open("metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Successfully downloaded {dataset_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download {dataset_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error processing {dataset_name}: {e}")
        return False
    finally:
        # Return to original directory
        os.chdir(Path.cwd())

def main():
    """Main function to set up and download all datasets"""
    print("🚀 FairMind Testing Dataset Setup")
    print("=" * 50)
    
    # Check if Kaggle is installed
    if not check_kaggle_installed():
        if not install_kaggle():
            print("❌ Cannot proceed without Kaggle CLI")
            return
    
    # Check credentials
    if not setup_kaggle_credentials():
        print("❌ Cannot proceed without Kaggle credentials")
        return
    
    # Download all datasets
    success_count = 0
    total_count = len(DATASETS)
    
    for dataset_name, dataset_config in DATASETS.items():
        if download_dataset(dataset_name, dataset_config):
            success_count += 1
    
    print(f"\n📊 Download Summary:")
    print(f"   Successfully downloaded: {success_count}/{total_count} datasets")
    
    if success_count == total_count:
        print("🎉 All datasets downloaded successfully!")
        print("\nNext steps:")
        print("1. Review the downloaded datasets")
        print("2. Run model training scripts")
        print("3. Upload models to FairMind for testing")
    else:
        print("⚠️  Some datasets failed to download. Please check the errors above.")

if __name__ == "__main__":
    main()
