"""
Synthetic Indian compensation dataset for the Pay Equity tool.

Design goals:
- Fixed pay (annual fixed CTC) in whole rupees — no decimals.
- Multiple, DELIBERATELY DIFFERENT scenarios per function so the dashboard
  has something to say:
    * some functions are equitable (the "right approach")
    * some pay men more (a real gap to remediate)
    * at least one pays women more (so not everyone is "underpaid")
- Natural salary noise so regression residuals fall on BOTH sides of the
  prediction (some people paid above model, some below).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Annual fixed-pay bands by level, in INR lakhs (LPA). Converted to rupees below.
LEVEL_BANDS_LPA = {
    'L1': (6, 10),
    'L2': (11, 18),
    'L3': (20, 32),
    'L4': (38, 55),
    'L5': (60, 90),
}

# Per-function configuration.
#   multiplier   : pay premium/discount for the function
#   female_gap   : fraction women are paid BELOW comparable men
#                  (0 = fair, +ve = women underpaid, -ve = women paid more)
#   pct_female   : share of women in the function
#   headcount    : number of employees to generate
FUNCTIONS = {
    'Engineering':        {'multiplier': 1.15, 'female_gap':  0.065, 'pct_female': 0.30, 'headcount': 60},
    'Product Management': {'multiplier': 1.25, 'female_gap':  0.005, 'pct_female': 0.44, 'headcount': 40},
    'Data Science':       {'multiplier': 1.20, 'female_gap':  0.010, 'pct_female': 0.42, 'headcount': 40},
    'Sales':              {'multiplier': 1.05, 'female_gap':  0.120, 'pct_female': 0.34, 'headcount': 50},
    'Finance':            {'multiplier': 1.00, 'female_gap': -0.040, 'pct_female': 0.52, 'headcount': 40},
    'Marketing':          {'multiplier': 0.98, 'female_gap':  0.030, 'pct_female': 0.55, 'headcount': 36},
    'Human Resources':    {'multiplier': 0.92, 'female_gap':  0.000, 'pct_female': 0.62, 'headcount': 34},
    'Operations':         {'multiplier': 0.95, 'female_gap':  0.050, 'pct_female': 0.38, 'headcount': 40},
}

LEVEL_WEIGHTS = {'L1': 0.24, 'L2': 0.30, 'L3': 0.26, 'L4': 0.14, 'L5': 0.06}
LOCATIONS = ['Bangalore', 'Delhi NCR', 'Mumbai', 'Hyderabad', 'Pune']
LOCATION_MULT = {'Bangalore': 1.08, 'Delhi NCR': 1.05, 'Mumbai': 1.06, 'Hyderabad': 1.00, 'Pune': 0.98}


def _round_pay(value: float) -> int:
    """Round fixed pay to the nearest 1,000 rupees (whole number, no decimals)."""
    return int(round(value / 1000.0) * 1000)


def generate_sample_dataset(random_seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)

    rows = []
    emp_id = 1
    hire_base = datetime(2018, 1, 1)

    for function, cfg in FUNCTIONS.items():
        n = cfg['headcount']
        # Split headcount across levels, then place BOTH genders at every level
        # so within-cohort (function+level) comparisons are meaningful.
        for level, weight in LEVEL_WEIGHTS.items():
            n_level = max(2, int(round(n * weight)))
            n_female = int(round(n_level * cfg['pct_female']))
            n_male = n_level - n_female
            genders = ['Female'] * n_female + ['Male'] * n_male
            rng.shuffle(genders)

            lo, hi = LEVEL_BANDS_LPA[level]
            mid = (lo + hi) / 2
            for gender in genders:
                # Anchor to the level midpoint (with a little spread) so LEVEL is
                # the dominant explainable driver. A wide uniform(lo,hi) draw would
                # be pure noise that hides the gender effect and lowers R².
                base_lpa = mid * float(rng.normal(1.0, 0.04)) * cfg['multiplier']

                tenure = round(float(rng.uniform(0.5, 9.0)), 1)
                perf = float(np.clip(rng.normal(3.6, 0.7), 1, 5))
                location = LOCATIONS[rng.integers(0, len(LOCATIONS))]

                # Legitimate, explainable drivers.
                tenure_factor = 1 + tenure * 0.022
                perf_factor = 1 + (perf - 3.0) * 0.03
                loc_factor = LOCATION_MULT[location]

                pay = base_lpa * 100000 * tenure_factor * perf_factor * loc_factor

                # Unexplained gender effect (the thing we want to detect).
                if gender == 'Female':
                    pay *= (1 - cfg['female_gap'])

                # Idiosyncratic noise → residuals land on both sides of prediction.
                pay *= rng.normal(1.0, 0.055)

                fixed_pay = _round_pay(pay)
                bonus = _round_pay(fixed_pay * rng.uniform(0.10, 0.30))
                hire_date = hire_base + timedelta(days=int((9.0 - tenure) * 365))

                rows.append({
                    'employee_id': f'EMP{emp_id:04d}',
                    'job_title': f'{function} {level}',
                    'job_function': function,
                    'job_level': level,
                    'department': function,
                    'location': location,
                    'base_salary': fixed_pay,      # annual FIXED pay, whole rupees
                    'bonus': bonus,
                    'tenure_years': tenure,
                    'gender': gender,
                    'hire_date': hire_date.strftime('%Y-%m-%d'),
                    'performance_rating': round(perf, 1),
                })
                emp_id += 1

    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=random_seed).reset_index(drop=True)


def generate_median_reference(random_seed: int = 42) -> pd.DataFrame:
    """
    A sample MEDIAN benchmark table (function + level -> market median fixed pay).

    This is the kind of file a comp & ben professional would upload for the
    Linear (Median) model. Medians here are the gender-neutral band midpoints,
    so the linear model measures how far each cohort sits from a fair market line.
    """
    rows = []
    for function, cfg in FUNCTIONS.items():
        for level, (lo, hi) in LEVEL_BANDS_LPA.items():
            mid_lpa = (lo + hi) / 2 * cfg['multiplier']
            rows.append({
                'job_function': function,
                'job_level': level,
                'median_salary': _round_pay(mid_lpa * 100000),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_dataset()
    print(f"Generated {len(df)} employees across {df['job_function'].nunique()} functions")
    print("\nMedian FIXED pay by function and gender (INR):")
    piv = df.pivot_table(index='job_function', columns='gender',
                         values='base_salary', aggfunc='median')
    piv['gap_%'] = ((piv['Female'] - piv['Male']) / piv['Male'] * 100).round(1)
    print(piv.astype({'Female': int, 'Male': int}))
