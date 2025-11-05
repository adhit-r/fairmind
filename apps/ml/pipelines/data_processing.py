"""
Data Processing Pipeline for Fairmind ML Engineering
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import mlflow
from mlflow_config import get_experiment, log_model_metrics

def load_data(data_path):
    """Load data from various formats"""
    data_path = Path(data_path)
    
    if data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    elif data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.json':
        return pd.read_json(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def validate_data(df):
    """Validate data quality and structure"""
    validation_results = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "duplicate_rows": df.duplicated().sum(),
        "memory_usage": df.memory_usage(deep=True).sum()
    }
    
    # Check for common data quality issues
    quality_issues = []
    
    if validation_results["duplicate_rows"] > 0:
        quality_issues.append(f"Found {validation_results['duplicate_rows']} duplicate rows")
    
    missing_percentage = (df.isnull().sum() / len(df) * 100).max()
    if missing_percentage > 50:
        quality_issues.append(f"Some columns have >50% missing values")
    
    validation_results["quality_issues"] = quality_issues
    validation_results["quality_score"] = max(0, 100 - len(quality_issues) * 10 - missing_percentage)
    
    return validation_results

def preprocess_data(df, target_column=None, protected_attributes=None):
    """Preprocess data for ML pipeline"""
    processed_df = df.copy()
    
    # Handle missing values
    numeric_columns = processed_df.select_dtypes(include=[np.number]).columns
    categorical_columns = processed_df.select_dtypes(include=['object']).columns
    
    # Fill missing values
    for col in numeric_columns:
        processed_df[col].fillna(processed_df[col].median(), inplace=True)
    
    for col in categorical_columns:
        processed_df[col].fillna(processed_df[col].mode()[0] if not processed_df[col].mode().empty else 'Unknown', inplace=True)
    
    # Encode categorical variables
    for col in categorical_columns:
        if col != target_column and col not in (protected_attributes or []):
            processed_df[col] = pd.Categorical(processed_df[col]).codes
    
    return processed_df

def main():
    """Main data processing pipeline"""
    # Set up MLflow experiment
    experiment = get_experiment()
    if experiment:
        mlflow.set_experiment(experiment.name)
    
    with mlflow.start_run(run_name="data_processing"):
        # Load data
        raw_data_path = Path("apps/ml/data/raw")
        processed_data_path = Path("apps/ml/data/processed")
        features_data_path = Path("apps/ml/data/features")
        
        # Create output directories
        processed_data_path.mkdir(parents=True, exist_ok=True)
        features_data_path.mkdir(parents=True, exist_ok=True)
        
        # Process each dataset
        data_files = list(raw_data_path.glob("*.csv")) + list(raw_data_path.glob("*.parquet"))
        
        for data_file in data_files:
            print(f"Processing {data_file.name}")
            
            # Load and validate data
            df = load_data(data_file)
            validation_results = validate_data(df)
            
            # Log validation metrics
            log_model_metrics({
                "data_quality_score": validation_results["quality_score"],
                "total_rows": validation_results["total_rows"],
                "total_columns": validation_results["total_columns"],
                "duplicate_rows": validation_results["duplicate_rows"]
            })
            
            # Preprocess data
            processed_df = preprocess_data(df)
            
            # Save processed data
            output_file = processed_data_path / f"processed_{data_file.stem}.parquet"
            processed_df.to_parquet(output_file, index=False)
            
            # Save features
            features_file = features_data_path / f"features_{data_file.stem}.parquet"
            processed_df.to_parquet(features_file, index=False)
            
            print(f"Processed {data_file.name} -> {output_file}")
        
        # Save data quality metrics
        metrics_path = Path("apps/ml/metrics")
        metrics_path.mkdir(parents=True, exist_ok=True)
        
        with open(metrics_path / "data_quality.json", "w") as f:
            json.dump(validation_results, f, indent=2)
        
        print("Data processing pipeline completed successfully!")

if __name__ == "__main__":
    main()
