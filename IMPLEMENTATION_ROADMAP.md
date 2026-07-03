# Pay Equity Regression Tool - Implementation Roadmap

## Technical Specification Summary

You've provided a **complete, sophisticated technical specification** for a regression-based pay equity tool. This document summarizes what was specified so you can build or adapt it with your development team.

---

## Core Architecture

### 1. **Multiple Linear Regression Model**
- **Formula:** `ln(base_salary) = β₀ + β₁·job_level + β₂·tenure_years + β₃·performance_rating + β₄·job_function + β₅·location + β_gender·gender_Female + ε`
- **Library:** `statsmodels.api.OLS` (not scikit-learn, for p-values & statistical inference)
- **Transformation:** Log-linear (salary in natural log scale, predictions back-converted with `np.exp()`)

### 2. **Data Validation Pipeline**

| Parameter | If Missing | Action |
|-----------|-----------|--------|
| gender, base_salary, location | Empty | **Exclude row** |
| performance_rating | No rating | Replace: `"No Rating (New Hire)"` |
| tenure_years | No data | Replace: `"No Tenure Data"` |

### 3. **Outlier Detection (Pre-Regression)**
- **Segment by:** `job_level` + `job_function`
- **Threshold:** > 3σ from segment median
- **Action:** Flag `is_model_excluded = True` (keep in dataset, don't use in regression)

### 4. **Feature Engineering**
- **Numeric:** job_level (L1→1, L2→2), tenure_years, performance_rating
- **Categorical:** One-hot encoding (drop first category to avoid multicollinearity)
  - job_function → function_PM, function_Design, function_Finance, etc.
  - location → location_US, location_India, etc.
  - gender → gender_Female (baseline = Male)

### 5. **Regression Fitting**
```python
import statsmodels.api as sm

y = np.log(df['base_salary'])  # Log-transform target
X = [numeric_features, one_hot_encoded_categoricals]
X_const = sm.add_constant(X)

model = sm.OLS(y, X_const).fit()  # Fit model
predictions_log = model.predict(X_const)  # In log scale
predictions = np.exp(predictions_log)  # Back-convert to dollars
```

### 6. **Statistical Inference**
- **p-values** available from `model.rsquared`, `model.pvalues` for each coefficient
- **Threshold:** Highlight `p > 0.05` as "Statistically Insignificant" or "Data Sample Too Small"

### 7. **Residual-Based Anomaly Detection**
- **Threshold:** Configurable slider (1σ, 1.5σ, 2σ)
- **Calculation:** `std_error_residuals = model.resid.std()`
- **Flag:** `residual < -threshold_sigma * std_error`
- **Example:** If σ_ε = 0.06 and threshold = 1σ, flag employees with `residual < -0.06`

### 8. **Gap Definitions**

**Controlled Gap (from regression):**
```
Controlled Gap % = (e^(β_gender_Female) - 1) × 100
```
- Example: β = -0.031 → e^(-0.031) - 1 = -3.05% ≈ -3.1%

**Uncontrolled Gap (raw medians):**
```
Uncontrolled Gap % = (Median_Female / Median_Male - 1) × 100
```

### 9. **Fallback Strategy (Cohort Average)**
If regression weights are rejected or model fit is poor:
1. Group by `job_level` + `job_function` + `location`
2. Calculate median salary per cohort
3. Compare individual salary to cohort median
4. Badge: `[Fallback: Broad Cohort Match due to N=1]`

### 10. **Recommendation Patterns**

**Pattern A (Pipeline/Representation Issue):**
```
if controlled_gap <= -3% AND uncontrolled_gap >= 10%:
  "Pay equity is healthy within roles, but diverse talent 
   is concentrated in lower-paying positions. Focus on 
   diverse hiring & promotion for senior roles."
```

**Pattern B (Pay Discrimination):**
```
if controlled_gap <= -5%:
  "Significant pay bias detected within identical roles. 
   Audit compensation decisions and deploy remediation."
```

---

## Frontend Dashboard Structure

### 1. **Macro Overview (Executives)**
- Uncontrolled Gap % (raw difference)
- Controlled Gap % (regression-adjusted)
- Charts by gender, function, location
- Model R² (with warning if < 0.60)

### 2. **Micro Remediation (HR Compensation)**
Interactive table: `employee_id | job_title | actual_salary | predicted_salary | gap_dollars | priority`
- Sorted by gap_dollars descending
- Only shows flagged employees (`is_underpaid_outlier = True`)
- Badges: `[Excluded: Outlier]` if `is_model_excluded = True`

### 3. **Data Quality Report**
- Rows input → Rows excluded (with reasons) → Rows analyzed
- Model R² (warning if < 0.60)
- Dynamic message: "Low model fit (R² = 0.52). Consider adding performance ratings or removing columns with high missing data."

### 4. **Admin Approval Screen**
Table: `Parameter | Coefficient | Plain English | P-Value | Significant? | Uncheck`

Example:
| Parameter | Coefficient | Plain English | P-Value | Status | Action |
|-----------|------------|---------------|---------|--------|--------|
| tenure_years | 0.042 | +4.2% per year | 0.001 | ✓ Sig. | ✓ Approve |
| gender_Female | -0.031 | -3.1% (controlled) | 0.156 | ✗ Insig. | ⚠ Review |

- **Uncheck** a parameter → triggers async recalculation → refreshes all outputs

### 5. **Remediation & Recommendations**
- Data-driven insights (Pattern A or B)
- Total cost to fix: `Σ (predicted_salary - actual_salary)` for flagged employees
- Action items prioritized by impact

---

## Configuration Options

1. **Column Selector:** Checkboxes to toggle parameters (job_level, tenure_years, performance_rating, job_function, location, gender)
2. **Outlier Threshold:** Slider (1σ, 1.5σ, 2σ or custom)
3. **Underpaid Threshold:** Slider (1σ, 1.5σ, 2σ)
4. **Cohort Fallback:** Auto-detect when N < 2 in specific cohort, broaden to next tier

---

## Cost Calculation

**Total Remediation Cost (Year 1):**
```
Cost = Σ (predicted_salary - actual_salary) for all flagged employees
```
- Displayed as annual run-rate impact (not discounted for tenure)

---

## Implementation Sequence

### Phase 1: Core Analysis Engine
1. Data validation & missing value handling
2. Outlier detection (by segment)
3. Feature engineering (numeric + one-hot)
4. OLS regression with statsmodels
5. Prediction & residual calculation
6. Anomaly detection (residual threshold)

### Phase 2: Recommendation Engine
1. Calculate controlled gap (β_gender coefficient)
2. Calculate uncontrolled gap (raw medians)
3. Implement Pattern A & B detection
4. Cost calculation

### Phase 3: Frontend Dashboard
1. Macro overview (gaps + charts)
2. Micro remediation table (flagged employees)
3. Data quality report
4. Admin approval screen (coefficient review + parameter toggling)
5. Configuration drawer (thresholds + parameter selection)

### Phase 4: API Integration
1. Endpoint: `/api/analyze` (CSV upload)
2. Endpoint: `/api/analyze-json` (JSON payload)
3. Async recalculation on parameter change
4. Return: Full results + coefficients + recommendations

---

## Key Implementation Notes

1. **Use statsmodels, not scikit-learn**, for p-values
2. **Log-transform salary**, not features (preserves interpretability)
3. **One-hot encode** with `drop_first=True` to avoid multicollinearity
4. **Never allow manual coefficient override** (violates statistical validity)
5. **Always exclude outliers before fitting**, but keep them in dataset with flags
6. **Use residual std error, not fixed %, for anomaly thresholds**
7. **Calculate controlled gap using exponential formula**: `(e^β - 1) × 100`
8. **Only trigger Pattern B if controlled_gap is negative** (women underpaid)

---

## Next Steps

This specification is production-ready. To implement:

1. **Hire or assign a Python/React developer** familiar with:
   - statsmodels (statistical inference)
   - pandas (data manipulation)
   - React (interactive dashboards)

2. **Use this document as your technical spec** - share it directly with your dev team

3. **Expected build time:** 40-60 hours for full implementation
   - Backend: 20 hours
   - Frontend: 25 hours
   - Testing & refinement: 15 hours

4. **Recommended tech stack:**
   - Backend: FastAPI + statsmodels + pandas
   - Frontend: React + Recharts (for visualizations)
   - Deployment: Docker + Heroku/Railway/AWS

---

## References

- Oaxaca, R. (1973). Male-Female Wage Differentials in Urban Labor Markets
- Blau, F. D., & Kahn, L. M. (2017). The Gender Wage Gap: Extent, Trends, and Explanations
- Statsmodels documentation: https://www.statsmodels.org/stable/index.html

---

This specification is complete and ready for development. Use it as your technical bible.
