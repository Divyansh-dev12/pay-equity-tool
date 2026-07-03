# Pay Equity Studio — Standard Operating Procedure

**Version:** 1.0 · **Date:** 2026-07-03  
**Tool URL (local):** http://localhost:3000  
**GitHub:** https://github.com/Divyansh-dev12/pay-equity-tool

---

## 1. Purpose

Pay Equity Studio is a full-stack analytical tool for detecting, quantifying, and remediating gender pay gaps in an organisation. It provides two complementary analytical lenses:

1. **Regression Model** — a statistically rigorous, like-for-like comparison that controls for legitimate pay drivers (level, tenure, performance, function, location) and isolates an unexplained gender residual.
2. **Median (Linear) Model** — a transparent, benchmarking-based approach that measures how far each employee sits above or below the median pay line of their cohort (function × level).

---

## 2. System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.10+ |
| Node.js | 18+ |
| Backend port | 8000 |
| Frontend port | 3000 |

**Python dependencies** (in `backend/requirements.txt`): FastAPI, uvicorn, pandas, numpy, statsmodels, scikit-learn, python-multipart

**Frontend dependencies**: React 18, Vite 5, Recharts, jsPDF, html2canvas, pptxgenjs

---

## 3. Starting the Application

### 3.1 First-time setup

```bash
# 1. Clone / navigate to the project
cd ~/Desktop/pay-equity-tool

# 2. Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Install frontend dependencies
cd frontend && npm install && cd ..
```

### 3.2 Starting the servers (every session)

Open **two terminal tabs**:

**Tab 1 — Backend:**
```bash
cd ~/Desktop/pay-equity-tool/backend
source ../venv/bin/activate
python -m uvicorn main:app --port 8000
```

**Tab 2 — Frontend:**
```bash
cd ~/Desktop/pay-equity-tool/frontend
npm run dev
```

Open your browser at **http://localhost:3000**.

> **Important:** Do NOT use `--reload` with uvicorn in production use. It causes unnecessary process restarts.

---

## 4. Loading Data

From the home screen, choose a model and then load data via one of two methods:

### 4.1 Sample dataset (instant, no file needed)
Click **▶ Load sample data**. The backend generates a synthetic dataset of **340 employees** and runs the full analysis pipeline in seconds. Use this to explore all features before uploading real data.

### 4.2 Upload your own CSV
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

Optional columns (will be used if present): `job_title`, `department`, `hire_date`, `bonus`.

> **Minimum requirement:** 15+ employees for meaningful regression; 5+ employees per cohort recommended for the median model.

---

## 5. Regression Model — How It Works

### 5.1 The core formula

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

The **gender coefficient** (`β_gender`) is the **controlled pay gap** — the unexplained pay difference for a woman vs a man with identical level, tenure, performance, function and location. It is expressed as a percentage (e.g., −3.5% means women are paid 3.5% less after all legitimate factors are held equal).

### 5.2 Key metrics

| Metric | What it means |
|--------|---------------|
| **Controlled gap** | Like-for-like gender gap (β_gender). The key number for legal and remediation purposes. |
| **Uncontrolled gap** | Raw median pay difference between women and men, no adjustment. Reflects both pay and representation gaps. |
| **R²** | How much of pay variation the model explains. R² > 0.85 = high confidence in the controlled gap. |
| **Underpaid flag** | Employees whose actual pay is > 1 σ below their model prediction (regression residual < −1 SD). |
| **Above-model flag** | Employees whose actual pay is > 15% above their model prediction. |

### 5.3 Steps the engine runs

1. **Data preparation** — drops invalid rows, imputes minor missing values.
2. **Outlier detection** — flags salary outliers within function × level cohorts (±3 σ threshold). These are still included in the regression but flagged in the roster.
3. **Feature engineering** — one-hot encodes function and location; log-transforms salary.
4. **OLS fitting** — statsmodels OLS with heteroscedasticity-consistent standard errors.
5. **Anomaly detection** — identifies underpaid individuals (residual < −1 σ).
6. **Breakdowns** — computes gap statistics per function for the heat-map and callouts.
7. **Recommendations** — severity-tiered action plan based on controlled gap magnitude.

### 5.4 Reading the coefficients table

The coefficients panel (bottom of results) shows every model variable with its coefficient and p-value. P-value < 0.05 = statistically significant. The gender coefficient row is highlighted — this is your primary finding.

---

## 6. Median (Linear) Model — How It Works

### 6.1 The approach

Every employee is compared to the **median fixed pay of their cohort**, where cohort = (job_function × job_level). The gap is expressed as a percentage above or below that line.

```
gap_rupees = base_salary − cohort_median
gap_pct    = gap_rupees / cohort_median × 100
```

An employee is **below median** if `gap_rupees < 0`.  
An employee is **significantly above** if `gap_pct > +15%`.

### 6.2 Median source options

| Option | When to use |
|--------|-------------|
| **Internal medians** (default) | Medians are computed from your uploaded employee data. Useful for spotting intra-company gaps. |
| **Upload market benchmark CSV** | Upload a file with columns `job_function`, `job_level`, `median_salary` to compare against external market rates. Any cohort missing from the upload falls back to the internal median. |

### 6.3 Key metrics

| Metric | What it means |
|--------|---------------|
| **Gender gap vs median** | Women's average position (%) minus men's average position. Negative = women sit further below the fair line. |
| **% below median** | Share of women/men paid below their cohort median. |
| **Below median cost** | Sum of shortfalls (gap_rupees) for all employees below the median line — the minimum cost to bring everyone to parity. |
| **Above median >15%** | Employees significantly over the benchmark — market over-positioning risk if they leave. |

---

## 7. Dashboard Features

### 7.1 Filter bar (Quick Roster Filter)

Located above the employee roster. Dropdowns for **Function**, **Level**, and **Gender** filter all panels simultaneously — KPI cards, analytics charts, budget planner, cost impact, and the roster table all reflect the active filter.

The **blue banner** at the top of results confirms how many employees are in the filtered view.

### 7.2 Analytics overview panel

Below the export bar, above the roster. Contains:

- **Totals row** — 6 KPI tiles (total payroll, headcount, underpaid/below-median count, cost to fix, above-model count, gap %).
- **Gender split pie** — female/male proportion in the current filtered view.
- **Pay by level line chart** — median salary for women vs men at each level (L1–L5).
- **Remediation cost by function** (regression) / **% below median by function** (median) — horizontal bar chart, sorted by severity.
- **Headcount by level** (regression) / **Pay positioning** (median) — stacked bar/pie showing who sits where.

### 7.3 Budget planner

Enter an **annual remediation budget as % of total payroll**. The tool calculates:
- Annual budget in INR
- Number of years to fully close the gap at that pace
- Contextual tips (one-cycle fix, two-cycle split, attrition risk warning)

### 7.4 Employee roster (3-way toggle)

| Tab | Shows |
|-----|-------|
| **All employees** | Full filtered list, sorted by shortfall (largest first) |
| **Underpaid / Below median** | Only flagged employees (orange tab) |
| **Above model / Above median** | Employees significantly over the pay line (green tab) |

Pagination kicks in at 500 rows per page.

### 7.5 AI Insights

Auto-generated narrative (4–5 bullets) at the top of results, ordered by importance. Highlights the largest gap, best-performing function, remediation scope, and recommended priority.

### 7.6 Chatbot

Bottom of each dashboard. Ask natural-language questions about the data (e.g. "What is the gap in Engineering?", "Which level has the worst gap?"). The chatbot uses the current analysis context.

---

## 8. Export (PDF & PPT)

The **Export current view** bar appears above the analytics panel.

| Button | Output |
|--------|--------|
| 📄 Download PDF | A4 portrait. Pages: cover, KPI grid, AI insights, charts (2 per page), recommended actions. |
| 📊 Download PPT | 16:9 slides. Slides: title, KPI dashboard, AI insights, charts, recommendations. |

**Filter-aware:** If a filter is active (e.g. Function = Sales), only Sales data is exported. The file name includes the filter and date: e.g. `pay-equity-regression-Function-Sales-2026-07-03.pdf`.

---

## 9. Sample Dataset — 340 Employees

The built-in sample dataset is a **synthetic Indian compensation dataset** generated with deliberate, realistic scenarios. It is reproducible (fixed random seed = 42).

### 9.1 Dataset composition

| Function | Headcount | % Female | Designed Gap | Scenario |
|----------|-----------|----------|--------------|----------|
| Engineering | 60 | 30% | −6.5% (men paid more) | Common tech gap |
| Sales | 50 | 34% | −12.0% (men paid more) | Largest gap — priority case |
| Operations | 40 | 38% | −5.0% (men paid more) | Moderate gap |
| Marketing | 36 | 55% | −3.0% (men paid more) | Mild gap, female-majority |
| Data Science | 40 | 42% | −1.0% (near-equitable) | Almost fair |
| Product Management | 40 | 44% | −0.5% (near-equitable) | Best-in-class |
| Finance | 40 | 52% | +4.0% (women paid more) | Women outperform |
| Human Resources | 34 | 62% | 0.0% (fully equitable) | Benchmark function |

**Total: 340 employees · 196 Male · 144 Female**

### 9.2 Pay bands (Annual Fixed CTC, INR)

| Level | Band (LPA) | Approx INR range |
|-------|-----------|-----------------|
| L1 | ₹6–10 LPA | ₹7.65L – ₹13.2L |
| L2 | ₹11–18 LPA | ₹14L – ₹24L |
| L3 | ₹20–32 LPA | ₹25L – ₹43L |
| L4 | ₹38–55 LPA | ₹48L – ₹74L |
| L5 | ₹60–90 LPA | ₹76L – ₹1.17Cr |

Actual salaries vary by function multiplier, location premium, tenure, and performance. Range across full dataset: **₹7.65L – ₹1.17Cr**.

### 9.3 Other dimensions

| Dimension | Values |
|-----------|--------|
| Tenure | 0.5 – 9.0 years (uniform random) |
| Performance rating | 1.0 – 5.0 scale (normal dist., mean 3.6) |
| Locations | Bangalore (+8%), Mumbai (+6%), Delhi NCR (+5%), Hyderabad (base), Pune (−2%) |

### 9.4 Observed gaps in sample data (regression model output)

| Function | Female Median | Male Median | Raw Gap |
|----------|--------------|-------------|---------|
| Sales | ₹16.7L | ₹20.7L | **−19.5%** |
| Operations | ₹14.4L | ₹17.4L | **−17.2%** |
| Human Resources | ₹15.5L | ₹18.0L | −13.7% |
| Finance | ₹17.1L | ₹17.8L | −4.4% |
| Engineering | ₹21.9L | ₹20.6L | +6.3% |
| Data Science | ₹22.4L | ₹21.4L | +4.4% |
| Marketing | ₹19.3L | ₹18.1L | +6.9% |
| Product Management | ₹24.2L | ₹22.6L | +7.1% |

> Note: raw gaps reflect both pay discrimination AND seniority distribution differences within each function. The regression model's controlled gap isolates the pure pay effect.

---

## 10. Interpreting Results

### 10.1 What action is required?

| Controlled gap | Interpretation | Recommended action |
|---------------|---------------|--------------------|
| 0% to −2% | Marginal / likely noise | Monitor; check specific pockets |
| −2% to −5% | Moderate, real gap | Targeted remediation; leadership briefing |
| −5% to −10% | Significant | Formal remediation plan; HR + legal review |
| < −10% | Severe | Immediate pay corrections; audit hiring process |

### 10.2 Prioritisation framework

1. Fix employees with the **largest shortfall first** (highest gap_dollars / gap_rupees).
2. Focus on functions with the **highest controlled gap** and female concentration.
3. Use the **budget planner** to model a realistic remediation timeline.
4. Check the **natural rebalancing offset** — above-model employees who leave naturally reduce the net remediation cost.

---

## 11. Uploading Real Data — Checklist

- [ ] Base salary = annual fixed CTC only (exclude bonus, variable pay).
- [ ] All values in **INR whole rupees** (no decimals, no commas in the CSV).
- [ ] Gender column uses **Female / Male** exactly (case-insensitive).
- [ ] Job levels are **consistent** across functions (e.g. all Senior roles = L3, not a mix of L3/Senior/III).
- [ ] At least **5 employees per cohort** (function × level) for the median model to be meaningful.
- [ ] Remove any employees on long leave or in transitional roles if they would distort salary data.

---

## 12. API Endpoints (for integrations)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/api/sample-data` | Returns 340-row synthetic dataset |
| POST | `/api/analyze` | Upload CSV → full regression analysis |
| POST | `/api/analyze-json` | JSON body → full regression analysis |
| POST | `/api/analyze-median` | Upload CSV → median model analysis |
| POST | `/api/analyze-median-json` | JSON body → median model analysis |
| POST | `/api/chat` | Chatbot query against current context |

Base URL: `http://localhost:8000`

---

## 13. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "Analysis failed" on upload | Missing required columns or non-numeric salary column | Check CSV column names match Section 4.2 |
| Very low R² (< 0.5) | Too few employees or salary data is very noisy | Ensure 50+ employees; check salary column is base pay not total comp |
| All employees show as underpaid | Salary column includes only base without tenure/level differences | Verify data; try the median model instead |
| Backend won't start | Port 8000 in use | `lsof -ti:8000 | xargs kill` then restart |
| Frontend blank page | Backend not running | Start backend first, then frontend |
| Export PDF is blank/charts missing | Browser security blocks canvas capture | Open app at http://localhost:3000 (not file://) |

---

*Pay Equity Studio is built for analytical decision support. All results should be reviewed by a qualified HR or legal professional before taking compensation actions.*
