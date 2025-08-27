#!/usr/bin/env python3
"""
Enhanced Dataset & Model Downloader for FairMind Testing
Downloads both traditional datasets and LLM models for comprehensive testing
"""

import os
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Any

class EnhancedDownloader:
    def __init__(self, base_dir="test_models"):
        self.base_dir = Path(base_dir)
        
    def check_kaggle_credentials(self):
        """Check if Kaggle credentials are set up"""
        kaggle_file = Path.home() / ".kaggle" / "kaggle.json"
        if not kaggle_file.exists():
            print("❌ Kaggle credentials not found")
            print("Please run: python setup_kaggle_credentials.py")
            return False
        
        # Test Kaggle API
        try:
            result = subprocess.run(['kaggle', 'datasets', 'list', '--limit', '1'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Kaggle API working")
                return True
            else:
                print("❌ Kaggle API test failed")
                return False
        except Exception as e:
            print(f"❌ Error testing Kaggle API: {e}")
            return False
    
    def download_kaggle_dataset(self, dataset_name: str, kaggle_url: str, target_dir: str):
        """Download a dataset from Kaggle"""
        target_path = self.base_dir / target_dir
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"📥 Downloading {dataset_name}...")
        
        try:
            os.chdir(target_path)
            cmd = ["kaggle", "datasets", "download", "-d", kaggle_url]
            subprocess.run(cmd, check=True)
            
            # Unzip and clean up
            zip_files = list(Path(".").glob("*.zip"))
            if zip_files:
                subprocess.run(["unzip", "-o", str(zip_files[0])], check=True)
                zip_files[0].unlink()
            
            print(f"✅ {dataset_name} downloaded successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to download {dataset_name}: {e}")
            return False
        finally:
            os.chdir(Path.cwd())
    
    def download_huggingface_model(self, model_name: str, model_type: str, target_dir: str):
        """Download a model from Hugging Face"""
        target_path = self.base_dir / target_dir
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"🤗 Downloading {model_name} from Hugging Face...")
        
        try:
            # Use huggingface_hub to download
            from huggingface_hub import snapshot_download
            
            model_path = snapshot_download(
                repo_id=model_name,
                local_dir=target_path,
                local_dir_use_symlinks=False
            )
            
            # Create metadata
            metadata = {
                "model_name": model_name,
                "model_type": model_type,
                "source": "huggingface",
                "downloaded_at": str(Path.cwd()),
                "local_path": str(model_path)
            }
            
            with open(target_path / "model_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ {model_name} downloaded successfully")
            return True
            
        except ImportError:
            print("❌ huggingface_hub not installed. Installing...")
            subprocess.run(["uv", "pip", "install", "huggingface_hub"], check=True)
            return self.download_huggingface_model(model_name, model_type, target_dir)
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}")
            return False
    
    def download_torchvision_model(self, model_name: str, target_dir: str):
        """Download a PyTorch model"""
        target_path = self.base_dir / target_dir
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"🔥 Downloading {model_name} from torchvision...")
        
        try:
            import torch
            import torchvision.models as models
            
            # Get the model
            if model_name == "resnet50":
                model = models.resnet50(pretrained=True)
            elif model_name == "resnet18":
                model = models.resnet18(pretrained=True)
            elif model_name == "vgg16":
                model = models.vgg16(pretrained=True)
            elif model_name == "alexnet":
                model = models.alexnet(pretrained=True)
            else:
                print(f"❌ Unknown model: {model_name}")
                return False
            
            # Save the model
            torch.save(model.state_dict(), target_path / f"{model_name}.pth")
            
            # Create metadata
            metadata = {
                "model_name": model_name,
                "model_type": "image_classification",
                "source": "torchvision",
                "framework": "pytorch",
                "downloaded_at": str(Path.cwd())
            }
            
            with open(target_path / "model_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ {model_name} downloaded successfully")
            return True
            
        except ImportError:
            print("❌ torchvision not installed. Installing...")
            subprocess.run(["uv", "pip", "install", "torch", "torchvision"], check=True)
            return self.download_torchvision_model(model_name, target_dir)
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}")
            return False
    
    def download_audio_model(self, model_name: str, target_dir: str):
        """Download an audio model"""
        target_path = self.base_dir / target_dir
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"🎵 Downloading {model_name} audio model...")
        
        try:
            # For now, we'll use a simple approach
            # In production, you'd use transformers for Whisper or similar
            metadata = {
                "model_name": model_name,
                "model_type": "audio_speech",
                "source": "synthetic",
                "note": "Placeholder for actual audio model download",
                "downloaded_at": str(Path.cwd())
            }
            
            with open(target_path / "model_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ {model_name} metadata created (placeholder)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup {model_name}: {e}")
            return False
    
    def download_all_datasets_and_models(self):
        """Download all datasets and models"""
        print("🚀 Enhanced Dataset & Model Downloader")
        print("=" * 50)
        
        # Check Kaggle credentials
        if not self.check_kaggle_credentials():
            print("\n⚠️  Skipping Kaggle datasets. Please set up credentials first.")
            print("Continuing with model downloads...")
        
        results = {
            "datasets": {},
            "models": {}
        }
        
        # Traditional ML Datasets (Kaggle)
        if self.check_kaggle_credentials():
            kaggle_datasets = {
                "credit_card_fraud": {
                    "url": "mlg-ulb/creditcardfraud",
                    "dir": "traditional_ml/credit_risk"
                },
                "diabetes_prediction": {
                    "url": "uciml/diabetes-database", 
                    "dir": "traditional_ml/healthcare"
                },
                "hr_analytics": {
                    "url": "vjchoudhary7/hr-analytics-case-study",
                    "dir": "traditional_ml/hiring"
                }
            }
            
            for name, config in kaggle_datasets.items():
                results["datasets"][name] = self.download_kaggle_dataset(
                    name, config["url"], config["dir"]
                )
        
        # LLM Models (Hugging Face)
        llm_models = {
            "gpt2": {
                "name": "gpt2",
                "type": "text_generation",
                "dir": "llm_models/text_generation"
            },
            "distilbert": {
                "name": "distilbert-base-uncased",
                "type": "text_classification", 
                "dir": "llm_models/text_classification"
            },
            "bert": {
                "name": "bert-base-uncased",
                "type": "text_understanding",
                "dir": "llm_models/text_understanding"
            }
        }
        
        for name, config in llm_models.items():
            results["models"][name] = self.download_huggingface_model(
                config["name"], config["type"], config["dir"]
            )
        
        # Image Classification Models (Torchvision)
        image_models = {
            "resnet50": "llm_models/image_classification/resnet50",
            "resnet18": "llm_models/image_classification/resnet18", 
            "vgg16": "llm_models/image_classification/vgg16"
        }
        
        for name, target_dir in image_models.items():
            results["models"][name] = self.download_torchvision_model(name, target_dir)
        
        # Audio Models
        audio_models = {
            "whisper_base": "llm_models/audio_speech/whisper_base",
            "wav2vec2": "llm_models/audio_speech/wav2vec2"
        }
        
        for name, target_dir in audio_models.items():
            results["models"][name] = self.download_audio_model(name, target_dir)
        
        # Print summary
        self.print_download_summary(results)
        
        return results
    
    def print_download_summary(self, results):
        """Print download summary"""
        print("\n📊 Download Summary")
        print("=" * 30)
        
        # Datasets
        if results["datasets"]:
            print("\n📁 Datasets:")
            for name, success in results["datasets"].items():
                status = "✅" if success else "❌"
                print(f"  {status} {name}")
        
        # Models
        if results["models"]:
            print("\n🤖 Models:")
            for name, success in results["models"].items():
                status = "✅" if success else "❌"
                print(f"  {status} {name}")
        
        # Calculate success rates
        dataset_success = sum(results["datasets"].values()) if results["datasets"] else 0
        dataset_total = len(results["datasets"]) if results["datasets"] else 0
        model_success = sum(results["models"].values()) if results["models"] else 0
        model_total = len(results["models"]) if results["models"] else 0
        
        print(f"\n📈 Success Rates:")
        if dataset_total > 0:
            print(f"  Datasets: {dataset_success}/{dataset_total} ({dataset_success/dataset_total*100:.1f}%)")
        if model_total > 0:
            print(f"  Models: {model_success}/{model_total} ({model_success/model_total*100:.1f}%)")
        
        total_success = dataset_success + model_success
        total_items = dataset_total + model_total
        
        if total_items > 0:
            print(f"  Overall: {total_success}/{total_items} ({total_success/total_items*100:.1f}%)")
        
        if total_success == total_items:
            print("\n🎉 All downloads completed successfully!")
        else:
            print("\n⚠️  Some downloads failed. Check the errors above.")

def main():
    """Main function"""
    downloader = EnhancedDownloader()
    downloader.download_all_datasets_and_models()

if __name__ == "__main__":
    main()
