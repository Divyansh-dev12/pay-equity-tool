"""
Shared breakdown analytics used by both the Regression and Linear (Median) models.

Everything here returns plain JSON-serializable Python types (ints for money,
floats for percentages) so it can go straight into an API response.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


def _is_female(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(['female', 'f'])


def _is_male(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(['male', 'm'])


def gender_summary(df: pd.DataFrame, salary_col: str = 'base_salary') -> Dict:
    """Overall male vs female pay picture."""
    fem = df[_is_female(df['gender'])][salary_col]
    male = df[_is_male(df['gender'])][salary_col]

    med_f = int(fem.median()) if len(fem) else 0
    med_m = int(male.median()) if len(male) else 0
    mean_f = int(fem.mean()) if len(fem) else 0
    mean_m = int(male.mean()) if len(male) else 0

    raw_gap = ((med_f - med_m) / med_m * 100) if med_m else 0.0

    return {
        'female_count': int(len(fem)),
        'male_count': int(len(male)),
        'female_median': med_f,
        'male_median': med_m,
        'female_mean': mean_f,
        'male_mean': mean_m,
        'uncontrolled_gap_pct': round(float(raw_gap), 2),
    }


def _level_adjusted_gap(sub: pd.DataFrame, salary_col: str) -> float:
    """
    Gap between women and men after holding job level constant.

    For each level present with both genders, take the median female-vs-male
    difference, then weight those differences by cohort size. This strips out
    the "women sit in more junior levels" composition effect, leaving the
    like-for-like gap.
    """
    diffs, weights = [], []
    for _, cell in sub.groupby('job_level'):
        f = cell[_is_female(cell['gender'])][salary_col]
        m = cell[_is_male(cell['gender'])][salary_col]
        # Means are far more stable than medians for the small gender groups
        # inside a single function+level cell.
        if len(f) >= 1 and len(m) >= 1 and m.mean() > 0:
            diffs.append((f.mean() - m.mean()) / m.mean())
            weights.append(len(cell))
    if not weights:
        return 0.0
    return float(np.average(diffs, weights=weights) * 100)


def gap_by_dimension(df: pd.DataFrame, dimension: str,
                     salary_col: str = 'base_salary') -> List[Dict]:
    """
    Break the pay gap down by a dimension (e.g. 'job_function' or 'job_level').

    Returns one row per dimension value with:
      - raw (uncontrolled) gap
      - level-adjusted gap (only meaningful for job_function)
      - headcounts and median pay by gender
    Sorted worst-gap-first (most negative = women most underpaid).
    """
    out = []
    for value, sub in df.groupby(dimension):
        f = sub[_is_female(sub['gender'])][salary_col]
        m = sub[_is_male(sub['gender'])][salary_col]
        if len(f) == 0 or len(m) == 0:
            continue

        med_f, med_m = int(f.median()), int(m.median())
        raw_gap = ((med_f - med_m) / med_m * 100) if med_m else 0.0
        adj_gap = (_level_adjusted_gap(sub, salary_col)
                   if dimension == 'job_function' else raw_gap)

        out.append({
            'name': str(value),
            'headcount': int(len(sub)),
            'female_count': int(len(f)),
            'male_count': int(len(m)),
            'female_median': med_f,
            'male_median': med_m,
            'raw_gap_pct': round(float(raw_gap), 2),
            'adjusted_gap_pct': round(float(adj_gap), 2),
        })

    out.sort(key=lambda r: r['adjusted_gap_pct'])
    return out


def rate_function(adjusted_gap_pct: float) -> Dict:
    """
    Turn a function's adjusted gap into a plain-language verdict + status color.
    Convention: negative gap = women paid less.
    """
    g = adjusted_gap_pct
    if g <= -5:
        return {'status': 'Action needed', 'color': 'red',
                'verdict': f'Women paid {abs(g):.1f}% less for comparable work — remediate.'}
    if g <= -2:
        return {'status': 'Watch', 'color': 'amber',
                'verdict': f'A small gap of {abs(g):.1f}% favouring men — monitor.'}
    if g < 2:
        return {'status': 'Equitable', 'color': 'green',
                'verdict': 'Pay is balanced for comparable work — the right approach.'}
    if g < 5:
        return {'status': 'Watch', 'color': 'amber',
                'verdict': f'Women paid {g:.1f}% more — check for over-correction.'}
    return {'status': 'Review', 'color': 'amber',
            'verdict': f'Women paid {g:.1f}% more for comparable work — review.'}


def build_breakdowns(df: pd.DataFrame, salary_col: str = 'base_salary') -> Dict:
    """Assemble all breakdown analytics for the dashboard."""
    by_function = gap_by_dimension(df, 'job_function', salary_col)
    by_level = gap_by_dimension(df, 'job_level', salary_col)

    # Attach a verdict to each function.
    for row in by_function:
        row.update(rate_function(row['adjusted_gap_pct']))

    worst = by_function[0] if by_function else None
    # "Right approach" = the most equitable function (gap closest to zero).
    best = min(by_function, key=lambda r: abs(r['adjusted_gap_pct'])) if by_function else None

    return {
        'gender_summary': gender_summary(df, salary_col),
        'by_function': by_function,
        'by_level': by_level,
        'worst_function': worst,
        'best_function': best,
    }
