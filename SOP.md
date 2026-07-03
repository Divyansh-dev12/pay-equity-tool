# Pay Equity Studio — Standard Operating Procedure

**Version:** 1.0 · **Date:** 2026-07-03
**GitHub:** https://github.com/Divyansh-dev12/pay-equity-tool

---

## 1. Purpose

Pay Equity Studio is an analytical tool for detecting, quantifying, and remediating gender pay gaps in an organisation. It provides two complementary analytical lenses:

1. **Regression Model** — a statistically rigorous, like-for-like comparison that controls for legitimate pay drivers (level, tenure, performance, function, location) and isolates an unexplained gender residual — the adjusted pay gap.
2. **Median Model** — a benchmarking-based approach that measures how far each employee sits above or below the cohort midpoint (function × level), producing a transparent pay positioning view without statistical assumptions.

Use the Regression Model when you need a defensible, audit-ready adjusted gap figure. Use the Median Model when you need a fast, business-readable read on how pay is positioned within cohorts.

---

## 2. Loading Data

From the home screen, select a model and load data via one of two methods:

### 2.1 Sample dataset (no file needed)

Click **▶ Load sample data**. The tool runs a full analysis on a built-in dataset of **340 synthetic employees** across 8 functions and 5 levels. Use this to explore all features before uploading your own data.

### 2.2 Upload your own employee data

Click **Upload CSV** and select a file with these required columns:

| Column | Description | Example |
|--------|-------------|---------|
| `employee_id` | Unique identifier | EMP0001 |
| `job_function` | Business function / department | Engineering |
| `job_level` | Seniority band | L3 |
| `gender` | Male / Female | Female |
| `base_salary` | Annual fixed pay in INR (whole number) | 2400000 |
| `tenure_years` | Years at company (decimal) | 3.5 |
| `performance_rating` | Rating on any scale (1–5 recommended) | 4.2 |
| `location` | Office city | Bangalore |

Optional columns (used if present): `job_title`, `department`, `hire_date`, `bonus`.

---

## 3. Regression Model — How It Works

### 3.1 The core formula

The model fits an Ordinary Least Squares (OLS) regression on log-transformed salary:

```
ln(base_salary) = β₀
                + β₁ · job_level      (L1–L5, dummy-encoded, L1 as base)
                + β₂ · tenure_years   (continuous)
                + β₃ · performance    (continuous)
                + β₄ · job_function   (dummy-encoded)
                + β₅ · location       (dummy-encoded)
                + β_gender · gender   (1 = Female, 0 = Male)
                + ε
```

The **gender coefficient** (`β_gender`) is the **adjusted pay gap** — the unexplained pay difference for a woman vs a man with identical level, tenure, performance, function and location. It is expressed as a percentage (e.g., −3.5% means women are paid 3.5% less after all legitimate factors are held equal).

### 3.2 Key metrics

| Metric | What it means |
|--------|---------------|
| **Adjusted pay gap** | Like-for-like gender gap (β_gender). The primary number for remediation and legal purposes. |
| **Unadjusted pay gap** | Raw median pay difference between women and men with no adjustment. Reflects both pay rates and representation differences across grades. |
| **R² (Model confidence)** | How much of pay variation the model explains. R² > 0.85 = high confidence in the adjusted gap figure. |
| **Below-range flag** | Employees whose actual pay is more than 1 standard deviation below their predicted pay for their grade and profile. |
| **Above-range flag** | Employees whose actual pay is more than 15% above their model prediction. |

### 3.3 Reading the model output

The **adjusted gap** is the headline finding. Compare it to the **unadjusted gap**:

- If both gaps are similarly large → the organisation is paying women less for equivalent roles.
- If the unadjusted gap is large but the adjusted gap is small → the gap is driven by grade and function distribution (a pipeline issue), not by unequal pay rates. The focus shifts to representation rather than remediation.

The **coefficients panel** (bottom of results) shows every model variable with its coefficient and statistical significance (p-value). A p-value below 0.05 indicates the relationship is statistically significant. The gender row is the primary finding.

---

## 4. Median Model — How It Works

### 4.1 The approach

Every employee is compared to the **cohort midpoint** — the median fixed pay of all employees in the same function and level. The gap is expressed as a percentage above or below that line.

```
gap_rupees = base_salary − cohort_midpoint
gap_pct    = gap_rupees / cohort_midpoint × 100
```

An employee is **below midpoint** if `gap_rupees < 0`.
An employee is **significantly above midpoint** if `gap_pct > +15%`.

### 4.2 Midpoint source options

| Option | When to use |
|--------|-------------|
| **Internal midpoints** (default) | Midpoints are computed from your uploaded employee data. Useful for spotting intra-company pay positioning gaps. |
| **Upload market benchmark** | Upload a file with columns `job_function`, `job_level`, `median_salary` to compare against external market rates. Any cohort missing from the upload falls back to internal midpoints. |

### 4.3 Key metrics

| Metric | What it means |
|--------|---------------|
| **Gender gap vs midpoint** | Women's average pay position (%) minus men's average position. Negative = women sit further below the fair pay line. |
| **% below midpoint** | Share of women / men paid below their cohort midpoint. |
| **Equity adjustment cost** | Sum of shortfalls for all employees below the midpoint — the minimum annual cost to bring everyone to pay parity. |
| **Above midpoint >15%** | Employees significantly above benchmark — attrition risk if they leave; budget exposure if they are retained above market. |

---

## 5. Dashboard Features

### 5.1 Filter bar

Located above the employee roster. Dropdowns for **Function**, **Level**, and **Gender** filter all panels simultaneously — KPI cards, analytics charts, budget planner, cost impact, and the roster all reflect the active filter.

A confirmation banner at the top of results shows how many employees are in the filtered view.

### 5.2 Analytics overview panel

Contains:

- **KPI tiles** — total fixed pay, headcount, below-range count, equity adjustment cost, above-range count, gap as % of fixed pay.
- **Gender split** — female/male proportion in the current filtered view.
- **Pay by level** — median salary for women vs men at each level (L1–L5).
- **Equity adjustment cost by function** (Regression) / **% below midpoint by function** (Median) — sorted by severity.
- **Headcount by level** (Regression) / **Pay positioning distribution** (Median).

### 5.3 Pay Equity Remediation Planner

Enter an **annual equity budget as % of total fixed pay**. The planner calculates:

- Annual budget in INR
- Estimated number of compensation cycles to fully close the gap
- Contextual guidance (one-cycle closure, two-cycle phased approach, attrition risk flag)

The planner auto-suggests the minimum budget percentage required to close the gap within a single review cycle — useful when building a business case for leadership approval.

### 5.4 Employee roster (3-tab view)

| Tab | Shows |
|-----|-------|
| **Full headcount** | Complete filtered employee list, sorted by shortfall (largest first) |
| **Below range / Below midpoint** | Only flagged employees requiring equity correction |
| **Above range** | Employees significantly above the pay line |

### 5.5 Insights

Auto-generated narrative (4–5 points) ordered by importance. Covers: headline adjusted gap, pipeline vs pay-rate story, priority function for equity review, benchmark function, and remediation scope.

### 5.6 Chatbot

Bottom of each dashboard. Ask questions about the data in plain English (e.g. "What is the adjusted gap in Engineering?", "Which level has the worst gap?", "How many women are below range in Sales?"). Responses are grounded in the current analysis output.

---

## 6. Export (PDF & PPT)

The **Export current view** bar appears above the analytics panel.

| Button | Output |
|--------|--------|
| **Download PDF** | A4 portrait. Pages: cover, KPI grid, insights, charts (2 per page), recommended actions. |
| **Download PPT** | 16:9 slides. Slides: title, KPI dashboard, insights, charts, recommendations. |

**Filter-aware:** if a filter is active (e.g. Function = Sales), only Sales data is exported. The file name includes the filter and date: e.g. `pay-equity-regression-Function-Sales-2026-07-03.pdf`.

---

## 7. Sample Dataset — 340 Employees

The built-in sample dataset is a **synthetic Indian compensation dataset** with deliberate, realistic pay equity scenarios across 8 functions and 5 levels.

### 7.1 Dataset composition

| Function | Headcount | % Female | Designed Gap | Scenario |
|----------|-----------|----------|--------------|----------|
| Engineering | 60 | 30% | −6.5% | Common tech pay gap |
| Sales | 50 | 34% | −12.0% | Largest gap — priority function |
| Operations | 40 | 38% | −5.0% | Moderate gap |
| Marketing | 36 | 55% | −3.0% | Mild gap, female-majority function |
| Data Science | 40 | 42% | −1.0% | Near-equitable |
| Product Management | 40 | 44% | −0.5% | Near-equitable |
| Finance | 40 | 52% | +4.0% | Women positioned above men |
| Human Resources | 34 | 62% | 0.0% | Benchmark function — fully equitable |

**Total: 340 employees · 196 Male · 144 Female**

### 7.2 Pay bands (Annual Fixed CTC, INR)

| Level | Band | Approx range |
|-------|------|--------------|
| L1 | ₹6–10 LPA | ₹7.65L – ₹13.2L |
| L2 | ₹11–18 LPA | ₹14L – ₹24L |
| L3 | ₹20–32 LPA | ₹25L – ₹43L |
| L4 | ₹38–55 LPA | ₹48L – ₹74L |
| L5 | ₹60–90 LPA | ₹76L – ₹1.17Cr |

### 7.3 Other dimensions

| Dimension | Values |
|-----------|--------|
| Tenure | 0.5 – 9.0 years |
| Performance rating | 1.0 – 5.0 scale (mean 3.6) |
| Locations | Bangalore (+8%), Mumbai (+6%), Delhi NCR (+5%), Hyderabad (base), Pune (−2%) |

### 7.4 Observed gaps in sample data

| Function | Female Median | Male Median | Raw Unadjusted Gap |
|----------|--------------|-------------|---------------------|
| Sales | ₹16.7L | ₹20.7L | **−19.5%** |
| Operations | ₹14.4L | ₹17.4L | **−17.2%** |
| Human Resources | ₹15.5L | ₹18.0L | −13.7% |
| Finance | ₹17.1L | ₹17.8L | −4.4% |
| Engineering | ₹21.9L | ₹20.6L | +6.3% |
| Data Science | ₹22.4L | ₹21.4L | +4.4% |
| Marketing | ₹19.3L | ₹18.1L | +6.9% |
| Product Management | ₹24.2L | ₹22.6L | +7.1% |

> The unadjusted gap reflects both pay rates and seniority distribution differences within each function. The regression model's adjusted gap isolates the pure pay effect.

---

## 8. Interpreting Results

### 8.1 Adjusted gap — action thresholds

| Adjusted gap | Interpretation | Recommended action |
|-------------|---------------|--------------------|
| 0% to −2% | Marginal / within acceptable range | Monitor; check specific pockets at function level |
| −2% to −5% | Moderate, real gap | Targeted equity correction in next review cycle; leadership briefing |
| −5% to −10% | Significant | Formal remediation plan; HR and legal review |
| < −10% | Severe | Immediate pay corrections; full compensation audit |

### 8.2 Prioritisation framework

1. Address employees with the **largest absolute shortfall first** (highest gap in rupees).
2. Focus on functions with the **highest adjusted gap** and a meaningful female headcount.
3. Use the **Remediation Planner** to model a realistic budget and timeline.
4. Factor in the **natural attrition offset** — above-range employees who exit reduce the net remediation cost over time.

---

## 9. Uploading Real Data — Pre-run Checklist

- [ ] Base salary = annual fixed CTC only (exclude variable pay, bonus, allowances).
- [ ] All salary values in **INR whole rupees** (no decimals, no commas in the CSV).
- [ ] Gender column uses **Female / Male** exactly (not F/M or other abbreviations).
- [ ] Job levels are **consistent** across functions (e.g. all Senior roles mapped to L3, not a mix of L3 / Senior / III).
- [ ] At least **5 employees per cohort** (function × level) for the median model to be meaningful.
- [ ] Exclude employees on long leave or in transitional roles if their salary would distort cohort midpoints.

---

*Pay Equity Studio is built for analytical decision support. All results should be reviewed by a qualified HR or legal professional before taking compensation actions.*
