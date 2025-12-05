"""
Modern Bias Detection Service
Uses current explainability techniques and modern AI fairness tools
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
import warnings
import logging
from datetime import datetime
import json
from itertools import combinations

warnings.filterwarnings('ignore')

# Modern explainability and fairness libraries
try:
    import fairlearn
    from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference
    from fairlearn.postprocessing import ThresholdOptimizer
    FAIRLEARN_AVAILABLE = True
except ImportError:
    FAIRLEARN_AVAILABLE = False
    print("Fairlearn not available - using fallback bias detection")

# Modern explainability - InterpretML (Microsoft)
try:
    import interpret
    from interpret.blackbox import LimeTabular
    from interpret.glassbox import ExplainableBoostingClassifier
    INTERPRET_AVAILABLE = True
except ImportError:
    INTERPRET_AVAILABLE = False
    print("InterpretML not available - using fallback explainability")

# Modern explainability - Alibi (Seldon)
try:
    import alibi
    from alibi.explainers import AnchorTabular, IntegratedGradients
    ALIBI_AVAILABLE = True
except ImportError:
    ALIBI_AVAILABLE = False
    print("Alibi not available - using fallback explainability")

# Modern explainability - ELI5
try:
    import eli5
    from eli5.lime import TextExplainer
    ELI5_AVAILABLE = True
except ImportError:
    ELI5_AVAILABLE = False
    print("ELI5 not available - using fallback explanations")

# Modern fairness - AIF360
try:
    from aif360.datasets import StandardDataset
    from aif360.metrics import ClassificationMetric
    from aif360.algorithms.preprocessing import Reweighing
    AIF360_AVAILABLE = True
except ImportError:
    AIF360_AVAILABLE = False
    print("AI Fairness 360 not available - using fallback fairness metrics")

# Modern ML libraries
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False

logger = logging.getLogger(__name__)

class ModernBiasDetectionService:
    """
    Modern bias detection service using current explainability techniques:
    - InterpretML (Microsoft's modern explainability library)
    - Alibi (Seldon's production-ready explainability)
    - ELI5 (modern LIME alternative)
    - Fairlearn (Microsoft's fairness library)
    - AIF360 (IBM's fairness library)
    """
    
    def __init__(self):
        self.supported_datasets = {
            'adult': self._load_adult_dataset,
            'compas': self._load_compas_dataset,
            'german': self._load_german_dataset,
            'diabetes': self._load_diabetes_dataset,
            'titanic': self._load_titanic_dataset,
            'credit': self._load_credit_dataset
        }
        self.explainer_cache = {}
        
    def _load_adult_dataset(self) -> pd.DataFrame:
        """Load Adult Census Income dataset or generate synthetic if unavailable."""
        try:
            from sklearn.datasets import fetch_openml
            adult = fetch_openml(name='adult', version=2, as_frame=True)
            df = adult.frame
            df['income'] = (df['income'] == '>50K').astype(int)
            return df
        except Exception as e:
            print(f"Failed to load Adult dataset from OpenML: {e}. Generating synthetic data.")
            return self._generate_synthetic_adult_data()
    
    def _generate_synthetic_adult_data(self) -> pd.DataFrame:
        """Generate synthetic Adult Census data as a fallback."""
        np.random.seed(42)
        n_samples = 1000
        age = np.clip(np.random.normal(38, 13, n_samples), 17, 90)
        workclass = np.random.choice(['Private', 'Self-emp-not-inc', 'Self-emp-inc', 'Federal-gov', 'Local-gov', 'State-gov', 'Without-pay', 'Never-worked'], n_samples, p=[0.7, 0.1, 0.05, 0.05, 0.05, 0.03, 0.01, 0.01])
        education = np.random.choice(['Bachelors', 'Some-college', 'HS-grad', 'Masters', 'Doctorate'], n_samples)
        race = np.random.choice(['White', 'Black', 'Asian-Pac-Islander', 'Other'], n_samples, p=[0.85, 0.1, 0.03, 0.02])
        sex = np.random.choice(['Male', 'Female'], n_samples, p=[0.55, 0.45])
        income = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            base_prob = 0.25 + (0.1 if race[i] == 'White' else 0) + (0.15 if sex[i] == 'Male' else 0) + (0.2 if education[i] in ['Bachelors', 'Masters', 'Doctorate'] else 0) + (0.1 if age[i] > 30 else 0)
            income[i] = np.random.binomial(1, min(base_prob, 0.9))
        return pd.DataFrame({'age': age, 'workclass': workclass, 'education': education, 'race': race, 'sex': sex, 'income': income})

    def _load_compas_dataset(self) -> pd.DataFrame:
        """Load COMPAS dataset or generate synthetic if unavailable."""
        return self._generate_synthetic_compas_data()

    def _generate_synthetic_compas_data(self) -> pd.DataFrame:
        """Generate synthetic COMPAS data."""
        np.random.seed(42)
        n_samples = 1000
        age = np.clip(np.random.normal(35, 12, n_samples), 18, 75)
        race = np.random.choice(['Caucasian', 'African-American', 'Hispanic', 'Other'], n_samples, p=[0.5, 0.3, 0.15, 0.05])
        sex = np.random.choice(['Male', 'Female'], n_samples, p=[0.7, 0.3])
        recidivism = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            base_prob = 0.3 + (0.2 if race[i] == 'African-American' else 0) + (0.1 if sex[i] == 'Male' else 0) + (0.15 if age[i] < 25 else 0)
            recidivism[i] = np.random.binomial(1, min(base_prob, 0.8))
        return pd.DataFrame({'age': age, 'race': race, 'sex': sex, 'recidivism': recidivism})

    def _load_german_dataset(self) -> pd.DataFrame:
        """Load German Credit dataset or generate synthetic if unavailable."""
        return self._generate_synthetic_german_data()

    def _generate_synthetic_german_data(self) -> pd.DataFrame:
        """Generate synthetic German Credit data."""
        np.random.seed(42)
        n_samples = 1000
        age = np.clip(np.random.normal(35, 12, n_samples), 18, 75)
        credit_history = np.random.choice(['good', 'poor', 'none'], n_samples, p=[0.6, 0.3, 0.1])
        sex = np.random.choice(['male', 'female'], n_samples, p=[0.6, 0.4])
        credit_risk = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            base_prob = 0.3 + (0.3 if credit_history[i] == 'poor' else 0) + (0.1 if sex[i] == 'female' else 0) + (0.1 if age[i] < 25 else 0)
            credit_risk[i] = np.random.binomial(1, min(base_prob, 0.8))
        return pd.DataFrame({'age': age, 'credit_history': credit_history, 'sex': sex, 'credit_risk': credit_risk})

    def _load_diabetes_dataset(self) -> pd.DataFrame:
        """Load Diabetes dataset or generate synthetic if unavailable."""
        return self._generate_synthetic_diabetes_data()

    def _generate_synthetic_diabetes_data(self) -> pd.DataFrame:
        """Generate synthetic Diabetes data."""
        np.random.seed(42)
        n_samples = 1000
        age = np.clip(np.random.normal(50, 15, n_samples), 20, 80)
        bmi = np.clip(np.random.normal(30, 8, n_samples), 15, 50)
        glucose = np.clip(np.random.normal(120, 30, n_samples), 70, 200)
        sex = np.random.choice(['male', 'female'], n_samples, p=[0.5, 0.5])
        diabetes = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            base_prob = 0.2 + (0.2 if bmi[i] > 30 else 0) + (0.3 if glucose[i] > 140 else 0) + (0.1 if age[i] > 45 else 0) + (0.05 if sex[i] == 'male' else 0)
            diabetes[i] = np.random.binomial(1, min(base_prob, 0.8))
        return pd.DataFrame({'age': age, 'bmi': bmi, 'glucose': glucose, 'sex': sex, 'diabetes': diabetes})

    def _load_titanic_dataset(self) -> pd.DataFrame:
        """Load Titanic dataset or generate synthetic if unavailable."""
        return self._generate_synthetic_titanic_data()

    def _generate_synthetic_titanic_data(self) -> pd.DataFrame:
        """Generate synthetic Titanic data."""
        np.random.seed(42)
        n_samples = 1000
        age = np.clip(np.random.normal(30, 15, n_samples), 1, 80)
        sex = np.random.choice(['male', 'female'], n_samples, p=[0.6, 0.4])
        pclass = np.random.choice([1, 2, 3], n_samples, p=[0.2, 0.3, 0.5])
        survived = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            base_prob = 0.4 + (0.3 if sex[i] == 'female' else 0) + (0.2 if pclass[i] == 1 else 0) + (0.1 if age[i] < 18 else 0)
            survived[i] = np.random.binomial(1, min(base_prob, 0.9))
        return pd.DataFrame({'age': age, 'sex': sex, 'pclass': pclass, 'survived': survived})

    def _load_credit_dataset(self) -> pd.DataFrame:
        """Load Credit dataset or generate synthetic if unavailable."""
        return self._generate_synthetic_credit_data()

    def _generate_synthetic_credit_data(self) -> pd.DataFrame:
        """Generate synthetic Credit data."""
        np.random.seed(42)
        n_samples = 1000
        income = np.clip(np.random.lognormal(10, 0.5, n_samples), 10000, 200000)
        age = np.clip(np.random.normal(35, 12, n_samples), 18, 75)
        education = np.random.choice(['high_school', 'bachelor', 'master', 'phd'], n_samples, p=[0.4, 0.4, 0.15, 0.05])
        sex = np.random.choice(['male', 'female'], n_samples, p=[0.5, 0.5])
        default = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            base_prob = 0.2 + (0.3 if income[i] < 30000 else 0) + (0.1 if education[i] == 'high_school' else 0) + (0.1 if age[i] < 25 else 0) + (0.05 if sex[i] == 'male' else 0)
            default[i] = np.random.binomial(1, min(base_prob, 0.7))
        return pd.DataFrame({'income': income, 'age': age, 'education': education, 'sex': sex, 'default': default})

    def _load_dataset_by_name(self, dataset_name: str) -> pd.DataFrame:
        """Load dataset by name from the supported list."""
        if dataset_name in self.supported_datasets:
            return self.supported_datasets[dataset_name]()
        else:
            raise ValueError(f"Dataset {dataset_name} not supported")
    
    def analyze_dataset_modern(self, dataset_name: str, target_column: str, 
                             sensitive_columns: List[str]) -> Dict[str, Any]:
        """
        Modern comprehensive dataset bias analysis with current explainability techniques.
        """
        try:
            df = self._load_dataset_by_name(dataset_name)
            
            X = df.drop(columns=[target_column])
            y = df[target_column]
            
            categorical_columns = X.select_dtypes(include=['object', 'category']).columns
            X_encoded = X.copy()
            for col in categorical_columns:
                X_encoded[col] = LabelEncoder().fit_transform(X_encoded[col].astype(str))
            
            X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)
            
            models = {
                'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
                'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            }
            if XGB_AVAILABLE:
                models['xgboost'] = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')
            if LGB_AVAILABLE:
                models['lightgbm'] = lgb.LGBMClassifier(random_state=42)

            trained_models = {}
            for name, model in models.items():
                model.fit(X_train.drop(columns=sensitive_columns, errors='ignore'), y_train)
                trained_models[name] = model
            
            analysis_results = {
                'dataset_info': self._analyze_dataset_info(df, target_column, sensitive_columns),
                'statistical_bias': self._analyze_statistical_bias(df, target_column, sensitive_columns),
                'model_bias': {},
                'modern_explainability': {},
                'recommendations': []
            }
            
            for model_name, model in trained_models.items():
                X_test_model = X_test.drop(columns=sensitive_columns, errors='ignore')
                predictions = model.predict(X_test_model)
                probabilities = model.predict_proba(X_test_model)[:, 1] if hasattr(model, 'predict_proba') else None
                
                model_bias = self._analyze_model_bias_modern(
                    df.loc[X_test.index], X_test, y_test, predictions, probabilities, 
                    target_column, sensitive_columns
                )
                analysis_results['model_bias'][model_name] = model_bias
                
                modern_explainability = self._analyze_modern_explainability(
                    model, X_train.drop(columns=sensitive_columns, errors='ignore'), X_test_model, y_test,
                    target_column
                )
                analysis_results['modern_explainability'][model_name] = modern_explainability
            
            analysis_results['recommendations'] = self._generate_modern_recommendations(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in modern dataset analysis: {str(e)}")
            raise
    
    def _analyze_dataset_info(self, df: pd.DataFrame, target_column: str, 
                            sensitive_columns: List[str]) -> Dict[str, Any]:
        """Analyze basic dataset information."""
        return {
            'total_samples': len(df),
            'features': len(df.columns) - 1,
            'target_distribution': df[target_column].value_counts().to_dict(),
            'sensitive_attributes': {
                col: {'distribution': df[col].value_counts().to_dict()} for col in sensitive_columns
            }
        }
    
    def _analyze_statistical_bias(self, df: pd.DataFrame, target_column: str, 
                                sensitive_columns: List[str]) -> Dict[str, Any]:
        """Analyze statistical bias in the dataset."""
        bias_analysis = {}
        for col in sensitive_columns:
            if col in df.columns:
                positive_rates = df.groupby(col)[target_column].mean().to_dict()
                demographic_parity_diff = max(positive_rates.values()) - min(positive_rates.values())
                bias_analysis[col] = {
                    'positive_rates': positive_rates,
                    'demographic_parity_difference': demographic_parity_diff
                }
        return bias_analysis
    
    def _analyze_model_bias_modern(self, test_df_orig: pd.DataFrame, X_test: pd.DataFrame, 
                                 y_test: pd.Series, predictions: np.ndarray, 
                                 probabilities: Optional[np.ndarray], 
                                 target_column: str, sensitive_columns: List[str]) -> Dict[str, Any]:
        """Modern model bias analysis including intersectional."""
        model_bias = {
            'overall_performance': self._calculate_performance_metrics(y_test, predictions),
            'sensitive_attribute_analysis': {},
            'intersectional_analysis': {}
        }
        
        for col in sensitive_columns:
            if col in test_df_orig.columns:
                sensitive_features = test_df_orig[col]
                model_bias['sensitive_attribute_analysis'][col] = self._calculate_fairness_metrics_by_group(
                    y_test, predictions, sensitive_features
                )
        
        if len(sensitive_columns) > 1:
            model_bias['intersectional_analysis'] = self._analyze_intersectional_bias(
                y_test, predictions, test_df_orig, sensitive_columns
            )
            
        return model_bias

    def _analyze_intersectional_bias(self, y_true: pd.Series, y_pred: np.ndarray, 
                                   df: pd.DataFrame, sensitive_columns: List[str]) -> Dict[str, Any]:
        """Analyzes fairness metrics for intersections of sensitive attributes."""
        intersectional_results = {}
        for r in range(2, len(sensitive_columns) + 1):
            for combo in combinations(sensitive_columns, r):
                combo_name = "_&_".join(combo)
                intersectional_feature = df[list(combo)].apply(lambda x: '_'.join(x.astype(str)), axis=1)
                intersectional_results[combo_name] = self._calculate_fairness_metrics_by_group(
                    y_true, y_pred, intersectional_feature
                )
        return intersectional_results

    def _analyze_modern_explainability(self, model, X_train: pd.DataFrame, X_test: pd.DataFrame,
                                     y_test: pd.Series, target_column: str) -> Dict[str, Any]:
        """Analyze model explainability using modern techniques."""
        explainability_results = {'feature_importance': {}}
        
        # 1. InterpretML (Microsoft's modern explainability)
        if INTERPRET_AVAILABLE:
            try:
                explainability_results['interpretml_analysis'] = self._perform_interpretml_analysis(model, X_train, X_test)
                explainability_results['feature_importance']['interpretml'] = explainability_results['interpretml_analysis']['feature_importance']
            except Exception as e:
                logger.warning(f"InterpretML analysis failed: {e}")
        
        # 2. Alibi (Seldon's production-ready explainability)
        if ALIBI_AVAILABLE:
            try:
                explainability_results['alibi_analysis'] = self._perform_alibi_analysis(model, X_train, X_test)
            except Exception as e:
                logger.warning(f"Alibi analysis failed: {e}")
        
        # 3. ELI5 (modern LIME alternative)
        if ELI5_AVAILABLE:
            try:
                explainability_results['eli5_analysis'] = self._perform_eli5_analysis(model, X_train, X_test)
            except Exception as e:
                logger.warning(f"ELI5 analysis failed: {e}")
        
        # 4. Native model explainability
        if hasattr(model, 'feature_importances_') or hasattr(model, 'coef_'):
            explainability_results['feature_importance']['native'] = self._calculate_native_feature_importance(model, X_train.columns)
        
        return explainability_results
    
    def _perform_interpretml_analysis(self, model, X_train: pd.DataFrame, X_test: pd.DataFrame) -> Dict[str, Any]:
        """Perform InterpretML analysis - Microsoft's modern explainability library."""
        try:
            # Create InterpretML explainer
            lime_explainer = LimeTabular(
                model, 
                X_train, 
                feature_names=X_train.columns.tolist(),
                class_names=['0', '1']
            )
            
            # Global explanations
            global_explanation = lime_explainer.explain_global(X_test.iloc[:50])
            
            # Local explanations for a few instances
            local_explanations = []
            for i in range(min(3, len(X_test))):
                local_exp = lime_explainer.explain_local(X_test.iloc[i:i+1])
                local_explanations.append({
                    'instance_id': i,
                    'feature_weights': local_exp.data(0)['names'],
                    'prediction': model.predict([X_test.iloc[i]])[0] if hasattr(model, 'predict') else None
                })
            
            return {
                'global_explanation': {
                    'feature_importance': global_explanation.data(0)['names'][:10],
                    'explanation_type': 'InterpretML LimeTabular'
                },
                'local_explanations': local_explanations,
                'explainer_type': 'InterpretML',
                'feature_importance': global_explanation.data(0)['names'][:10]
            }
        except Exception as e:
            logger.warning(f"InterpretML analysis failed: {e}")
            return {
                'global_explanation': {'error': str(e)},
                'local_explanations': [],
                'explainer_type': 'InterpretML (Failed)',
                'feature_importance': []
            }
    
    def _perform_alibi_analysis(self, model, X_train: pd.DataFrame, X_test: pd.DataFrame) -> Dict[str, Any]:
        """Perform Alibi analysis - Seldon's production-ready explainability."""
        try:
            # Anchor explanations (rule-based)
            anchor_explainer = AnchorTabular(
                model.predict_proba if hasattr(model, 'predict_proba') else model.predict,
                X_train.columns.tolist(),
                X_train.values,
                categorical_names={}
            )
            anchor_explainer.fit(X_train.values)
            
            # Generate anchor explanations for a few instances
            anchor_explanations = []
            for i in range(min(3, len(X_test))):
                try:
                    explanation = anchor_explainer.explain(X_test.iloc[i].values)
                    anchor_explanations.append({
                        'instance_id': i,
                        'anchor': explanation.anchor,
                        'precision': explanation.precision,
                        'coverage': explanation.coverage
                    })
                except Exception as e:
                    logger.warning(f"Anchor explanation failed for instance {i}: {e}")
            
            return {
                'anchor_explanations': anchor_explanations,
                'explainer_type': 'Alibi AnchorTabular',
                'num_explanations': len(anchor_explanations)
            }
        except Exception as e:
            logger.warning(f"Alibi analysis failed: {e}")
            return {
                'anchor_explanations': [],
                'explainer_type': 'Alibi AnchorTabular (Failed)',
                'error': str(e)
            }
    
    def _perform_eli5_analysis(self, model, X_train: pd.DataFrame, X_test: pd.DataFrame) -> Dict[str, Any]:
        """Perform ELI5 analysis - modern LIME alternative."""
        try:
            # Global feature importance
            if hasattr(model, 'feature_importances_'):
                global_importance = eli5.explain_weights(model, feature_names=X_train.columns.tolist())
                global_features = global_importance.feature_importances.importances[:10]
            elif hasattr(model, 'coef_'):
                global_importance = eli5.explain_weights(model, feature_names=X_train.columns.tolist())
                global_features = global_importance.feature_importances.importances[:10]
            else:
                global_features = []
            
            # Local explanations
            local_explanations = []
            for i in range(min(3, len(X_test))):
                try:
                    local_exp = eli5.explain_prediction(
                        model, 
                        X_test.iloc[i], 
                        feature_names=X_train.columns.tolist()
                    )
                    local_explanations.append({
                        'instance_id': i,
                        'explanation': str(local_exp),
                        'prediction': model.predict([X_test.iloc[i]])[0] if hasattr(model, 'predict') else None
                    })
                except Exception as e:
                    logger.warning(f"ELI5 explanation failed for instance {i}: {e}")
            
            return {
                'global_importance': global_features,
                'local_explanations': local_explanations,
                'explainer_type': 'ELI5',
                'num_explanations': len(local_explanations)
            }
        except Exception as e:
            logger.warning(f"ELI5 analysis failed: {e}")
            return {
                'global_importance': [],
                'local_explanations': [],
                'explainer_type': 'ELI5 (Failed)',
                'error': str(e)
            }

    def _calculate_native_feature_importance(self, model, features: List[str]) -> Dict[str, float]:
        """Calculate feature importance using model's native attributes."""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_[0])
        else:
            return {}
        
        feature_importance = pd.DataFrame(
            {'feature': features, 'importance': importances}
        ).sort_values(by='importance', ascending=False).head(10)
        return feature_importance.set_index('feature')['importance'].to_dict()

    def _calculate_performance_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate standard performance metrics."""
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0)
        }
    
    def _calculate_fairness_metrics_by_group(self, y_true: pd.Series, y_pred: np.ndarray, 
                                           sensitive_features: pd.Series) -> Dict[str, Any]:
        """Calculate fairness and performance metrics for each group."""
        groups = sensitive_features.unique()
        metrics = {}
        for group in groups:
            mask = (sensitive_features == group)
            if mask.sum() > 0:
                metrics[str(group)] = {
                    'performance': self._calculate_performance_metrics(y_true[mask], y_pred[mask]),
                    'sample_size': int(mask.sum()),
                    'selection_rate': y_pred[mask].mean()
                }
        
        if FAIRLEARN_AVAILABLE:
            metrics['demographic_parity_difference'] = demographic_parity_difference(y_true, y_pred, sensitive_features=sensitive_features)
            metrics['equalized_odds_difference'] = equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive_features)
            
        return metrics

    def _generate_modern_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on the modern analysis."""
        recommendations = []
        
        # Dataset bias recommendations
        for attr, metrics in analysis_results.get('statistical_bias', {}).items():
            if metrics.get('demographic_parity_difference', 0) > 0.1:
                recommendations.append(f"High statistical bias detected in '{attr}'. Consider pre-processing techniques like re-sampling or re-weighing (e.g., AIF360's Reweighing).")

        # Model bias recommendations
        for model_name, bias_data in analysis_results.get('model_bias', {}).items():
            for attr, metrics in bias_data.get('sensitive_attribute_analysis', {}).items():
                if metrics.get('demographic_parity_difference', 0) > 0.15:
                    recommendations.append(f"[{model_name}] exhibits high demographic parity difference for '{attr}'. Consider in-processing fairness constraints or post-processing methods like ThresholdOptimizer.")
                if metrics.get('equalized_odds_difference', 0) > 0.15:
                    recommendations.append(f"[{model_name}] exhibits high equalized odds difference for '{attr}', suggesting unequal error rates. This is critical in high-stakes decisions. Explore post-processing mitigations.")

        recommendations.append("Review the modern explainability results using InterpretML, Alibi, and ELI5. If sensitive attributes or their proxies are highly influential, investigate if their impact is justified or indicative of bias.")
        recommendations.append("Use the `mitigate_bias` method to explore pre-processing (Reweighing) and post-processing (ThresholdOptimizer) solutions and compare their impact on fairness and performance.")
        
        return recommendations

    def mitigate_bias(self, dataset_name: str, target_column: str, sensitive_columns: List[str],
                     privileged_groups: Dict, unprivileged_groups: Dict) -> Dict[str, Any]:
        """
        Applies and evaluates different bias mitigation techniques.
        """
        if not AIF360_AVAILABLE or not FAIRLEARN_AVAILABLE:
            raise ImportError("AIF360 and Fairlearn are required for mitigation.")

        df = self._load_dataset_by_name(dataset_name)
        
        # --- 1. Baseline Model ---
        X = df.drop(columns=[target_column])
        y = df[target_column]
        categorical_columns = X.select_dtypes(include=['object', 'category']).columns
        X_encoded = X.copy()
        for col in categorical_columns:
            X_encoded[col] = LabelEncoder().fit_transform(X_encoded[col].astype(str))
        
        X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.3, random_state=42)
        
        baseline_model = RandomForestClassifier(random_state=42)
        baseline_model.fit(X_train.drop(columns=sensitive_columns, errors='ignore'), y_train)
        y_pred_baseline = baseline_model.predict(X_test.drop(columns=sensitive_columns, errors='ignore'))
        
        baseline_metrics = self._calculate_fairness_metrics_by_group(
            y_test, y_pred_baseline, df.loc[y_test.index][sensitive_columns[0]]
        )

        # --- 2. Pre-processing: Reweighing ---
        aif_dataset_train = StandardDataset(df.loc[y_train.index],
                                           label_name=target_column,
                                           favorable_class=1,
                                           protected_attribute_names=sensitive_columns,
                                           privileged_classes=[privileged_groups[k] for k in sensitive_columns],
                                           unprivileged_classes=[unprivileged_groups[k] for k in sensitive_columns])
        
        RW = Reweighing(unprivileged_groups=unprivileged_groups, privileged_groups=privileged_groups)
        reweighed_dataset = RW.fit_transform(aif_dataset_train)
        
        reweighed_model = RandomForestClassifier(random_state=42)
        reweighed_model.fit(reweighed_dataset.features, reweighed_dataset.labels.ravel(), 
                           sample_weight=reweighed_dataset.instance_weights)
        y_pred_reweighed = reweighed_model.predict(X_test.drop(columns=sensitive_columns, errors='ignore'))
        
        reweighed_metrics = self._calculate_fairness_metrics_by_group(
            y_test, y_pred_reweighed, df.loc[y_test.index][sensitive_columns[0]]
        )

        # --- 3. Post-processing: ThresholdOptimizer ---
        y_prob_baseline = baseline_model.predict_proba(X_test.drop(columns=sensitive_columns, errors='ignore'))[:, 1]
        postprocess_model = ThresholdOptimizer(estimator=baseline_model, constraints="demographic_parity")
        postprocess_model.fit(X_train.drop(columns=sensitive_columns, errors='ignore'), y_train, 
                             sensitive_features=df.loc[y_train.index][sensitive_columns[0]])
        y_pred_postprocessed = postprocess_model.predict(X_test.drop(columns=sensitive_columns, errors='ignore'), 
                                                        sensitive_features=df.loc[y_test.index][sensitive_columns[0]])
        
        postprocessed_metrics = self._calculate_fairness_metrics_by_group(
            y_test, y_pred_postprocessed, df.loc[y_test.index][sensitive_columns[0]]
        )

        return {
            "baseline": {"performance": self._calculate_performance_metrics(y_test, y_pred_baseline), "fairness": baseline_metrics},
            "reweighing": {"performance": self._calculate_performance_metrics(y_test, y_pred_reweighed), "fairness": reweighed_metrics},
            "threshold_optimizer": {"performance": self._calculate_performance_metrics(y_test, y_pred_postprocessed), "fairness": postprocessed_metrics}
        }

