"""
Pay Equity Analysis Engine v2 - Multiple Linear Regression Based
Uses statsmodels.OLS for statistical inference with p-values
Implements residual-based anomaly detection
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


@dataclass
class RegressionResult:
    """Container for regression analysis results"""
    model_summary: Dict
    coefficients: Dict
    predictions: Dict
    anomalies: Dict
    recommendations: Dict
    data_quality: Dict
    model_stats: Dict


class PayEquityRegressionAnalyzer:
    """
    Multiple Linear Regression approach to pay equity analysis.

    Core methodology:
    - Log-linear salary model: ln(salary) = β₀ + β₁·level + β₂·tenure + ... + ε
    - Gender coefficient (β_gender) is the controlled pay gap
    - Residual-based anomaly detection (underpaid = residual < -1σ)
    - Statistical significance testing (p-values)
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.model = None
        self.model_results = None
        self.scaler_stats = {}
        self.categorical_mappings = {}

    def run_full_analysis(self,
                         include_parameters: List[str] = None,
                         outlier_threshold_sigma: float = 3.0,
                         underpaid_threshold_sigma: float = 1.0) -> RegressionResult:
        """
        Execute full analysis pipeline.

        Args:
            include_parameters: List of parameter names to include.
                              Default: ['job_level', 'tenure_years', 'performance_rating',
                                       'job_function', 'location']
            outlier_threshold_sigma: # std devs to exclude from model (default 3σ)
            underpaid_threshold_sigma: # std devs to flag as underpaid (default 1σ)
        """
        if include_parameters is None:
            include_parameters = ['job_level', 'tenure_years', 'performance_rating',
                                'job_function', 'location']

        # Step 1: Data Preparation & Validation
        print("Step 1: Data preparation & validation...")
        cleaned_df, data_quality = self._prepare_data()

        # Step 2: Outlier Detection (by job_level segment)
        print("Step 2: Outlier detection...")
        cleaned_df, outliers = self._detect_outliers(cleaned_df, outlier_threshold_sigma)

        # Step 3: Feature Engineering (one-hot encoding)
        print("Step 3: Feature engineering...")
        X, y, feature_names = self._prepare_features(
            cleaned_df,
            include_parameters
        )

        # Step 4: Fit Regression Model
        print("Step 4: Fitting regression model...")
        self.model_results = self._fit_regression(X, y)

        # Step 5: Generate Predictions & Residuals
        print("Step 5: Calculating predictions & residuals...")
        cleaned_df = self._calculate_predictions(cleaned_df, X, y)

        # Step 6: Detect Underpaid Anomalies
        print("Step 6: Detecting underpaid anomalies...")
        anomalies = self._detect_anomalies(
            cleaned_df,
            underpaid_threshold_sigma
        )

        # Step 7: Generate Recommendations
        print("Step 7: Generating recommendations...")
        recommendations = self._generate_recommendations(cleaned_df, anomalies)

        # Step 8: Calculate Summary Metrics
        print("Step 8: Calculating summary metrics...")
        model_stats = self._calculate_model_stats(cleaned_df, anomalies)

        # Package results
        coefficients_dict = self._format_coefficients(
            self.model_results,
            feature_names
        )

        return RegressionResult(
            model_summary=self._get_model_summary_dict(),
            coefficients=coefficients_dict,
            predictions={
                'total_employees': len(cleaned_df),
                'flagged_employees': len(anomalies['underpaid_employees']),
                'remediation_cost': anomalies['total_remediation_cost'],
                'individual_predictions': cleaned_df[[
                    'employee_id', 'base_salary', 'predicted_salary',
                    'gap_dollars', 'is_underpaid_outlier', 'is_model_excluded'
                ]].to_dict('records')
            },
            anomalies=anomalies,
            recommendations=recommendations,
            data_quality=data_quality,
            model_stats=model_stats
        )

    def _prepare_data(self) -> Tuple[pd.DataFrame, Dict]:
        """
        Validate & clean data according to spec.

        Rules:
        - Exclude: missing gender, base_salary, location
        - Replace: missing performance → "No Rating (New Hire)"
        - Replace: missing tenure → "No Tenure Data"
        """
        df = self.df.copy()
        quality_log = {
            'total_rows_input': len(df),
            'exclusions': {},
            'replacements': {}
        }

        # Identify critical missing values
        missing_gender = df['gender'].isnull().sum()
        missing_salary = df['base_salary'].isnull().sum()
        missing_location = df['location'].isnull().sum()

        # Exclude rows with critical missing data
        initial_count = len(df)
        df = df.dropna(subset=['gender', 'base_salary', 'location'])
        excluded_critical = initial_count - len(df)

        quality_log['exclusions']['missing_critical'] = {
            'count': excluded_critical,
            'reason': 'Missing gender, base_salary, or location'
        }

        # Handle performance rating
        missing_perf = df['performance_rating'].isnull().sum()
        df['performance_rating'] = df['performance_rating'].fillna('No Rating (New Hire)')
        quality_log['replacements']['performance_rating'] = {
            'count': missing_perf,
            'replacement': 'No Rating (New Hire)'
        }

        # Handle tenure
        missing_tenure = df['tenure_years'].isnull().sum()
        df['tenure_years'] = df['tenure_years'].fillna('No Tenure Data')
        quality_log['replacements']['tenure_years'] = {
            'count': missing_tenure,
            'replacement': 'No Tenure Data'
        }

        quality_log['total_rows_after_cleaning'] = len(df)

        return df, quality_log

    def _detect_outliers(self, df: pd.DataFrame, threshold_sigma: float = 3.0) -> Tuple[pd.DataFrame, List[str]]:
        """
        Detect outliers by job_level + job_function segment.
        Exclude from model but keep in dataset with flag.
        """
        df['is_model_excluded'] = False
        outlier_ids = []

        # Group by level and function
        for (level, function), group in df.groupby(['job_level', 'job_function']):
            if len(group) < 2:
                continue

            median = group['base_salary'].median()
            std_dev = group['base_salary'].std()

            if std_dev == 0:
                continue

            # Identify outliers (>3σ from group median)
            outlier_mask = np.abs(group['base_salary'] - median) > (threshold_sigma * std_dev)
            outlier_indices = group[outlier_mask].index

            df.loc[outlier_indices, 'is_model_excluded'] = True
            outlier_ids.extend(group.loc[outlier_indices, 'employee_id'].tolist())

        return df, outlier_ids

    def _prepare_features(self, df: pd.DataFrame, include_parameters: List[str]) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """
        Prepare feature matrix X and target vector y.
        - One-hot encode categorical variables (drop first category)
        - Log-transform salary as target
        - Exclude model_excluded rows from regression
        """
        # Filter out excluded rows
        df_model = df[~df['is_model_excluded']].copy()

        # Prepare y (log-transformed salary)
        y = np.log(df_model['base_salary'].astype(float))

        # Prepare X
        features_list = []

        # Numeric features
        numeric_features = {
            'job_level': 'job_level',
            'tenure_years': 'tenure_years',
            'performance_rating': 'performance_rating'
        }

        for param in include_parameters:
            if param == 'job_level' and 'job_level' in include_parameters:
                # Handle job_level as string (L1, L2, etc) or numeric
                job_level_numeric = pd.to_numeric(
                    df_model['job_level'].astype(str).str.replace('L', ''),
                    errors='coerce'
                )
                features_list.append(job_level_numeric)
            elif param == 'tenure_years' and 'tenure_years' in include_parameters:
                # Only include numeric tenure, skip categorical "No Tenure Data"
                tenure_numeric = pd.to_numeric(
                    df_model['tenure_years'],
                    errors='coerce'
                )
                features_list.append(tenure_numeric.fillna(df_model['tenure_years'].median()))
            elif param == 'performance_rating' and 'performance_rating' in include_parameters:
                # Only include numeric performance, skip categorical
                perf_numeric = pd.to_numeric(
                    df_model['performance_rating'],
                    errors='coerce'
                )
                features_list.append(perf_numeric.fillna(df_model['performance_rating'].median()))

        # Categorical features (one-hot, drop first)
        if 'job_function' in include_parameters:
            func_dummies = pd.get_dummies(df_model['job_function'], prefix='function', drop_first=True)
            features_list.extend([func_dummies[col] for col in func_dummies.columns])

        if 'location' in include_parameters:
            loc_dummies = pd.get_dummies(df_model['location'], prefix='location', drop_first=True)
            features_list.extend([loc_dummies[col] for col in loc_dummies.columns])

        if 'gender' in include_parameters:
            gender_dummies = pd.get_dummies(df_model['gender'], prefix='gender', drop_first=True)
            features_list.extend([gender_dummies[col] for col in gender_dummies.columns])

        X = pd.concat(features_list, axis=1)

        # Ensure all values are numeric and handle NaN
        X = X.fillna(X.mean())

        # Ensure X and y have matching indices
        X = X.loc[y.index]

        feature_names = list(X.columns)

        return X, y, feature_names

    def _fit_regression(self, X: pd.DataFrame, y: pd.Series) -> sm.regression.linear_model.RegressionResultsWrapper:
        """
        Fit OLS regression model with statsmodels.
        """
        # Ensure X is fully numeric
        X = X.astype(float)
        y = y.astype(float)

        X_with_const = sm.add_constant(X)
        model = sm.OLS(y, X_with_const)
        results = model.fit()

        return results

    def _calculate_predictions(self, df: pd.DataFrame, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """
        Calculate predicted salary and residuals for all employees.
        """
        df = df.copy()

        # Predictions for non-excluded employees
        df_model = df[~df['is_model_excluded']].copy()
        predictions_log = self.model_results.predict(sm.add_constant(X))
        df.loc[df_model.index, 'predicted_salary'] = np.exp(predictions_log)
        df.loc[df_model.index, 'residual_log'] = y - predictions_log

        # For excluded employees, use cohort average (fallback)
        df_excluded = df[df['is_model_excluded']].copy()
        for idx in df_excluded.index:
            cohort = df[
                (df['job_level'] == df.loc[idx, 'job_level']) &
                (df['job_function'] == df.loc[idx, 'job_function']) &
                (df['location'] == df.loc[idx, 'location']) &
                (~df['is_model_excluded'])
            ]
            if len(cohort) > 0:
                df.loc[idx, 'predicted_salary'] = cohort['base_salary'].median()
            else:
                # Broaden cohort: drop location
                cohort = df[
                    (df['job_level'] == df.loc[idx, 'job_level']) &
                    (df['job_function'] == df.loc[idx, 'job_function']) &
                    (~df['is_model_excluded'])
                ]
                df.loc[idx, 'predicted_salary'] = cohort['base_salary'].median() if len(cohort) > 0 else df.loc[idx, 'base_salary']

        # Calculate gap dollars
        df['gap_dollars'] = df['predicted_salary'] - df['base_salary']

        return df

    def _detect_anomalies(self, df: pd.DataFrame, threshold_sigma: float = 1.0) -> Dict:
        """
        Flag employees as underpaid if residual < -threshold_sigma * std_error.
        """
        std_error = self.model_results.resid.std()
        threshold = -threshold_sigma * std_error

        # Only flag non-excluded employees with regression residuals
        df_model = df[~df['is_model_excluded']].copy()
        underpaid_mask = df_model['residual_log'] < threshold

        underpaid_employees = df.loc[df_model[underpaid_mask].index].copy()
        underpaid_employees['is_underpaid_outlier'] = True

        # Mark all as underpaid for dashboard
        df['is_underpaid_outlier'] = False
        df.loc[underpaid_employees.index, 'is_underpaid_outlier'] = True

        # Calculate remediation cost
        total_cost = underpaid_employees['gap_dollars'].sum()

        return {
            'underpaid_employees': underpaid_employees[[
                'employee_id', 'job_title', 'base_salary', 'predicted_salary',
                'gap_dollars', 'is_model_excluded'
            ]].to_dict('records'),
            'underpaid_count': len(underpaid_employees),
            'total_remediation_cost': float(total_cost),
            'threshold_sigma': threshold_sigma,
            'std_error_residuals': float(std_error)
        }

    def _generate_recommendations(self, df: pd.DataFrame, anomalies: Dict) -> Dict:
        """
        Generate data-driven recommendations based on gap patterns.
        """
        # Calculate controlled and uncontrolled gaps
        controlled_gap = self._get_controlled_gap()
        uncontrolled_gap = self._get_uncontrolled_gap(df)

        recommendations = []
        pattern_detected = None

        # Pattern A: Pipeline/Representation Issue
        if controlled_gap <= -0.03 and uncontrolled_gap >= 0.10:
            pattern_detected = 'A'
            recommendations.append({
                'pattern': 'Pipeline & Representation Issue',
                'severity': 'High',
                'message': 'Pay equity is healthy for individuals doing equivalent work. However, a significant overall wage gap exists because diverse talent is concentrated in lower-paying, junior brackets. Focus initiatives on diverse hiring and promotion velocity for senior roles (L4+).',
                'actions': [
                    'Review hiring practices for senior roles',
                    'Analyze promotion velocity by demographic',
                    'Implement structured mentorship for underrepresented groups'
                ]
            })

        # Pattern B: Pay Discrimination Issue
        if controlled_gap <= -0.05:
            pattern_detected = 'B'
            recommendations.append({
                'pattern': 'Pay Discrimination Issue',
                'severity': 'Critical',
                'message': 'Significant pay variation detected between demographic groups performing identical roles at the same level. This indicates potential compensation bias at the point of hire or merit cycle. Recommendation: Audit specific department compensation decisions and deploy remediation budget.',
                'actions': [
                    'Conduct immediate compensation audit',
                    'Review hiring offer calibration process',
                    'Implement pay equity remediation',
                    'Establish transparent pay bands'
                ]
            })

        # Generic recommendation if no patterns detected
        if not recommendations:
            recommendations.append({
                'pattern': 'Standard Audit',
                'severity': 'Medium',
                'message': 'Pay equity baseline established. Monitor quarterly for deviations.',
                'actions': [
                    'Establish regular audit schedule',
                    'Implement transparent pay bands',
                    'Track promotion velocity by demographic'
                ]
            })

        return {
            'recommendations': recommendations,
            'controlled_gap_pct': controlled_gap * 100,
            'uncontrolled_gap_pct': uncontrolled_gap * 100,
            'pattern_detected': pattern_detected,
            'total_remediation_cost': anomalies['total_remediation_cost']
        }

    def _get_controlled_gap(self) -> float:
        """
        Extract controlled pay gap from gender_Female coefficient.
        Formula: (e^β - 1) × 100
        """
        params = self.model_results.params

        # Find gender_Female coefficient
        for param_name, value in params.items():
            if 'gender_Female' in param_name:
                return np.exp(value) - 1

        return 0.0

    def _get_uncontrolled_gap(self, df: pd.DataFrame) -> float:
        """
        Calculate uncontrolled gap from raw medians.
        Formula: (median_female / median_male - 1)
        """
        df_female = df[df['gender'].str.lower() == 'female']
        df_male = df[df['gender'].str.lower() == 'male']

        if len(df_female) == 0 or len(df_male) == 0:
            return 0.0

        median_female = df_female['base_salary'].median()
        median_male = df_male['base_salary'].median()

        return (median_female / median_male) - 1

    def _calculate_model_stats(self, df: pd.DataFrame, anomalies: Dict) -> Dict:
        """
        Calculate model performance metrics for dashboard.
        """
        return {
            'r_squared': float(self.model_results.rsquared),
            'adjusted_r_squared': float(self.model_results.rsquared_adj),
            'residual_std_error': float(self.model_results.resid.std()),
            'observations': int(self.model_results.nobs),
            'model_excludes_outliers': int(df['is_model_excluded'].sum()),
            'warning_low_fit': self.model_results.rsquared < 0.60,
            'recommendation_if_low_fit': 'Low model fit. Consider adding more data, cleaner parameters, or removing columns with high missing data.' if self.model_results.rsquared < 0.60 else ''
        }

    def _format_coefficients(self, results, feature_names: List[str]) -> Dict:
        """
        Format regression coefficients for admin approval screen.
        Includes p-values and significance flags.
        """
        coefficients_dict = {}

        for idx, (param_name, coef_value) in enumerate(results.params.items()):
            # Skip constant term or handle separately
            if param_name == 'const':
                continue

            p_value = results.pvalues[idx]
            significant = p_value < 0.05

            # Translate to plain English
            plain_english = self._coefficient_to_plain_english(param_name, coef_value)

            coefficients_dict[param_name] = {
                'coefficient': float(coef_value),
                'plain_english': plain_english,
                'p_value': float(p_value),
                'significant': significant,
                'status': 'Statistically Significant' if significant else 'Statistically Insignificant (p > 0.05)'
            }

        return coefficients_dict

    def _coefficient_to_plain_english(self, param_name: str, coef_value: float) -> str:
        """
        Convert coefficient to human-readable interpretation.
        """
        pct_change = (np.exp(coef_value) - 1) * 100

        if 'tenure' in param_name.lower():
            return f"Each year of tenure adds {pct_change:.2f}% to salary"
        elif 'performance' in param_name.lower():
            return f"Each performance point adds {pct_change:.2f}% to salary"
        elif 'gender_Female' in param_name:
            return f"Being Female is associated with {pct_change:.2f}% salary (controlled)"
        elif 'function_' in param_name:
            func_name = param_name.replace('function_', '').replace('_', ' ').title()
            return f"{func_name} roles pay {pct_change:.2f}% more than baseline function"
        elif 'location_' in param_name:
            loc_name = param_name.replace('location_', '').replace('_', ' ').title()
            return f"{loc_name} location pays {pct_change:.2f}% more than baseline location"
        else:
            return f"{param_name}: {pct_change:.2f}% impact"

    def _get_model_summary_dict(self) -> Dict:
        """
        Extract key model metrics for display.
        """
        return {
            'r_squared': float(self.model_results.rsquared),
            'adjusted_r_squared': float(self.model_results.rsquared_adj),
            'observations': int(self.model_results.nobs),
            'formula': 'ln(base_salary) ~ job_level + tenure_years + performance_rating + job_function + location + gender'
        }
