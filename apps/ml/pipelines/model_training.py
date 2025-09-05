"""
Model Training Pipeline for Fairmind ML Engineering
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import joblib
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from mlflow_config import get_experiment, log_model_metrics

def load_features(features_path):
    """Load processed features"""
    features_path = Path(features_path)
    feature_files = list(features_path.glob("*.parquet"))
    
    if not feature_files:
        raise ValueError("No feature files found")
    
    # Load the first feature file (can be extended to handle multiple)
    return pd.read_parquet(feature_files[0])

def prepare_training_data(df, target_column=None):
    """Prepare data for training"""
    if target_column is None:
        # Assume last column is target
        target_column = df.columns[-1]
    
    X = df.drop(columns=[target_column])
    y = df[target_column]
    
    return X, y, target_column

def train_model(X, y, model_type="classification"):
    """Train ML model"""
    if model_type == "classification":
        # Try multiple classifiers
        models = {
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
            "logistic_regression": LogisticRegression(random_state=42, max_iter=1000)
        }
    else:
        # Try multiple regressors
        models = {
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "linear_regression": LinearRegression()
        }
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    best_model = None
    best_score = -np.inf
    best_model_name = None
    
    for model_name, model in models.items():
        # Train model
        model.fit(X_train, y_train)
        
        # Evaluate model
        if model_type == "classification":
            y_pred = model.predict(X_test)
            score = accuracy_score(y_test, y_pred)
        else:
            y_pred = model.predict(X_test)
            score = r2_score(y_test, y_pred)
        
        # Log model metrics
        mlflow.sklearn.log_model(model, f"model_{model_name}")
        
        if model_type == "classification":
            mlflow.log_metrics({
                f"{model_name}_accuracy": accuracy_score(y_test, y_pred),
                f"{model_name}_precision": precision_score(y_test, y_pred, average='weighted'),
                f"{model_name}_recall": recall_score(y_test, y_pred, average='weighted'),
                f"{model_name}_f1": f1_score(y_test, y_pred, average='weighted')
            })
        else:
            mlflow.log_metrics({
                f"{model_name}_r2": r2_score(y_test, y_pred),
                f"{model_name}_mse": mean_squared_error(y_test, y_pred),
                f"{model_name}_rmse": np.sqrt(mean_squared_error(y_test, y_pred))
            })
        
        if score > best_score:
            best_score = score
            best_model = model
            best_model_name = model_name
    
    return best_model, best_model_name, X_test, y_test, best_score

def save_model(model, model_name, model_type):
    """Save trained model"""
    models_path = Path("apps/ml/models")
    models_path.mkdir(parents=True, exist_ok=True)
    
    model_file = models_path / f"{model_name}_{model_type}.joblib"
    joblib.dump(model, model_file)
    
    return model_file

def main():
    """Main model training pipeline"""
    # Set up MLflow experiment
    experiment = get_experiment()
    if experiment:
        mlflow.set_experiment(experiment.name)
    
    with mlflow.start_run(run_name="model_training"):
        # Load features
        features_path = Path("apps/ml/data/features")
        df = load_features(features_path)
        
        print(f"Loaded dataset with shape: {df.shape}")
        
        # Determine model type based on target variable
        target_column = df.columns[-1]
        target_values = df[target_column].unique()
        
        if len(target_values) <= 10 and df[target_column].dtype == 'object':
            model_type = "classification"
        else:
            model_type = "regression"
        
        print(f"Training {model_type} model for target: {target_column}")
        
        # Prepare training data
        X, y, target_column = prepare_training_data(df, target_column)
        
        # Train model
        model, model_name, X_test, y_test, score = train_model(X, y, model_type)
        
        # Save model
        model_file = save_model(model, model_name, model_type)
        
        # Log model parameters
        mlflow.log_params({
            "model_type": model_type,
            "model_name": model_name,
            "target_column": target_column,
            "n_features": X.shape[1],
            "n_samples": X.shape[0]
        })
        
        # Log model performance
        log_model_metrics({
            "best_model_score": score,
            "best_model_name": model_name
        })
        
        # Save training results
        results = {
            "model_type": model_type,
            "model_name": model_name,
            "target_column": target_column,
            "score": score,
            "n_features": X.shape[1],
            "n_samples": X.shape[0],
            "model_file": str(model_file)
        }
        
        metrics_path = Path("apps/ml/metrics")
        metrics_path.mkdir(parents=True, exist_ok=True)
        
        with open(metrics_path / "model_performance.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"Model training completed! Best model: {model_name} with score: {score:.4f}")
        print(f"Model saved to: {model_file}")

if __name__ == "__main__":
    main()
