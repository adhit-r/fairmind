"""
Refactored Bias Detection Service using BaseService.

This demonstrates migrating an existing service to the new architecture:
- Extends BaseService for common functionality
-Uses dependency injection
- Returns domain objects (not HTTP responses)
- Uses core exceptions
- Structured logging
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from core.base_service import BaseService, AsyncBaseService
from core.container import service, ServiceLifetime, inject
from core.exceptions import ValidationError, InvalidDataError
from core.interfaces import ILogger
from database.duckdb_manager import DuckDBManager
# Note: DatasetService import might cause circular dependency if not careful.
# We will use lazy injection or import inside method if needed.
from typing import Union
import uuid


# Domain Models
@dataclass
class BiasAnalysisResult:
    """Domain model for bias analysis results."""
    timestamp: str
    dataset_info: Dict[str, Any]
    data_quality: Dict[str, Any]
    bias_detection: Dict[str, Any]
    fairness_metrics: Dict[str, Any]
    recommendations: List[str]


@dataclass
class ModelBiasResult:
    """Domain model for model bias analysis results."""
    timestamp: str
    model_fairness: Dict[str, Any]
    overall_performance: Dict[str, float]
    bias_summary: Dict[str, Any]


@service(lifetime=ServiceLifetime.SINGLETON)
class BiasDetectionService(AsyncBaseService):
    """
    Refactored bias detection service using new architecture patterns.
    
    Changes from old service:
    - Extends AsyncBaseService
    - Uses dependency injection
    - Returns domain objects
    - Uses ValidationError instead of generic exceptions
    - Uses structured logging via self.logger
    - Validation helpers from BaseService
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.duckdb = inject(DuckDBManager)
        # Lazy load DatasetService to avoid potential circular imports
        from domain.dataset.services.dataset_service import DatasetService
        self.dataset_service = inject(DatasetService)
        
        self.bias_types = {
            'reporting_bias': 'Frequency of events in dataset does not reflect real-world frequency',
            'historical_bias': 'Historical data reflects past inequities',
            'automation_bias': 'Favoring automated results over manual ones',
            'selection_bias': 'Dataset examples not reflective of real-world distribution',
            'coverage_bias': 'Data not selected in representative fashion',
            'non_response_bias': 'Data unrepresentative due to participation gaps',
            'sampling_bias': 'Proper randomization not used in data collection',
            'group_attribution_bias': 'Generalizing individuals to entire groups',
            'in_group_bias': 'Preference for members of own group',
            'out_group_homogeneity_bias': 'Stereotyping members of other groups',
            'implicit_bias': 'Assumptions based on personal experiences',
            'confirmation_bias': 'Processing data to affirm pre-existing beliefs',
            'experimenter_bias': 'Training until results align with hypothesis'
        }
    
    async def analyze_dataset_bias(
        self,
        dataset_or_df: Union[pd.DataFrame, str],
        sensitive_attributes: List[str],
        target_column: str
    ) -> BiasAnalysisResult:
        """
        Comprehensive bias analysis of a dataset using DuckDB.
        
        Args:
            dataset_or_df: Input DataFrame or dataset ID (str)
            sensitive_attributes: List of sensitive attribute column names
            target_column: Target variable column name
            
        Returns:
            BiasAnalysisResult domain object
        """
        self._validate_required(
            dataset_or_df=dataset_or_df,
            sensitive_attributes=sensitive_attributes,
            target_column=target_column
        )
        
        # Generate unique table name for this analysis session
        table_name = f"analysis_{uuid.uuid4().hex}"
        
        try:
            # Register data in DuckDB
            if isinstance(dataset_or_df, str):
                # It's a dataset_id
                dataset = await self.dataset_service.get_dataset(dataset_or_df)
                file_path = dataset.file_path
                self.duckdb.register_file(table_name, file_path)
                
                # We need column names for validation
                # We can query them from DuckDB
                schema_df = self.duckdb.query_df(f"DESCRIBE {table_name}")
                columns = schema_df['column_name'].tolist()
                num_samples = self.duckdb.execute_query(f"SELECT COUNT(*) FROM {table_name}")[0][0]
                
            else:
                # It's a DataFrame
                df = dataset_or_df
                self.duckdb.get_connection().register(table_name, df)
                columns = df.columns.tolist()
                num_samples = len(df)

            # Validate columns exist
            missing_cols = [col for col in sensitive_attributes if col not in columns]
            if missing_cols:
                raise ValidationError(
                    f"Sensitive attributes not found in dataset: {missing_cols}",
                    details={"missing_columns": missing_cols}
                )
            
            if target_column not in columns:
                raise ValidationError(
                    f"Target column '{target_column}' not found in dataset",
                    details={"target_column": target_column}
                )
            
            # Log operation
            self._log_operation(
                "analyze_dataset_bias",
                num_samples=num_samples,
                num_features=len(columns),
                sensitive_attributes=sensitive_attributes,
                engine="duckdb"
            )
            
            analysis_results = {
                'timestamp': datetime.now().isoformat(),
                'dataset_info': self._analyze_dataset_info_sql(table_name, columns),
                'data_quality': self._analyze_data_quality_sql(table_name, sensitive_attributes, columns),
                'bias_detection': self._detect_bias_types_sql(table_name, sensitive_attributes, target_column),
                'fairness_metrics': self._calculate_fairness_metrics_sql(table_name, sensitive_attributes, target_column),
                'recommendations': []
            }
            
            # Generate recommendations (logic remains similar, operating on the results dict)
            analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
            
            return BiasAnalysisResult(**analysis_results)
        
        except Exception as e:
            self._handle_error(
                "analyze_dataset_bias",
                e,
                raise_as=InvalidDataError,
                sensitive_attributes=sensitive_attributes
            )
        finally:
            # Cleanup view
            try:
                self.duckdb.execute_query(f"DROP VIEW IF EXISTS {table_name}")
            except Exception:
                pass
    
    # Keep all the existing analysis methods but update error handling...
    # For brevity, showing just the key ones:
    
    def _analyze_dataset_info_sql(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        """Analyze basic dataset information using SQL."""
        try:
            # Get schema types
            schema_df = self.duckdb.query_df(f"DESCRIBE {table_name}")
            
            numeric_types = ['BIGINT', 'INTEGER', 'DOUBLE', 'FLOAT', 'DECIMAL', 'HUGEINT', 'SMALLINT', 'TINYINT', 'UBIGINT', 'UINTEGER', 'USMALLINT', 'UTINYINT']
            
            numeric_features = []
            categorical_features = []
            
            for _, row in schema_df.iterrows():
                col_type = row['column_type'].split('(')[0].upper() # Handle DECIMAL(10,2) etc
                if any(t in col_type for t in numeric_types):
                    numeric_features.append(row['column_name'])
                else:
                    categorical_features.append(row['column_name'])
            
            # Get total samples
            total_samples = self.duckdb.execute_query(f"SELECT COUNT(*) FROM {table_name}")[0][0]
            
            # Calculate missing values
            # Construct a query to sum nulls for all columns
            null_checks = [f"COUNT(*) - COUNT({col})" for col in columns]
            null_query = f"SELECT {', '.join(null_checks)} FROM {table_name}"
            null_counts = self.duckdb.execute_query(null_query)[0]
            
            total_missing = sum(null_counts)
            total_cells = total_samples * len(columns)
            
            return {
                'total_samples': total_samples,
                'total_features': len(columns),
                'missing_values_total': int(total_missing),
                'missing_values_percentage': float((total_missing / total_cells) * 100) if total_cells > 0 else 0.0,
                'numeric_features': numeric_features,
                'categorical_features': categorical_features
            }
        except Exception as e:
            self._log_error("_analyze_dataset_info_sql", e)
            raise InvalidDataError(f"Failed to analyze dataset info: {str(e)}")

    def _analyze_data_quality_sql(self, table_name: str, sensitive_attributes: List[str], columns: List[str]) -> Dict[str, Any]:
        """Analyze data quality using SQL."""
        try:
            # Missing values analysis by group
            missing_analysis = {}
            for attr in sensitive_attributes:
                if attr in columns:
                    # Calculate missing rate per group
                    # We need to check if any other column is null, grouped by attr
                    # This is complex in SQL for "any column". 
                    # The legacy code did: df.groupby(attr).apply(lambda x: x.isnull().sum() / len(x))
                    # This means: for each group, sum of nulls in ALL columns / number of rows in group
                    
                    # First get group counts
                    group_counts_df = self.duckdb.query_df(f"SELECT {attr}, COUNT(*) as count FROM {table_name} GROUP BY {attr}")
                    group_counts = dict(zip(group_counts_df[attr].astype(str), group_counts_df['count']))
                    
                    # Now get null counts per group
                    # We can sum the nulls for all columns
                    null_sums = [f"(COUNT(*) - COUNT({col}))" for col in columns]
                    total_nulls_expr = " + ".join(null_sums)
                    
                    query = f"SELECT {attr}, ({total_nulls_expr}) as total_nulls FROM {table_name} GROUP BY {attr}"
                    nulls_df = self.duckdb.query_df(query)
                    
                    attr_missing = {}
                    for _, row in nulls_df.iterrows():
                        group = str(row[attr])
                        total_nulls = row['total_nulls']
                        count = group_counts.get(group, 0)
                        # Normalize by number of rows (legacy behavior seems to be sum of nulls / rows, which is > 1 potentially if multiple cols null)
                        # Legacy: x.isnull().sum() returns Series of null counts per col. .sum() sums them up. / len(x).
                        # Yes, it's average missing values per row.
                        attr_missing[group] = float(total_nulls / count) if count > 0 else 0.0
                        
                    missing_analysis[attr] = attr_missing

            # Unexpected values (Outliers)
            # Using IQR method in SQL
            unexpected_values = {}
            # Identify numeric columns first (reuse logic or pass it)
            # For simplicity, query schema again or assume passed columns are all checkable
            # Let's just check numeric columns
            schema_df = self.duckdb.query_df(f"DESCRIBE {table_name}")
            numeric_types = ['BIGINT', 'INTEGER', 'DOUBLE', 'FLOAT', 'DECIMAL', 'HUGEINT', 'SMALLINT', 'TINYINT']
            numeric_cols = [
                row['column_name'] for _, row in schema_df.iterrows() 
                if any(t in row['column_type'].upper() for t in numeric_types) 
                and row['column_name'] not in sensitive_attributes
            ]
            
            for col in numeric_cols:
                # Calculate Q1, Q3
                quantiles = self.duckdb.execute_query(f"SELECT quantile_cont({col}, 0.25), quantile_cont({col}, 0.75) FROM {table_name}")
                q1, q3 = quantiles[0]
                if q1 is None or q3 is None:
                    continue
                    
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outlier_count = self.duckdb.execute_query(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {col} < {lower_bound} OR {col} > {upper_bound}"
                )[0][0]
                
                total_count = self.duckdb.execute_query(f"SELECT COUNT(*) FROM {table_name}")[0][0]
                
                unexpected_values[col] = {
                    'outlier_count': outlier_count,
                    'outlier_percentage': float((outlier_count / total_count) * 100) if total_count > 0 else 0.0
                }

            # Data skew analysis
            data_skew = {}
            for attr in sensitive_attributes:
                if attr in columns:
                    query = f"SELECT {attr}, COUNT(*) as count FROM {table_name} GROUP BY {attr}"
                    df_skew = self.duckdb.query_df(query)
                    
                    counts = df_skew['count'].tolist()
                    if not counts:
                        continue
                        
                    max_count = max(counts)
                    min_count = min(counts)
                    total = sum(counts)
                    
                    groups = dict(zip(df_skew[attr].astype(str), df_skew['count']))
                    distribution = {k: v/total for k, v in groups.items()}
                    
                    data_skew[attr] = {
                        'distribution': distribution,
                        'imbalance_ratio': float(max_count / min_count) if min_count > 0 else float('inf'),
                        'minority_group_size': int(min_count),
                        'majority_group_size': int(max_count),
                        'groups': groups
                    }

            return {
                'missing_values': missing_analysis,
                'unexpected_values': unexpected_values,
                'data_skew': data_skew
            }
        except Exception as e:
            self._log_error("_analyze_data_quality_sql", e)
            raise InvalidDataError(f"Failed to analyze data quality: {str(e)}")

    def _detect_bias_types_sql(self, table_name: str, sensitive_attributes: List[str], target_column: str) -> Dict[str, Any]:
        """Detect specific types of bias in the dataset using SQL."""
        try:
            bias_detections = {}
            
            # 1. Reporting Bias (Target Distribution)
            if target_column:
                query = f"SELECT \"{target_column}\", COUNT(*) as count FROM {table_name} GROUP BY \"{target_column}\""
                target_dist_df = self.duckdb.query_df(query)
                total = target_dist_df['count'].sum()
                
                if total > 0:
                    target_dist_df['prop'] = target_dist_df['count'] / total
                    max_prop = target_dist_df['prop'].max()
                    min_prop = target_dist_df['prop'].min()
                    
                    extreme_dist = max_prop > 0.8
                    very_skewed = (max_prop / min_prop > 10) if min_prop > 0 else True
                    
                    bias_detections['reporting_bias'] = {
                        'detected': bool(extreme_dist or very_skewed),
                        'target_distribution': dict(zip(target_dist_df[target_column].astype(str), target_dist_df['prop'])),
                        'max_proportion': float(max_prop),
                        'min_proportion': float(min_prop),
                        'ratio': float(max_prop / min_prop) if min_prop > 0 else float('inf'),
                        'indicators': {'extreme_distribution': bool(extreme_dist), 'very_skewed': bool(very_skewed)}
                    }
            
            # 2. Historical Bias (Group Disparities)
            historical_bias_indicators = {}
            for attr in sensitive_attributes:
                query = f"SELECT \"{attr}\", COUNT(*) as count FROM {table_name} GROUP BY \"{attr}\""
                group_dist_df = self.duckdb.query_df(query)
                total = group_dist_df['count'].sum()
                
                if total > 0:
                    group_dist_df['prop'] = group_dist_df['count'] / total
                    max_prop = group_dist_df['prop'].max()
                    min_prop = group_dist_df['prop'].min()
                    
                    extreme_disparity = (max_prop / min_prop > 5) if min_prop > 0 else True
                    
                    historical_bias_indicators[attr] = {
                        'detected': bool(extreme_disparity),
                        'group_distribution': dict(zip(group_dist_df[attr].astype(str), group_dist_df['prop'])),
                        'disparity_ratio': float(max_prop / min_prop) if min_prop > 0 else float('inf'),
                        'majority_group': str(group_dist_df.loc[group_dist_df['prop'].idxmax(), attr]),
                        'minority_group': str(group_dist_df.loc[group_dist_df['prop'].idxmin(), attr])
                    }
            bias_detections['historical_bias'] = {
                'detected': any(i['detected'] for i in historical_bias_indicators.values()),
                'indicators': historical_bias_indicators
            }
            
            # 3. Selection Bias (Coverage)
            selection_bias_indicators = {}
            for attr in sensitive_attributes:
                # Reuse group distribution from historical bias if possible, but for clarity re-query or just use logic
                # We need coverage < 5%
                query = f"SELECT \"{attr}\", COUNT(*) as count FROM {table_name} GROUP BY \"{attr}\""
                group_counts_df = self.duckdb.query_df(query)
                total = group_counts_df['count'].sum()
                
                coverage_bias = False
                if total > 0:
                    coverage_bias = (group_counts_df['count'] / total < 0.05).any()
                
                selection_bias_indicators[attr] = {
                    'detected': bool(coverage_bias),
                    'coverage_bias': bool(coverage_bias),
                    'group_representation': dict(zip(group_counts_df[attr].astype(str), group_counts_df['count'] / total))
                }
            bias_detections['selection_bias'] = {
                'detected': any(i['detected'] for i in selection_bias_indicators.values()),
                'indicators': selection_bias_indicators
            }
            
            # 4. Group Attribution Bias (Correlations)
            # Check correlations between sensitive attributes and numeric columns
            group_attribution_indicators = {}
            schema_df = self.duckdb.query_df(f"DESCRIBE {table_name}")
            numeric_types = ['BIGINT', 'INTEGER', 'DOUBLE', 'FLOAT', 'DECIMAL']
            numeric_cols = [
                row['column_name'] for _, row in schema_df.iterrows() 
                if any(t in row['column_type'].upper() for t in numeric_types) 
                and row['column_name'] not in sensitive_attributes
            ]
            
            for attr in sensitive_attributes:
                # Only if attr is numeric-ish? Or encode it?
                # DuckDB corr requires numeric.
                # If attr is categorical (string), we can't easily run corr without encoding.
                # Legacy code checked `pd.api.types.is_numeric_dtype(df[attr])`.
                # We can check schema for attr.
                attr_type = schema_df[schema_df['column_name'] == attr]['column_type'].iloc[0].upper()
                is_numeric_attr = any(t in attr_type for t in numeric_types)
                
                correlations = {}
                if is_numeric_attr:
                    for col in numeric_cols:
                        try:
                            corr_val = self.duckdb.execute_query(f"SELECT CORR(\"{attr}\", \"{col}\") FROM {table_name}")[0][0]
                            if corr_val is not None:
                                correlations[col] = float(corr_val)
                        except Exception:
                            pass
                
                strong_correlations = {k: v for k, v in correlations.items() if abs(v) > 0.3}
                group_attribution_indicators[attr] = {
                    'detected': len(strong_correlations) > 0,
                    'strong_correlations': strong_correlations
                }
            
            bias_detections['group_attribution_bias'] = {
                'detected': any(i['detected'] for i in group_attribution_indicators.values()),
                'indicators': group_attribution_indicators
            }

            # 5. Implicit Bias (Feature Disparities)
            implicit_bias_indicators = {}
            for attr in sensitive_attributes:
                feature_disparities = {}
                for col in numeric_cols:
                    try:
                        # Calculate mean per group
                        query = f"SELECT \"{attr}\", AVG(\"{col}\") as mean_val FROM {table_name} GROUP BY \"{attr}\""
                        means_df = self.duckdb.query_df(query)
                        
                        if not means_df.empty:
                            means = means_df['mean_val']
                            max_mean = means.max()
                            min_mean = means.min()
                            avg_mean = means.mean()
                            
                            mean_disparity = (max_mean - min_mean) / avg_mean if avg_mean != 0 else 0
                            
                            feature_disparities[col] = {
                                'mean_disparity': float(mean_disparity),
                                'significant_disparity': bool(mean_disparity > 0.5)
                            }
                    except Exception:
                        pass
                
                significant = {k: v for k, v in feature_disparities.items() if v['significant_disparity']}
                implicit_bias_indicators[attr] = {
                    'detected': len(significant) > 0,
                    'significant_disparities': significant
                }
            
            bias_detections['implicit_bias'] = {
                'detected': any(i['detected'] for i in implicit_bias_indicators.values()),
                'indicators': implicit_bias_indicators
            }
            
            return bias_detections
        except Exception as e:
            self._log_error("_detect_bias_types_sql", e)
            raise InvalidDataError(f"Failed to detect bias types: {str(e)}")

    def _calculate_fairness_metrics_sql(self, table_name: str, sensitive_attributes: List[str], target_column: str) -> Dict[str, Any]:
        """Calculate fairness metrics using SQL."""
        try:
            fairness_metrics = {}
            
            for attr in sensitive_attributes:
                # Demographic Parity: P(Y=1|A=a)
                # We need average target value per group.
                # Assuming target is numeric (0/1). If not, we might need to cast or count specific value.
                # Let's assume numeric for now as per legacy.
                
                query = f"SELECT \"{attr}\", AVG(CAST(\"{target_column}\" AS DOUBLE)) as acceptance_rate FROM {table_name} GROUP BY \"{attr}\""
                try:
                    metrics_df = self.duckdb.query_df(query)
                except Exception:
                    # Maybe target is string? Try casting to int if it looks like '0'/'1' or just skip
                    continue
                
                acceptance_rates = dict(zip(metrics_df[attr].astype(str), metrics_df['acceptance_rate']))
                
                if acceptance_rates:
                    max_rate = max(acceptance_rates.values())
                    min_rate = min(acceptance_rates.values())
                    dp_disparity = max_rate - min_rate
                    dp_ratio = max_rate / min_rate if min_rate > 0 else float('inf')
                else:
                    dp_disparity = 0.0
                    dp_ratio = 1.0
                
                demographic_parity = {
                    'acceptance_rates': acceptance_rates,
                    'disparity': float(dp_disparity),
                    'ratio': float(dp_ratio),
                    'fair': bool(dp_disparity < 0.1),
                    'groups': list(acceptance_rates.keys())
                }
                
                # Equality of Opportunity: P(Y=1|A=a, Y_true=1)
                # Since this is dataset bias, we treat target_column as Y_true.
                # So this metric is actually P(Y=1|A=a, Y=1) which is always 1.0?
                # Wait, legacy code: "Only consider positive examples (target = 1)"
                # "opportunity_rates[group] = len(positive_data) / len(group_data)"
                # positive_data = group_data[group_data[target] == 1]
                # len(positive_data) / len(group_data) IS P(Y=1|A=a).
                # So Legacy Equality of Opportunity WAS JUST Demographic Parity.
                # I will replicate this behavior but note it's redundant.
                
                equality_of_opportunity = {
                    'opportunity_rates': acceptance_rates, # Same as DP
                    'disparity': float(dp_disparity),
                    'ratio': float(dp_ratio),
                    'fair': bool(dp_disparity < 0.1),
                    'groups': list(acceptance_rates.keys())
                }
                
                # Statistical Parity
                # Difference between two groups. If > 2 groups, legacy code failed or picked 2?
                # Legacy: "if len(groups) != 2: return error"
                statistical_parity = {'fair': True}
                groups = list(acceptance_rates.keys())
                if len(groups) == 2:
                    diff = acceptance_rates[groups[0]] - acceptance_rates[groups[1]]
                    statistical_parity = {
                        'group1_rate': float(acceptance_rates[groups[0]]),
                        'group2_rate': float(acceptance_rates[groups[1]]),
                        'statistical_parity_difference': float(diff),
                        'fair': bool(abs(diff) < 0.1),
                        'groups': groups
                    }
                
                fairness_metrics[attr] = {
                    'demographic_parity': demographic_parity,
                    'equality_of_opportunity': equality_of_opportunity,
                    'statistical_parity': statistical_parity
                }
            
            return fairness_metrics
        except Exception as e:
            self._log_error("_calculate_fairness_metrics_sql", e)
            raise InvalidDataError(f"Failed to calculate fairness metrics: {str(e)}")

    def _calculate_demographic_parity(self, df: pd.DataFrame, sensitive_attr: str, 
                                    target_column: str) -> Dict[str, Any]:
        """Calculate demographic parity across groups."""
        groups = df[sensitive_attr].unique()
        acceptance_rates = {}
        
        for group in groups:
            group_data = df[df[sensitive_attr] == group]
            # Handle non-numeric target if necessary, but assuming numeric/binary for now
            try:
                acceptance_rates[str(group)] = float(group_data[target_column].mean())
            except Exception:
                acceptance_rates[str(group)] = 0.0
        
        # Calculate disparity
        if acceptance_rates:
            max_rate = max(acceptance_rates.values())
            min_rate = min(acceptance_rates.values())
            disparity = max_rate - min_rate
            ratio = max_rate / min_rate if min_rate > 0 else float('inf')
        else:
            disparity = 0.0
            ratio = 1.0
        
        return {
            'acceptance_rates': acceptance_rates,
            'disparity': float(disparity),
            'ratio': float(ratio),
            'fair': bool(disparity < 0.1),  # Less than 10% difference
            'groups': [str(g) for g in groups]
        }

    def _calculate_equality_of_opportunity(self, df: pd.DataFrame, sensitive_attr: str, 
                                         target_column: str) -> Dict[str, Any]:
        """Calculate equality of opportunity for positive class."""
        groups = df[sensitive_attr].unique()
        opportunity_rates = {}
        
        for group in groups:
            group_data = df[df[sensitive_attr] == group]
            # Only consider positive examples (target = 1)
            # Assuming 1 is the positive class. If target is not binary 0/1, this needs adjustment.
            # For robustness, let's assume > 0 or True is positive if not explicitly 1.
            try:
                positive_data = group_data[group_data[target_column] == 1]
                if len(positive_data) > 0: # This logic in legacy was flawed, it should be P(Y_hat=1 | Y=1)
                    # But here we are analyzing DATASET bias, so we don't have predictions Y_hat.
                    # Equality of Opportunity is a model metric.
                    # For dataset, we can only look at base rates (Demographic Parity).
                    # The legacy code calculated "true positive rate" but using ground truth as both?
                    # "Only consider positive examples (target = 1)" -> This is just the prevalence in the group?
                    # No, P(Y=1|A=a) is base rate.
                    # If we are analyzing dataset, maybe we mean "Label bias"?
                    # Let's stick to the legacy implementation for now to maintain behavior.
                    # Legacy: opportunity_rates[group] = len(positive_data) / len(group_data)
                    # This IS the base rate (Demographic Parity).
                    # So it duplicates demographic parity?
                    # Let's just copy it.
                    opportunity_rates[str(group)] = float(len(positive_data) / len(group_data))
                else:
                    opportunity_rates[str(group)] = 0.0
            except Exception:
                opportunity_rates[str(group)] = 0.0
        
        # Calculate disparity
        if opportunity_rates:
            max_rate = max(opportunity_rates.values())
            min_rate = min(opportunity_rates.values())
            disparity = max_rate - min_rate
            ratio = max_rate / min_rate if min_rate > 0 else float('inf')
        else:
            disparity = 0.0
            ratio = 1.0
        
        return {
            'opportunity_rates': opportunity_rates,
            'disparity': float(disparity),
            'ratio': float(ratio),
            'fair': bool(disparity < 0.1),  # Less than 10% difference
            'groups': [str(g) for g in groups]
        }

    def _calculate_statistical_parity(self, df: pd.DataFrame, sensitive_attr: str, 
                                    target_column: str) -> Dict[str, Any]:
        """Calculate statistical parity difference."""
        groups = df[sensitive_attr].unique()
        if len(groups) != 2:
            return {'error': 'Statistical parity requires exactly 2 groups', 'fair': True}
        
        group1, group2 = groups
        
        try:
            # Calculate positive prediction rates (base rates in dataset)
            group1_rate = df[df[sensitive_attr] == group1][target_column].mean()
            group2_rate = df[df[sensitive_attr] == group2][target_column].mean()
            
            statistical_parity_difference = group1_rate - group2_rate
            
            return {
                'group1_rate': float(group1_rate),
                'group2_rate': float(group2_rate),
                'statistical_parity_difference': float(statistical_parity_difference),
                'fair': bool(abs(statistical_parity_difference) < 0.1),  # Less than 10% difference
                'groups': [str(group1), str(group2)]
            }
        except Exception:
             return {'error': 'Calculation failed', 'fair': True}

    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on bias analysis findings."""
        recommendations = []
        
        # Data quality recommendations
        data_quality = analysis_results.get('data_quality', {})
        
        if data_quality.get('data_skew'):
            for attr, skew_info in data_quality['data_skew'].items():
                if skew_info.get('imbalance_ratio', 0) > 5:
                    recommendations.append(
                        f"High data imbalance detected in {attr} (ratio: {skew_info['imbalance_ratio']:.2f}). "
                        "Consider oversampling minority groups or collecting more balanced data."
                    )
        
        # Bias detection recommendations
        bias_detection = analysis_results.get('bias_detection', {})
        
        if bias_detection.get('reporting_bias', {}).get('detected'):
            recommendations.append(
                "Reporting bias detected in target variable. Consider collecting more representative data "
                "or using techniques like SMOTE to balance the dataset."
            )
        
        if bias_detection.get('historical_bias', {}).get('detected'):
            recommendations.append(
                "Historical bias detected. Consider using more recent data or applying bias mitigation "
                "techniques like MinDiff or Counterfactual Logit Pairing."
            )
        
        if bias_detection.get('selection_bias', {}).get('detected'):
            recommendations.append(
                "Selection bias detected. Review data collection methodology and consider "
                "collecting more representative samples."
            )
        
        # Fairness metrics recommendations
        fairness_metrics = analysis_results.get('fairness_metrics', {})
        
        for attr, metrics in fairness_metrics.items():
            if not metrics.get('demographic_parity', {}).get('fair'):
                recommendations.append(
                    f"Demographic parity violation detected for {attr}. Consider applying "
                    "fairness-aware training techniques."
                )
            
            if not metrics.get('equality_of_opportunity', {}).get('fair'):
                recommendations.append(
                    f"Equality of opportunity violation detected for {attr}. Consider using "
                    "techniques that ensure equal true positive rates across groups."
                )
        
        if not recommendations:
            recommendations.append("No significant bias issues detected. Continue monitoring for bias as the model evolves.")
        
        return recommendations
