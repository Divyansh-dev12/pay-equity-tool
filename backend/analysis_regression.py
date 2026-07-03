"""
Pay Equity Analysis Engine - Regression-Based Approach (Simplified MVP)
Uses statsmodels OLS for statistical inference with p-values
Implements residual-based anomaly detection
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class RegressionAnalysisResult:
    """Container for complete analysis results"""
    model_summary: Dict
    coefficients: Dict
    predictions: List[Dict]
    anomalies: Dict
    recommendations: Dict
    data_quality: Dict
    model_stats: Dict


def _to_json_serializable(obj):
    """Convert numpy/pandas types to JSON-serializable Python types"""
    if isinstance(obj, (float, np.floating)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if pd.isna(obj):
        return None
    return obj


class PayEquityRegressionAnalyzer:
    """
    Regression-based pay equity analysis using OLS.

    Core formula: ln(salary) = β₀ + β₁·level + β₂·tenure + β₃·performance +
                               β₄·function + β₅·location + β_gender·gender + ε
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.model = None
        self.original_df = None
        self.feature_names = []

    def run_full_analysis(self,
                        outlier_sigma: float = 3.0,
                        underpaid_sigma: float = 1.0) -> RegressionAnalysisResult:
        """Execute complete analysis pipeline"""

        print("\n" + "="*70)
        print("PAY EQUITY REGRESSION ANALYSIS")
        print("="*70)

        # Step 1: Data Preparation
        print("\nStep 1: Data preparation...")
        df_clean, data_quality = self._prepare_data()

        # Step 2: Outlier Detection
        print("Step 2: Outlier detection (by job_level + function)...")
        df_clean = self._detect_and_flag_outliers(df_clean, outlier_sigma)

        # Step 3: Prepare for Regression
        print("Step 3: Feature engineering & preparing regression...")
        X, y, feature_names = self._prepare_regression_data(df_clean)
        self.feature_names = feature_names  # store for coefficient/gap mapping

        # Step 4: Fit Regression
        print("Step 4: Fitting OLS regression model...")
        self.model = self._fit_ols_model(X, y)

        # Step 5: Calculate Predictions
        print("Step 5: Calculating predictions & residuals...")
        df_clean = self._add_predictions(df_clean, X, y)

        # Step 6: Detect Anomalies
        print("Step 6: Detecting underpaid anomalies...")
        anomalies = self._detect_anomalies(df_clean, underpaid_sigma)

        # Step 7: Generate Recommendations
        print("Step 7: Generating recommendations...")
        recommendations = self._generate_recommendations(df_clean, anomalies)

        # Step 8: Calculate Stats
        print("Step 8: Calculating model statistics...")
        model_stats = self._get_model_stats()

        # Step 9: Format Coefficients
        print("Step 9: Formatting results...")
        coef_dict = self._format_coefficients(feature_names)

        # Prepare predictions for output
        predictions_output = self._format_predictions(df_clean)

        print("\n" + "="*70)
        print("✓ ANALYSIS COMPLETE")
        print("="*70 + "\n")

        # Clean model stats to avoid NaN/inf in JSON
        r2 = float(self.model.rsquared)
        if math.isnan(r2) or math.isinf(r2):
            r2 = None
        adj_r2 = float(self.model.rsquared_adj)
        if math.isnan(adj_r2) or math.isinf(adj_r2):
            adj_r2 = None

        # Clean model_stats
        cleaned_model_stats = {}
        for k, v in model_stats.items():
            if isinstance(v, float):
                try:
                    if math.isnan(v) or math.isinf(v):
                        cleaned_model_stats[k] = None
                    else:
                        cleaned_model_stats[k] = v
                except (TypeError, ValueError):
                    cleaned_model_stats[k] = v
            else:
                cleaned_model_stats[k] = v

        return RegressionAnalysisResult(
            model_summary={
                'formula': 'ln(base_salary) ~ job_level + tenure + performance + function + location + gender',
                'total_observations': int(self.model.nobs),
                'r_squared': r2,
                'adjusted_r_squared': adj_r2
            },
            coefficients=coef_dict,
            predictions=predictions_output,
            anomalies=anomalies,
            recommendations=recommendations,
            data_quality=data_quality,
            model_stats=cleaned_model_stats
        )

    def _prepare_data(self) -> Tuple[pd.DataFrame, Dict]:
        """
        Validate & clean data per spec:
        - Exclude: missing gender, base_salary, location
        - Replace: performance → "No Rating", tenure → "No Tenure Data"
        """
        df = self.df.copy()
        initial_count = len(df)

        # Exclude critical missing values
        df = df.dropna(subset=['gender', 'base_salary', 'location'])
        excluded_critical = initial_count - len(df)

        # Replace performance
        if 'performance_rating' in df.columns:
            missing_perf = df['performance_rating'].isnull().sum()
            df['performance_rating'] = df['performance_rating'].fillna('No Rating')
        else:
            missing_perf = 0
            df['performance_rating'] = 'No Rating'

        # Replace tenure
        if 'tenure_years' in df.columns:
            missing_tenure = df['tenure_years'].isnull().sum()
            df['tenure_years'] = df['tenure_years'].fillna('No Tenure Data')
        else:
            missing_tenure = 0
            df['tenure_years'] = 'No Tenure Data'

        # Add job_function if missing
        if 'job_function' not in df.columns:
            df['job_function'] = df.get('job_title', 'General')

        data_quality = {
            'input_rows': int(initial_count),
            'output_rows': int(len(df)),
            'excluded_critical': int(excluded_critical),
            'missing_performance': int(missing_perf),
            'missing_tenure': int(missing_tenure),
            'excluded_reasons': 'Missing gender, base_salary, or location'
        }

        return df, data_quality

    def _detect_and_flag_outliers(self, df: pd.DataFrame, threshold_sigma: float) -> pd.DataFrame:
        """
        Flag outliers by job_level + job_function segment.
        Mark with is_model_excluded=True (keep in dataset, don't use in regression).
        """
        df['is_model_excluded'] = False

        # Group by level and function
        groupby_cols = ['job_level', 'job_function']

        for group_key, group_data in df.groupby(groupby_cols, dropna=False):
            if len(group_data) < 2:
                continue

            median = group_data['base_salary'].median()
            std_dev = group_data['base_salary'].std()

            if std_dev == 0 or pd.isna(std_dev):
                continue

            # Calculate z-score
            z_scores = np.abs((group_data['base_salary'] - median) / std_dev)
            outlier_mask = z_scores > threshold_sigma

            df.loc[group_data[outlier_mask].index, 'is_model_excluded'] = True

        excluded_count = df['is_model_excluded'].sum()
        print(f"   - Flagged {excluded_count} outliers for exclusion from model")

        return df

    def _prepare_regression_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare X and y for regression.
        - y: log-transformed salary
        - X: numeric features + one-hot encoded categoricals
        """
        # Use only non-excluded employees
        df_model = df[~df['is_model_excluded']].copy()

        # Target: log-transformed salary
        y = np.log(df_model['base_salary'].values)

        # Features
        features = []
        feature_names = []

        # 1. Job Level (numeric: extract number from 'L1', 'L2', etc)
        job_level_numeric = pd.to_numeric(
            df_model['job_level'].astype(str).str.replace('L', ''),
            errors='coerce'
        ).fillna(2).values  # Default to level 2 if missing
        features.append(job_level_numeric)
        feature_names.append('job_level')

        # 2. Tenure (numeric for numeric values, 0 for categorical)
        tenure_numeric = []
        for val in df_model['tenure_years']:
            try:
                tenure_numeric.append(float(val))
            except:
                tenure_numeric.append(0)  # Default for "No Tenure Data"
        features.append(np.array(tenure_numeric))
        feature_names.append('tenure_years')

        # 3. Performance (numeric for numeric values, 0 for categorical)
        perf_numeric = []
        for val in df_model['performance_rating']:
            try:
                perf_numeric.append(float(val))
            except:
                perf_numeric.append(3.0)  # Default middle rating for "No Rating"
        features.append(np.array(perf_numeric))
        feature_names.append('performance_rating')

        # 4. Job Function (one-hot, drop first)
        function_dummies = pd.get_dummies(df_model['job_function'], drop_first=True)
        for col in function_dummies.columns:
            features.append(function_dummies[col].values)
            feature_names.append(f'function_{col}')

        # 5. Location (one-hot, drop first)
        location_dummies = pd.get_dummies(df_model['location'], drop_first=True)
        for col in location_dummies.columns:
            features.append(location_dummies[col].values)
            feature_names.append(f'location_{col}')

        # 6. Gender: measure the Female effect explicitly (Male = baseline).
        # This matches the spec formula Controlled Gap = (e^β_gender_Female - 1),
        # where a NEGATIVE coefficient means women are underpaid. We do NOT use
        # get_dummies(drop_first=True) here because it drops "Female" alphabetically
        # and would instead measure a Male premium (inverting the sign the
        # recommendation logic depends on).
        gender_lower = df_model['gender'].astype(str).str.lower()
        female_indicator = gender_lower.isin(['female', 'f']).astype(float).values
        features.append(female_indicator)
        feature_names.append('gender_Female')

        # Combine into feature matrix
        X = np.column_stack(features)

        return X, y, feature_names

    def _fit_ols_model(self, X: np.ndarray, y: np.ndarray):
        """Fit OLS regression with statsmodels"""
        X_with_const = sm.add_constant(X)
        model = sm.OLS(y, X_with_const).fit()

        print(f"   - Model R² = {model.rsquared:.4f}")
        print(f"   - Observations = {model.nobs}")

        return model

    def _add_predictions(self, df: pd.DataFrame, X: np.ndarray, y: np.ndarray) -> pd.DataFrame:
        """
        Calculate predicted salary and residuals.
        For excluded employees, use cohort median fallback.
        """
        df = df.copy()

        # Initialize columns
        df['predicted_salary'] = np.nan
        df['residual_log'] = np.nan
        df['gap_dollars'] = np.nan

        # Add predictions for non-excluded
        df_model_indices = df[~df['is_model_excluded']].index
        X_with_const = sm.add_constant(X)
        predictions_log = self.model.predict(X_with_const)
        predictions_dollars = np.exp(predictions_log)

        df.loc[df_model_indices, 'predicted_salary'] = predictions_dollars
        df.loc[df_model_indices, 'residual_log'] = y - predictions_log

        # Fallback: cohort median for excluded employees
        df_excluded = df[df['is_model_excluded']]
        for idx in df_excluded.index:
            cohort = df[
                (df['job_level'] == df.loc[idx, 'job_level']) &
                (df['job_function'] == df.loc[idx, 'job_function']) &
                (~df['is_model_excluded'])
            ]
            if len(cohort) > 0:
                df.loc[idx, 'predicted_salary'] = cohort['base_salary'].median()
            else:
                df.loc[idx, 'predicted_salary'] = df.loc[idx, 'base_salary']
            df.loc[idx, 'residual_log'] = 0.0  # No residual for excluded

        # Round predicted pay to whole rupees (fixed-pay concept, no decimals)
        df['predicted_salary'] = df['predicted_salary'].round()
        df['gap_dollars'] = (df['predicted_salary'] - df['base_salary']).round()

        return df

    def _detect_anomalies(self, df: pd.DataFrame, threshold_sigma: float) -> Dict:
        """Flag underpaid employees based on residual threshold"""
        df_model = df[~df['is_model_excluded']].copy()

        std_error = self.model.resid.std()
        threshold = -threshold_sigma * std_error

        # Identify underpaid
        underpaid_mask = df_model['residual_log'] < threshold
        underpaid_employees = df_model[underpaid_mask]

        df['is_underpaid_outlier'] = False
        df.loc[underpaid_employees.index, 'is_underpaid_outlier'] = True

        # Total remediation cost
        remediation_cost = underpaid_employees['gap_dollars'].sum()

        # Clean records for JSON serialization
        underpaid_records = []
        for _, row in underpaid_employees.iterrows():
            record = {
                'employee_id': str(row.get('employee_id', '')),
                'job_title': str(row.get('job_title', '')),
                'base_salary': float(row.get('base_salary', 0)),
                'predicted_salary': float(row.get('predicted_salary', 0)),
                'gap_dollars': float(row.get('gap_dollars', 0))
            }
            underpaid_records.append(record)

        return {
            'underpaid_count': int(len(underpaid_employees)),
            'total_remediation_cost': float(remediation_cost),
            'std_error_residuals': float(std_error),
            'threshold_sigma': float(threshold_sigma),
            'underpaid_employees': underpaid_records
        }

    def _generate_recommendations(self, df: pd.DataFrame, anomalies: Dict) -> Dict:
        """Generate data-driven recommendations based on gap patterns"""
        # Calculate gaps
        controlled_gap = self._get_controlled_gap()
        uncontrolled_gap = self._get_uncontrolled_gap(df)

        recommendations = []
        pattern = None
        cg_pct = abs(controlled_gap * 100)

        # Pattern B: material adjusted gap — equity audit required
        if controlled_gap <= -0.05:
            pattern = 'B'
            recommendations.append({
                'pattern': 'Material Adjusted Pay Gap — Audit Required',
                'severity': 'Critical',
                'message': f'A {cg_pct:.1f}% adjusted pay gap persists between women and men in comparable roles (same grade, tenure, performance, function and location). Immediate pay equity audit and equity adjustment are recommended.',
                'actions': [
                    'Commission a grade-by-grade compensation audit and quantify the total equity adjustment cost',
                    'Recalibrate salary offer guidelines and merit-increase matrices for flagged functions',
                    'Establish a dedicated equity adjustment budget to close like-for-like gaps in the current review cycle',
                    'Publish structured pay bands to constrain future below-range placements',
                ]
            })

        # Moderate: real gap — targeted corrections in next cycle
        elif controlled_gap <= -0.02:
            pattern = 'B-moderate'
            recommendations.append({
                'pattern': 'Targeted Equity Correction Required',
                'severity': 'High',
                'message': f'A {cg_pct:.1f}% adjusted pay gap favours men. The disparity is function-specific rather than organisation-wide — address the at-risk cohorts before the gap widens across review cycles.',
                'actions': [
                    'Prioritise equity corrections in functions with the largest adjusted gaps (see function breakdown)',
                    'Review current-cycle merit increase and promotion decisions in flagged functions',
                    'Set a remediation target: bring every function within ±2% adjusted gap by next review cycle',
                    'Re-run the pay equity analysis post-corrections to confirm gap closure',
                ]
            })

        # Pattern A: representation gap — pipeline intervention needed
        elif uncontrolled_gap <= -0.08 or uncontrolled_gap >= 0.08:
            pattern = 'A'
            recommendations.append({
                'pattern': 'Grade Distribution & Pipeline Gap',
                'severity': 'Medium',
                'message': 'Fixed pay is broadly equitable for comparable roles, but an overall pay gap exists because women and men are distributed differently across grades and functions. The primary lever is pipeline and representation, not pay correction.',
                'actions': [
                    'Analyse promotion velocity and external hire mix by gender and grade',
                    'Build targeted pipelines into higher-paying functions and senior grades',
                    'Implement structured sponsorship and succession planning for under-represented talent',
                    'Track grade distribution and promotion rates by gender alongside pay equity each quarter',
                ]
            })

        # Default: equitable
        else:
            recommendations.append({
                'pattern': 'Pay Equity in Good Standing',
                'severity': 'Low',
                'message': 'The adjusted pay gap is within acceptable range and no material disparity is detected. Maintain the current standard with regular monitoring.',
                'actions': [
                    'Run a formal pay equity review on a quarterly basis to detect early drift',
                    'Monitor promotion velocity and grade distribution by gender each cycle',
                    'Maintain published pay band ranges to reinforce internal equity',
                ]
            })

        return {
            'recommendations': recommendations,
            'pattern_detected': pattern,
            'controlled_gap_pct': controlled_gap * 100,
            'uncontrolled_gap_pct': uncontrolled_gap * 100,
            'total_remediation_cost': anomalies['total_remediation_cost']
        }

    def _named_coefficients(self):
        """Map feature_names to their coefficient and p-value.

        params[0] is the constant; params[1:] align with self.feature_names.
        Returns list of (name, coefficient, p_value) tuples.
        """
        params = np.asarray(self.model.params)
        pvalues = np.asarray(self.model.pvalues)
        result = []
        for i, name in enumerate(self.feature_names):
            param_idx = i + 1  # +1 to skip the constant
            if param_idx < len(params):
                coef = float(params[param_idx])
                pval = float(pvalues[param_idx]) if param_idx < len(pvalues) else 1.0
                result.append((name, coef, pval))
        return result

    def _get_controlled_gap(self) -> float:
        """Extract controlled pay gap from gender coefficient"""
        for name, coef, _ in self._named_coefficients():
            if 'gender' in name.lower():
                return float(np.exp(coef) - 1)
        return 0.0

    def _get_uncontrolled_gap(self, df: pd.DataFrame) -> float:
        """Calculate raw median difference"""
        df_female = df[df['gender'].str.lower().isin(['female', 'f'])]
        df_male = df[df['gender'].str.lower().isin(['male', 'm'])]

        if len(df_female) == 0 or len(df_male) == 0:
            return 0.0

        median_female = df_female['base_salary'].median()
        median_male = df_male['base_salary'].median()

        if median_male == 0:
            return 0.0

        return (median_female / median_male) - 1

    def _get_model_stats(self) -> Dict:
        """Get model performance metrics"""
        return {
            'r_squared': float(self.model.rsquared),
            'adjusted_r_squared': float(self.model.rsquared_adj),
            'residual_std_error': float(self.model.resid.std()),
            'observations': int(self.model.nobs),
            'warning_low_fit': bool(self.model.rsquared < 0.60),
            'recommendation_if_low_fit': 'Model fit is low. Consider adding more data or different parameters.' if self.model.rsquared < 0.60 else 'Model fit is acceptable.'
        }

    def _format_coefficients(self, feature_names: List[str]) -> Dict:
        """Format coefficients for admin approval display"""
        coef_dict = {}

        for param_name, coef_value, p_value in self._named_coefficients():
            significant = p_value < 0.05

            # Plain English interpretation
            pct_change = float((np.exp(float(coef_value)) - 1) * 100)

            if 'job_level' in param_name:
                plain = f"Each level increase adds {pct_change:.2f}% to salary"
            elif 'tenure' in param_name:
                plain = f"Each year of tenure adds {pct_change:.2f}% to salary"
            elif 'performance' in param_name:
                plain = f"Each performance point adds {pct_change:.2f}% to salary"
            elif 'gender' in param_name:
                plain = f"Being {param_name.replace('gender_', '')} is associated with {pct_change:.2f}% salary (controlled)"
            elif 'function' in param_name:
                func = param_name.replace('function_', '')
                plain = f"{func} role pays {pct_change:.2f}% more than baseline"
            elif 'location' in param_name:
                loc = param_name.replace('location_', '')
                plain = f"{loc} location pays {pct_change:.2f}% more than baseline"
            else:
                plain = f"{param_name}: {pct_change:.2f}% impact"

            coef_dict[param_name] = {
                'coefficient': _to_json_serializable(float(coef_value)),
                'plain_english': str(plain),
                'p_value': _to_json_serializable(float(p_value)),
                'significant': bool(significant),
                'status': 'Statistically Significant' if significant else 'Not Significant (p > 0.05)'
            }

        return coef_dict

    def _format_predictions(self, df: pd.DataFrame) -> List[Dict]:
        """Format predictions for output"""
        output = []

        for idx, row in df.iterrows():
            base_sal = row['base_salary']
            pred_sal = row.get('predicted_salary', base_sal)
            gap = row.get('gap_dollars', 0)

            # Handle NaN values
            if pd.isna(base_sal):
                base_sal = 0
            if pd.isna(pred_sal):
                pred_sal = base_sal
            if pd.isna(gap):
                gap = 0

            output.append({
                'employee_id': str(row.get('employee_id', f'EMP{idx}')),
                'job_title': str(row.get('job_title', 'Unknown')),
                'job_function': str(row.get('job_function', 'General')),
                'job_level': str(row.get('job_level', '')),
                'gender': str(row.get('gender', '')),
                'base_salary': int(round(base_sal)),
                'predicted_salary': int(round(pred_sal)),
                'gap_dollars': int(round(gap)),
                'is_underpaid_outlier': bool(row.get('is_underpaid_outlier', False)),
                'is_model_excluded': bool(row.get('is_model_excluded', False))
            })

        return output
