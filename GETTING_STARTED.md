# Getting Started with Pay Equity Analyzer

## What's Included

You now have a **complete full-stack pay equity analysis tool** with:

### ✅ Backend (FastAPI)
- `backend/analysis.py` — Core 5-step analysis engine (200+ lines)
  - Step 1: Data validation & quality checks
  - Step 2: Descriptive statistics & gap analysis
  - Step 3: Controlled gap analysis (Oaxaca 1973 methodology)
  - Step 4: Root cause investigation
  - Step 5: Remediation planning
- `backend/main.py` — FastAPI endpoints
- `backend/models.py` — Pydantic data models
- `backend/synthetic_data.py` — TechCorp synthetic dataset generator
- `backend/requirements.txt` — Python dependencies

### ✅ Frontend (React + Vite)
- `frontend/src/App.jsx` — Interactive UI with charts
- `frontend/src/App.css` — Modern responsive styling
- React components for:
  - File upload & demo data loading
  - Step-by-step analysis display
  - Executive summary dashboard
  - Charts (bar, pie, line) powered by Recharts
  - Downloadable JSON reports

### ✅ Documentation
- `docs/FRAMEWORK.md` — Full 5-step methodology (comprehensive)
- `docs/CASE_STUDY.md` — TechCorp analysis walkthrough
- `docs/RESEARCH.md` — Paper citations + corporate case studies
- `README.md` — Project overview

---

## Quick Start (Two Terminals)

### Terminal 1: Backend

```bash
cd /Users/divyanshkhanduja/Desktop/pay-equity-tool

# Create virtual environment (one time)
python3 -m venv venv
source venv/bin/activate

# Install dependencies (one time)
pip install -r backend/requirements.txt

# Start backend server
cd backend
python3 -m uvicorn main:app --reload
```

**Backend runs at:** `http://localhost:8000`  
**API docs:** `http://localhost:8000/docs` (Swagger UI)

### Terminal 2: Frontend

```bash
cd /Users/divyanshkhanduja/Desktop/pay-equity-tool
cd frontend

# Install dependencies (one time)
npm install

# Start dev server
npm run dev
```

**Frontend runs at:** `http://localhost:5173`

---

## How to Use

1. **Open browser:** `http://localhost:5173`

2. **Choose one:**
   - Click "Load Sample Data" → Analyzes TechCorp (synthetic 102 employees)
   - Click "Upload CSV" → Upload your own employee data

3. **Watch the analysis** run through all 5 steps:
   - Step 1: Data validation
   - Step 2: Headcount & salary breakdown
   - Step 3: Controlled gaps (flags ≥2%)
   - Step 4: Root cause analysis
   - Step 5: Remediation plan + costs

4. **Download report** → JSON file with full analysis

---

## Testing the API Directly

### Get Sample Data
```bash
curl http://localhost:8000/api/sample-data | jq '.rows'
# Output: 102 (TechCorp employees)
```

### Upload CSV (with your own data)
```bash
curl -X POST -F "file=@your_data.csv" http://localhost:8000/api/analyze | jq '.summary'
```

### API Endpoints
- `GET /` — Health check
- `GET /api/sample-data` — Returns TechCorp synthetic dataset
- `POST /api/analyze` — Upload CSV file → Full analysis
- `POST /api/analyze-json` — Send JSON → Full analysis

---

## Sample CSV Format

Create a file `data.csv`:

```csv
employee_id,job_title,job_level,base_salary,gender,tenure_years,performance_rating
EMP001,Software Engineer,L2,2400000,Male,2.5,4.1
EMP002,Software Engineer,L2,2280000,Female,2.3,4.0
EMP003,Product Manager,L2,3520000,Male,4.2,4.0
EMP004,Product Manager,L2,3270000,Female,4.5,4.3
```

**Required columns:**
- employee_id
- job_title
- job_level
- base_salary
- gender
- tenure_years

**Optional:**
- department
- location
- bonus
- equity
- performance_rating
- hire_date

Upload via web UI or via API:
```bash
curl -X POST -F "file=@data.csv" http://localhost:8000/api/analyze
```

---

## The Case Study (TechCorp)

**Synthetic dataset:** 102 employees, 5 roles, deliberately-created gaps

**Key findings:**
- **Overall unadjusted gap:** -5.2% (women earn 5.2% less on average)
- **Product Manager (L2) gap:** -7.1% ← Unexplained, requires immediate action
- **Software Engineer gap:** -6.7% ← Partially explained by tenure
- **Finance gap:** +3.5% (women actually earn more)

**Cost to remediate:** ₹15L/year (~2% of payroll)

**Timeline:** Immediate actions within 30 days; investigation complete by year-end

Run it: Click "Load Sample Data" in the UI

---

## Understanding the Analysis

### Unadjusted Gap
The raw difference in median pay between men and women across the entire company.

**Example:** Men earn ₹30L median, women earn ₹28.5L median → -5% gap

**Problem:** This conflates two issues:
1. **Occupational segregation** — women in lower-paying roles
2. **Pay discrimination** — women paid less for same role

### Controlled Gap
The difference when comparing like-for-like roles/levels.

**Example:** Product Managers (all levels):
- Men: ₹35.2L median
- Women: ₹32.7L median
- Controlled gap: -7.1%

This isolates pay decisions from job choice.

### Explained vs Unexplained
After accounting for tenure, performance, hire date, etc.

**Explained:** 2 years of tenure difference → ~2% salary difference (normal progression)

**Unexplained:** 7% gap with no tenure/performance difference → potential discrimination

---

## Deployment (Production)

### Backend (FastAPI)
Options:
- **Heroku:** `git push heroku main`
- **Railway:** Connect repo, auto-deploy
- **AWS Lambda:** Deploy with Zappa
- **Docker:** Build image, push to registry

Key: Update `CORS_ORIGINS` in `backend/main.py` with frontend URL

### Frontend (React)
Options:
- **Vercel:** `npm install -g vercel && vercel`
- **Netlify:** Drag-drop `npm run build` output
- **GitHub Pages:** Add to GitHub, enable Pages

Key: Update `API_URL` in `frontend/src/App.jsx` with backend URL

---

## Customization

### Use Your Own Salary Data
1. Prepare CSV (format above)
2. Upload via UI or API
3. Get analysis in seconds

### Modify the Analysis
Edit `backend/analysis.py`:
- Adjust gap threshold (currently 2%)
- Add new metrics (e.g., bonus gap analysis)
- Customize root cause factors

### Update Styling
Edit `frontend/src/App.css`:
- Change color scheme
- Adjust layout
- Add new components

### Generate Different Sample Data
Edit `backend/synthetic_data.py`:
- Change salary bands
- Adjust headcount distribution
- Modify gap patterns

Then re-run sample data generation:
```bash
python3 backend/synthetic_data.py
```

---

## Troubleshooting

**Backend won't start:**
```bash
# Check Python version
python3 --version  # Needs 3.9+

# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

**Frontend won't start:**
```bash
# Check Node version
node --version  # Needs 16+

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**CORS errors:**
Make sure both servers are running:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

If deploying, update CORS origins in `backend/main.py`:
```python
allow_origins=["https://your-frontend-url.com"],
```

**Data not analyzing:**
Check browser console (F12) for error messages. Ensure CSV has required columns.

---

## What's Next?

### For Learning
1. Read `/docs/FRAMEWORK.md` for deep methodology dive
2. Read `/docs/CASE_STUDY.md` for walkthrough example
3. Read `/docs/RESEARCH.md` for paper citations

### For Using It
1. Prepare your employee data (CSV)
2. Upload via web UI or API
3. Review findings step-by-step
4. Download JSON report for board/leadership

### For Building
1. Extend analysis (add bonus gap, equity gap, etc.)
2. Add data visualization (heatmaps, regression plots)
3. Export to PDF (instead of JSON)
4. Connect to HR system (pull data automatically)
5. Deploy to production

---

## Project Structure

```
pay-equity-tool/
├── backend/
│   ├── main.py                 # FastAPI app + endpoints
│   ├── analysis.py             # 5-step analysis engine
│   ├── models.py               # Data models (Pydantic)
│   ├── synthetic_data.py       # Dataset generator
│   └── requirements.txt         # Python deps
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── App.css             # Styling
│   │   └── main.jsx            # Entry point
│   ├── index.html              # HTML template
│   ├── vite.config.js          # Build config
│   └── package.json            # Node deps
├── docs/
│   ├── FRAMEWORK.md            # 5-step methodology
│   ├── CASE_STUDY.md           # TechCorp analysis
│   └── RESEARCH.md             # Papers + case studies
├── .claude/
│   └── launch.json             # Launch config (for Claude Code)
├── README.md                   # Project overview
├── GETTING_STARTED.md          # This file
└── .gitignore
```

---

## Questions?

**Framework questions?** → Read `docs/FRAMEWORK.md`  
**How to interpret results?** → Read `docs/CASE_STUDY.md`  
**Research/references?** → Read `docs/RESEARCH.md`  
**API questions?** → Check `backend/main.py` or visit `http://localhost:8000/docs`  

---

## Credits

- **Framework:** Oaxaca (1973) wage decomposition
- **Case studies:** Salesforce, Microsoft, Google, Oracle
- **Research:** Blau & Kahn (2017)
- **Built with:** FastAPI + React + Recharts

Happy analyzing! 🎯
