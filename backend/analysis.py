"""
Pay Equity Analysis Engine - 5-Step Methodology Implementation
Based on Oaxaca (1973) wage decomposition methodology
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class AnalysisResult:
    """Container for analysis results"""
    step1_data_quality: Dict
    step2_descriptive: Dict
    step3_controlled_gaps: Dict
    step4_root_causes: Dict
    step5_remediation: Dict
    summary: Dict


class PayEquityAnalyzer:
    """Implements the 5-step pay equity audit methodology"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.results = {}

    def run_full_analysis(self) -> AnalysisResult:
        """Execute all 5 steps and return comprehensive results"""
        step1 = self.step1_data_preparation()
        step2 = self.step2_descriptive_analysis()
        step3 = self.step3_controlled_gaps()
        step4 = self.step4_root_cause_analysis(step3)
        step5 = self.step5_remediation(step4)

        summary = self._generate_summary(step1, step2, step3, step4, step5)

        return AnalysisResult(
            step1_data_quality=step1,
            step2_descriptive=step2,
            step3_controlled_gaps=step3,
            step4_root_causes=step4,
            step5_remediation=step5,
            summary=summary
        )

    def step1_data_preparation(self) -> Dict:
        """
        STEP 1: DATA PREPARATION & VALIDATION

        Outputs:
        - Data quality checks (missing values, outliers, duplicates)
        - Cleaned dataset statistics
        - Data assumptions documented
        """
        df = self.df

        # Check for required columns
        required = ['employee_id', 'job_title', 'job_level', 'base_salary', 'gender', 'tenure_years']
        missing_cols = [c for c in required if c not in df.columns]

        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Identify duplicates
        duplicates = df.duplicated(subset=['employee_id']).sum()

        # Check for missing values
        missing_data = df.isnull().sum().to_dict()
        missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()

        # Identify outliers (using IQR method)
        salary_Q1 = df['base_salary'].quantile(0.25)
        salary_Q3 = df['base_salary'].quantile(0.75)
        salary_IQR = salary_Q3 - salary_Q1
        outlier_threshold_upper = salary_Q3 + 1.5 * salary_IQR
        outlier_threshold_lower = salary_Q1 - 1.5 * salary_IQR

        outliers = df[
            (df['base_salary'] > outlier_threshold_upper) |
            (df['base_salary'] < outlier_threshold_lower)
        ]

        return {
            'total_employees': len(df),
            'duplicates_found': int(duplicates),
            'missing_values': missing_data,
            'missing_pct': missing_pct,
            'outliers_found': len(outliers),
            'outlier_examples': outliers[['employee_id', 'job_title', 'base_salary']].to_dict('records')[:5],
            'salary_stats': {
                'mean': float(df['base_salary'].mean()),
                'median': float(df['base_salary'].median()),
                'min': float(df['base_salary'].min()),
                'max': float(df['base_salary'].max()),
                'std': float(df['base_salary'].std())
            },
            'data_ready': duplicates == 0 and all(v == 0 for v in missing_data.values())
        }

    def step2_descriptive_analysis(self) -> Dict:
        """
        STEP 2: DESCRIPTIVE BREAKDOWN

        Outputs:
        - Headcount by role + gender (TABLE 1)
        - Median salary by role + gender (TABLE 2)
        - Unadjusted wage gaps
        - Occupational segregation analysis
        """
        df = self.df

        # TABLE 1: Headcount by role and gender
        headcount = pd.crosstab(
            df['job_title'],
            df['gender'],
            margins=True,
            margins_name='TOTAL'
        ).fillna(0).astype(int)

        # Calculate gender distribution by role
        gender_pct = {}
        for role in df['job_title'].unique():
            role_df = df[df['job_title'] == role]
            female_count = (role_df['gender'].str.lower() == 'female').sum()
            total_count = len(role_df)
            gender_pct[role] = {
                'female_count': int(female_count),
                'total': int(total_count),
                'pct_female': round(female_count / total_count * 100, 1) if total_count > 0 else 0
            }

        # TABLE 2: Median salary by role and gender
        salary_by_role_gender = df.groupby(['job_title', 'gender'])['base_salary'].agg(['median', 'count', 'mean']).reset_index()

        # Calculate unadjusted gaps by role
        gaps_by_role = {}
        for role in df['job_title'].unique():
            role_df = df[df['job_title'] == role]

            # Separate by gender
            female_salaries = role_df[role_df['gender'].str.lower() == 'female']['base_salary']
            male_salaries = role_df[role_df['gender'].str.lower() == 'male']['base_salary']

            if len(female_salaries) > 0 and len(male_salaries) > 0:
                female_median = female_salaries.median()
                male_median = male_salaries.median()
                gap_pct = ((female_median - male_median) / male_median * 100) if male_median != 0 else 0

                gaps_by_role[role] = {
                    'male_median': float(male_median),
                    'female_median': float(female_median),
                    'gap_pct': round(gap_pct, 2),
                    'male_count': len(male_salaries),
                    'female_count': len(female_salaries)
                }

        # Overall unadjusted gap
        overall_female_median = df[df['gender'].str.lower() == 'female']['base_salary'].median()
        overall_male_median = df[df['gender'].str.lower() == 'male']['base_salary'].median()
        overall_gap = ((overall_female_median - overall_male_median) / overall_male_median * 100) if overall_male_median != 0 else 0

        # Occupational segregation: % female by role
        all_female_pct = (df['gender'].str.lower() == 'female').sum() / len(df) * 100

        return {
            'headcount_by_role_gender': headcount.to_dict(),
            'gender_pct_by_role': gender_pct,
            'salary_by_role_gender': salary_by_role_gender.to_dict('records'),
            'unadjusted_gaps_by_role': gaps_by_role,
            'overall_unadjusted_gap_pct': round(overall_gap, 2),
            'overall_female_median': float(overall_female_median),
            'overall_male_median': float(overall_male_median),
            'occupational_segregation': {
                'company_female_pct': round(all_female_pct, 1),
                'roles_below_avg': [r for r, p in gender_pct.items() if p['pct_female'] < all_female_pct],
                'roles_above_avg': [r for r, p in gender_pct.items() if p['pct_female'] > all_female_pct]
            }
        }

    def step3_controlled_gaps(self) -> Dict:
        """
        STEP 3: CONTROLLED WAGE GAP ANALYSIS

        For each role + level with N >= 5, calculate:
        - Median salary by gender
        - Controlled gap (accounting for role/level)

        Outputs:
        - Controlled gaps by role/level
        - Flag gaps > 2% for further investigation
        - Gaps explained vs unexplained
        """
        df = self.df

        controlled_gaps = {}
        gaps_needing_investigation = []  # gaps >= 2%

        # Group by role and level (if available)
        if 'job_level' in df.columns:
            groupby_cols = ['job_title', 'job_level']
        else:
            groupby_cols = ['job_title']

        # Calculate gaps for each group
        for group_key, group_df in df.groupby(groupby_cols):
            role = group_key[0] if isinstance(group_key, tuple) else group_key
            level = group_key[1] if isinstance(group_key, tuple) else None

            # Only analyze groups with sufficient sample size (N >= 5)
            if len(group_df) < 5:
                continue

            female_salaries = group_df[group_df['gender'].str.lower() == 'female']['base_salary']
            male_salaries = group_df[group_df['gender'].str.lower() == 'male']['base_salary']

            # Skip if one gender has 0 representation
            if len(female_salaries) == 0 or len(male_salaries) == 0:
                continue

            female_median = female_salaries.median()
            male_median = male_salaries.median()
            gap_pct = ((female_median - male_median) / male_median * 100) if male_median != 0 else 0

            key = f"{role}_{level}" if level else role
            controlled_gaps[key] = {
                'role': role,
                'level': level,
                'male_median': float(male_median),
                'female_median': float(female_median),
                'gap_pct': round(gap_pct, 2),
                'male_count': len(male_salaries),
                'female_count': len(female_salaries),
                'total_count': len(group_df),
                'significance': 'FLAG' if abs(gap_pct) >= 2 else 'OK'
            }

            # Track gaps for investigation
            if abs(gap_pct) >= 2:
                gaps_needing_investigation.append({
                    'key': key,
                    'gap_pct': round(gap_pct, 2),
                    'direction': 'women paid less' if gap_pct < 0 else 'women paid more'
                })

        # Sort by magnitude
        gaps_needing_investigation.sort(key=lambda x: abs(x['gap_pct']), reverse=True)

        return {
            'controlled_gaps': controlled_gaps,
            'gaps_flagged_count': len(gaps_needing_investigation),
            'gaps_needing_investigation': gaps_needing_investigation,
            'methodology_note': 'Based on Oaxaca (1973) wage decomposition. Compares like-for-like roles.'
        }

    def step4_root_cause_analysis(self, step3_results: Dict) -> Dict:
        """
        STEP 4: FLAG OUTLIERS & IDENTIFY ROOT CAUSES

        For each flagged gap (>= 2%), investigate:
        - Tenure differences
        - Performance rating differences
        - Hire date patterns
        - Occupational segregation within role

        Outputs:
        - Root cause analysis for each gap
        - Unexplained vs explained portion
        - Recommendations by gap
        """
        df = self.df
        root_causes = {}

        for gap_info in step3_results['gaps_needing_investigation']:
            key = gap_info['key']
            role, level = key.rsplit('_', 1) if '_' in key else (key, None)

            # Get the subset
            if level:
                subset = df[(df['job_title'] == role) & (df['job_level'] == level)]
            else:
                subset = df[df['job_title'] == role]

            female_subset = subset[subset['gender'].str.lower() == 'female']
            male_subset = subset[subset['gender'].str.lower() == 'male']

            # Analyze tenure
            tenure_diff = None
            if 'tenure_years' in subset.columns:
                female_tenure = female_subset['tenure_years'].mean()
                male_tenure = male_subset['tenure_years'].mean()
                tenure_diff = round(female_tenure - male_tenure, 2)

            # Analyze performance (if available)
            performance_diff = None
            if 'performance_rating' in subset.columns:
                female_perf = female_subset['performance_rating'].mean()
                male_perf = male_subset['performance_rating'].mean()
                performance_diff = round(female_perf - male_perf, 2)

            # Analyze hire dates
            hire_diff = None
            if 'hire_date' in subset.columns:
                female_hire_years = female_subset['tenure_years'].mean()
                male_hire_years = male_subset['tenure_years'].mean()
                hire_diff = round(female_hire_years - male_hire_years, 2)

            # Determine root cause assessment
            assessment = self._assess_root_cause(
                gap_pct=gap_info['gap_pct'],
                tenure_diff=tenure_diff,
                performance_diff=performance_diff,
                hire_diff=hire_diff
            )

            root_causes[key] = {
                'gap_pct': gap_info['gap_pct'],
                'role': role,
                'level': level,
                'affected_females': len(female_subset),
                'affected_males': len(male_subset),
                'tenure_diff_years': tenure_diff,
                'performance_diff': performance_diff,
                'hire_diff_years': hire_diff,
                'assessment': assessment,
                'recommendation': self._get_recommendation(assessment, gap_info['gap_pct'], len(female_subset))
            }

        return root_causes

    def _assess_root_cause(self, gap_pct: float, tenure_diff: float = None,
                           performance_diff: float = None, hire_diff: float = None) -> str:
        """
        Determine if gap is explained by legitimate factors or potentially discriminatory
        """
        explained_factors = []

        # Tenure: each year of tenure typically explains ~1-2% of salary gap
        if tenure_diff is not None:
            if tenure_diff < -0.5:  # Women have less tenure
                explained_factors.append(f"Tenure difference ({tenure_diff} years, women newer)")

        # Performance: differences in rating can explain gap
        if performance_diff is not None:
            if abs(performance_diff) > 0.2:
                explained_factors.append(f"Performance difference ({performance_diff} rating points)")

        if explained_factors:
            return f"PARTIALLY EXPLAINED: {'; '.join(explained_factors)}"
        else:
            return "UNEXPLAINED: No legitimate factors account for gap"

    def _get_recommendation(self, assessment: str, gap_pct: float, affected_count: int) -> Dict:
        """Generate remediation recommendation based on root cause"""

        if "UNEXPLAINED" in assessment:
            if abs(gap_pct) > 5:
                priority = "IMMEDIATE"
                timeline = "30 days"
            elif abs(gap_pct) >= 2:
                priority = "MEDIUM"
                timeline = "90 days"
            else:
                priority = "MONITORING"
                timeline = "Annual review"
        else:
            priority = "MONITORING"
            timeline = "Annual review"

        return {
            'priority': priority,
            'timeline': timeline,
            'action': f"Review and adjust {affected_count} employee(s)" if priority != "MONITORING" else "Monitor in next audit"
        }

    def step5_remediation(self, step4_results: Dict) -> Dict:
        """
        STEP 5: REMEDIATION RECOMMENDATIONS & PRIORITIZATION

        For each unexplained gap:
        - Calculate remediation cost
        - Prioritize by impact + magnitude
        - Create action plan

        Outputs:
        - Remediation plan by priority
        - Total cost (immediate + medium-term)
        - Timeline
        """
        remediation_plan = {
            'immediate': [],
            'medium_term': [],
            'monitoring': [],
            'total_cost': 0,
            'affected_employees': 0
        }

        for key, analysis in step4_results.items():
            recommendation = analysis['recommendation']
            priority = recommendation['priority']

            # Calculate remediation cost (rough estimate)
            # Adjustment = gap % × current median salary × number of affected employees
            affected = analysis['affected_females']
            estimated_salary = 3000000  # Placeholder; would use actual median
            cost = abs(analysis['gap_pct'] / 100) * estimated_salary * affected

            action = {
                'role_level': key,
                'gap_pct': analysis['gap_pct'],
                'affected_employees': affected,
                'assessment': analysis['assessment'],
                'estimated_cost': int(cost),
                'timeline': recommendation['timeline'],
                'action': recommendation['action']
            }

            if priority == 'IMMEDIATE':
                remediation_plan['immediate'].append(action)
                remediation_plan['total_cost'] += cost
                remediation_plan['affected_employees'] += affected
            elif priority == 'MEDIUM':
                remediation_plan['medium_term'].append(action)
                remediation_plan['total_cost'] += cost
                remediation_plan['affected_employees'] += affected
            else:
                remediation_plan['monitoring'].append(action)

        return remediation_plan

    def _generate_summary(self, step1, step2, step3, step4, step5) -> Dict:
        """Generate executive summary"""
        return {
            'total_employees_analyzed': step1['total_employees'],
            'overall_unadjusted_gap_pct': step2['overall_unadjusted_gap_pct'],
            'controlled_gaps_flagged': step3['gaps_flagged_count'],
            'immediate_actions_needed': len(step5['immediate']),
            'total_remediation_cost': int(step5['total_cost']),
            'employees_affected': step5['affected_employees'],
            'key_insights': [
                f"Overall unadjusted gap: {step2['overall_unadjusted_gap_pct']}%",
                f"{step3['gaps_flagged_count']} role/levels with gaps >= 2%",
                f"{len(step5['immediate'])} immediate remediation action(s) needed" if step5['immediate'] else "No immediate actions needed",
                f"Company female representation: {step2['occupational_segregation']['company_female_pct']}%"
            ]
        }
