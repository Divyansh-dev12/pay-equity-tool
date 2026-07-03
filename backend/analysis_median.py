"""
Linear (Median) pay-equity model.

Simpler and more transparent than the regression model: every employee is
compared to the MEDIAN fixed pay for their cohort (job_function + job_level).
The median can either be:
  - uploaded by the user (a market/benchmark table), or
  - computed from the uploaded employee data itself.

We then measure how far each person sits from that median, and roll it up by
gender, function and level to expose where pay sits below the fair line.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from analytics import _is_female, _is_male, build_breakdowns


def _round(x) -> int:
    try:
        return int(round(float(x)))
    except (TypeError, ValueError):
        return 0


def run_median_analysis(df: pd.DataFrame,
                        median_table: Optional[pd.DataFrame] = None,
                        salary_col: str = 'base_salary') -> Dict:
    df = df.copy()
    df[salary_col] = pd.to_numeric(df[salary_col], errors='coerce')
    df = df.dropna(subset=[salary_col, 'gender', 'job_function', 'job_level'])
    input_rows = len(df)

    # ---- Establish the median line per cohort (function + level) -------------
    if median_table is not None and len(median_table) > 0:
        source = 'uploaded'
        mt = median_table.copy()
        mt.columns = [c.strip().lower() for c in mt.columns]
        mt = mt.rename(columns={'median': 'median_salary', 'median_pay': 'median_salary'})
        mt['median_salary'] = pd.to_numeric(mt['median_salary'], errors='coerce')
        key = ['job_function', 'job_level']
        df = df.merge(mt[key + ['median_salary']], on=key, how='left')
        # Any cohort missing from the upload falls back to the data median.
        data_median = df.groupby(key)[salary_col].transform('median')
        df['cohort_median'] = df['median_salary'].fillna(data_median)
        df = df.drop(columns=['median_salary'])
    else:
        source = 'computed_from_data'
        df['cohort_median'] = df.groupby(['job_function', 'job_level'])[salary_col].transform('median')

    df['cohort_median'] = df['cohort_median'].round().astype(int)
    df['gap_rupees'] = (df[salary_col] - df['cohort_median']).round().astype(int)
    df['gap_pct'] = np.where(df['cohort_median'] > 0,
                             df['gap_rupees'] / df['cohort_median'] * 100, 0.0)
    df['below_median'] = df['gap_rupees'] < 0

    # ---- Overall gender position vs the median line -------------------------
    fem = df[_is_female(df['gender'])]
    male = df[_is_male(df['gender'])]

    def pos(sub):
        return round(float(sub['gap_pct'].mean()), 2) if len(sub) else 0.0

    def below_pct(sub):
        return round(float(sub['below_median'].mean() * 100), 1) if len(sub) else 0.0

    female_pos, male_pos = pos(fem), pos(male)

    summary = {
        'total_employees': int(len(df)),
        'cohorts': int(df.groupby(['job_function', 'job_level']).ngroups),
        'female_avg_position_pct': female_pos,     # avg % above/below median
        'male_avg_position_pct': male_pos,
        'gender_gap_vs_median_pct': round(female_pos - male_pos, 2),
        'female_below_median_pct': below_pct(fem),
        'male_below_median_pct': below_pct(male),
        'female_count': int(len(fem)),
        'male_count': int(len(male)),
    }

    # ---- By function & by level: female vs male average position -----------
    def dimension_positions(dim: str) -> List[Dict]:
        out = []
        for value, sub in df.groupby(dim):
            f = sub[_is_female(sub['gender'])]
            m = sub[_is_male(sub['gender'])]
            if len(f) == 0 or len(m) == 0:
                continue
            fp, mp = pos(f), pos(m)
            out.append({
                'name': str(value),
                'headcount': int(len(sub)),
                'female_position_pct': fp,
                'male_position_pct': mp,
                'gap_vs_median_pct': round(fp - mp, 2),
                'below_median_count': int(sub['below_median'].sum()),
            })
        out.sort(key=lambda r: r['gap_vs_median_pct'])
        return out

    # ---- Per-employee roster (whole rupees, no decimals) -------------------
    employees = []
    for _, r in df.iterrows():
        employees.append({
            'employee_id': str(r.get('employee_id', '')),
            'job_title': str(r.get('job_title', '')),
            'job_function': str(r['job_function']),
            'job_level': str(r['job_level']),
            'gender': str(r['gender']),
            'base_salary': _round(r[salary_col]),
            'cohort_median': _round(r['cohort_median']),
            'gap_rupees': _round(r['gap_rupees']),
            'gap_pct': round(float(r['gap_pct']), 1),
            'below_median': bool(r['below_median']),
        })

    return {
        'method': 'median',
        'median_source': source,
        'summary': summary,
        'by_function': dimension_positions('job_function'),
        'by_level': dimension_positions('job_level'),
        'breakdowns': build_breakdowns(df, salary_col),
        'employees': employees,
        'data_quality': {
            'input_rows': int(input_rows),
            'analyzed_rows': int(len(df)),
        },
    }
