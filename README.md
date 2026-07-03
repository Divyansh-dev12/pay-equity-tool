# Pay Equity Analysis Tool

A full-stack web application implementing a defensible, reproducible 5-step methodology for identifying and remediating wage gaps. Built on academic research (Oaxaca 1973, Blau & Kahn 2017) and validated against real corporate case studies (Salesforce, Microsoft, Google, Oracle).

## What This Does

Uploads employee compensation data → Runs statistical analysis → Generates:
1. **Data quality report** (Step 1)
2. **Workforce composition breakdown** (Step 2)
3. **Controlled wage gap analysis** by role/level (Step 3)
4. **Root cause investigation** for flagged gaps (Step 4)
5. **Prioritized remediation plan** with costs (Step 5)

## Key Features

✓ **Upload CSV or use sample data** — No manual analysis needed  
✓ **Automatic gap detection** — Flags gaps ≥2% for investigation  
✓ **Root cause analysis** — Separates explained (tenure/performance) from unexplained gaps  
✓ **Remediation planning** — Prioritizes by impact, estimates costs  
✓ **Downloadable reports** — Share with leadership/board  
✓ **Built-in case study** — Synthetic TechCorp dataset demonstrates the full analysis  

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Server runs at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`

### Try the Demo

1. Open http://localhost:5173
2. Click "Load Sample Data"
3. Click "Analyze" → Watch as the 5 steps run in sequence
4. Review findings (gaps flagged, root causes, remediation plan)
5. Download report

---

## The Framework

### Step 1: Data Preparation & Validation
- Validate required columns (employee_id, job_title, job_level, base_salary, gender, tenure_years)
- Check for duplicates, missing values, outliers
- Output: Clean dataset + data quality summary

### Step 2: Descriptive Analysis
- Headcount by role + gender (Table 1)
- Median salary by role + gender (Table 2)
- Unadjusted wage gaps
- Occupational segregation analysis

### Step 3: Controlled Wage Gap Analysis
**Methodology:** Oaxaca (1973) wage decomposition

For each role/level combination (N ≥ 5):
- Calculate median salary for males
- Calculate median salary for females
- Controlled gap = (Female Median - Male Median) / Male Median

Interpretation:
- < 2% = noise, no action
- 2–5% = worth investigating
- > 5% = flag for immediate remediation

### Step 4: Root Cause Investigation
For each flagged gap (≥ 2%), analyze:
- Tenure differences (seniority explains gap)
- Performance rating differences (merit explains gap)
- Hire date patterns (negotiation bias?)
- Occupational segregation (sub-role specialization?)

Output: "Explained" vs "Unexplained" portion of gap

### Step 5: Remediation Planning
- **IMMEDIATE** (30 days): Gaps > 5% unexplained
- **MEDIUM-TERM** (6 months): Gaps 2–5% unexplained
- **MONITORING**: Gaps explained by legitimate factors

Calculate cost per action: `Gap % × Salary × # Employees`

---

## Case Study: TechCorp

**Included in `/docs/CASE_STUDY.md`**

- 102 employees across 5 roles
- 37% female, 63% male
- Synthetic dataset with realistic salary ranges (INR)
- **Findings:**
  - Overall unadjusted gap: 5.2%
  - Product Manager gap: 7.1% (unexplained) → Immediate remediation
  - Software Engineer gap: 6.7% (partially explained) → Investigate
  - Cost to remediate: ₹15L/year (4% of payroll)

**Run it:**
```bash
curl http://localhost:8000/api/sample-data
# Returns 102 employee records
```

---

## API Endpoints

### `GET /api/sample-data`
Returns synthetic TechCorp dataset (102 employees)

```json
{
  "data": [
    {
      "employee_id": "EMP0001",
      "job_title": "Software Engineer",
      "job_level": "L2",
      "base_salary": 2400000,
      "gender": "Male",
      "tenure_years": 2.5,
      ...
    }
  ],
  "rows": 102
}
```

### `POST /api/analyze`
Upload CSV file with employee data

**Required columns:**
- employee_id
- job_title
- job_level
- base_salary
- gender
- tenure_years

**Optional:**
- department, location, bonus, equity, performance_rating, hire_date

**Returns:** Full AnalysisResponse (all 5 steps)

```json
{
  "step1_data_quality": { ... },
  "step2_descriptive": { ... },
  "step3_controlled_gaps": { ... },
  "step4_root_causes": { ... },
  "step5_remediation": { ... },
  "summary": { ... }
}
```

### `POST /api/analyze-json`
Same as `/api/analyze` but accepts JSON payload instead of CSV

---

## CSV Template

Create your own dataset using this format:

```csv
employee_id,job_title,job_level,base_salary,gender,tenure_years,performance_rating
EMP0001,Software Engineer,L2,2400000,Male,2.5,4.1
EMP0002,Software Engineer,L2,2280000,Female,2.3,4.0
EMP0003,Product Manager,L2,3520000,Male,4.2,4.0
EMP0004,Product Manager,L2,3270000,Female,4.5,4.3
...
```

**Notes:**
- Gender: "Male" or "Female"
- Base salary: In consistent currency (INR, USD, etc.)
- Tenure: In years (decimal)
- Performance: Optional, 1–5 scale

---

## Research & References

### Methodology
- **Oaxaca, R. (1973).** "Male-Female Wage Differentials in Urban Labor Markets." *International Economic Review*, 14(3): 693–709.
  - Foundational wage decomposition methodology
  - [Full text](https://www.jstor.org/stable/2525981)

- **Blau, F. D., & Kahn, L. M. (2017).** "The Gender Wage Gap: Extent, Trends, and Explanations." *Journal of Economic Literature*, 55(3): 789–865.
  - Shows occupational segregation is major driver of gaps
  - [Full text](https://www.aeaweb.org/articles?id=10.1257%2Fjel.20160995)

### Corporate Case Studies
- **Salesforce:** $5–6M/year for audits since 2015; improved from 5% to 0% gap in many roles
- **Microsoft:** Zero controlled gaps (within job title/level/tenure)
- **Google:** $118M settlement (2022) for equal pay claims
- **Oracle:** Ongoing litigation; alleged 20% gaps in tech roles

### More Details
See `/docs/FRAMEWORK.md`, `/docs/CASE_STUDY.md`, `/docs/RESEARCH.md`

---

## Project Structure

```
pay-equity-tool/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── analysis.py          # 5-step analysis logic
│   ├── models.py            # Data models
│   ├── synthetic_data.py    # Case study data generation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── index.css
│   └── package.json
├── docs/
│   ├── FRAMEWORK.md         # Full 5-step methodology
│   ├── CASE_STUDY.md        # TechCorp analysis
│   └── RESEARCH.md          # Paper citations + references
└── README.md
```

---

## Development

### Add a new analysis feature
1. Extend `PayEquityAnalyzer` in `backend/analysis.py`
2. Update API endpoint in `backend/main.py`
3. Add UI component in `frontend/src/components/`

### Customize for your company
1. Modify `synthetic_data.py` with your salary bands/roles
2. Update headcount distribution
3. Regenerate dataset: `python synthetic_data.py`

### Deploy
- **Backend:** Deploy FastAPI app (Heroku, Railway, AWS Lambda)
- **Frontend:** Deploy React app (Vercel, Netlify, GitHub Pages)
- **CORS:** Update allowed origins in `main.py`

---

## FAQ

**Q: Is this a compliance tool?**  
A: No. This identifies wage gaps. A legal determination of discrimination requires additional legal analysis. Use this for proactive auditing.

**Q: Does it handle protected leave, part-time, commissions?**  
A: Not in base version. Customize `Step 1` to exclude these categories or adjust salaries to FTE equivalents.

**Q: Can I use it for bonus/equity analysis?**  
A: Yes. Run the same analysis on bonus or equity columns (adjust column names in CSV).

**Q: How often should I audit?**  
A: Salesforce does annual audits. Recommended frequency: annually (post-review cycle) or semi-annually for large organizations.

---

## License

MIT

---

## Credits

- **Framework:** Based on Oaxaca (1973) wage decomposition methodology
- **Case studies:** Inspired by Salesforce, Microsoft, Google, Oracle transparency reports
- **Research:** Blau & Kahn (2017); Harvard Business School pay equity research

---

## Questions?

- Read `/docs/FRAMEWORK.md` for methodology details
- Check `/docs/CASE_STUDY.md` for walkthrough example
- See `/docs/RESEARCH.md` for paper citations

Built with FastAPI + React. Open source. MIT license.
