# Pay Equity Analyzer - Quick Start (5 Minutes)

## TL;DR

You have a **complete pay equity analysis tool** ready to use. Start both servers and upload data.

---

## Start (Choose One)

### Option A: Use the convenience script (Easiest)
```bash
cd /Users/divyanshkhanduja/Desktop/pay-equity-tool
chmod +x run.sh
./run.sh
```

Then open: http://localhost:5173

---

### Option B: Start servers manually (2 terminals)

**Terminal 1: Backend**
```bash
cd /Users/divyanshkhanduja/Desktop/pay-equity-tool
source venv/bin/activate
cd backend
python3 -m uvicorn main:app --reload
```
→ Backend ready at http://localhost:8000

**Terminal 2: Frontend**
```bash
cd /Users/divyanshkhanduja/Desktop/pay-equity-tool/frontend
npm run dev
```
→ Frontend ready at http://localhost:5173

---

## Try the Demo (1 Click)

1. Open http://localhost:5173
2. Click **"Load Sample Data"**
3. Watch the analysis run (TechCorp case study: 102 employees)
4. Review findings:
   - Step 1: Data validation ✓
   - Step 2: Headcount & salary breakdown
   - Step 3: Controlled gaps (flags ≥2%)
   - Step 4: Root causes
   - Step 5: Remediation plan
5. Click **"Download Full Report"**

**Demo findings:**
- Overall gap: ~5%
- Product Manager gap: -7% (unexplained) → Immediate action needed
- Cost to fix: ~₹15L/year

---

## Use Your Own Data

1. Prepare CSV with these columns:
   ```
   employee_id, job_title, job_level, base_salary, gender, tenure_years
   EMP001,Software Engineer,L2,2400000,Male,2.5
   EMP002,Software Engineer,L2,2280000,Female,2.3
   ```

2. Upload via UI → "Upload CSV"

3. Get analysis in seconds

---

## API (Curl/Postman)

### Get sample data
```bash
curl http://localhost:8000/api/sample-data | jq '.rows'
# Output: 102
```

### Upload CSV
```bash
curl -X POST -F "file=@data.csv" \
  http://localhost:8000/api/analyze | jq '.summary'
```

### API docs
Visit: http://localhost:8000/docs

---

## Understand the Results

**Unadjusted Gap:** Raw difference in median pay (all roles)  
**Controlled Gap:** Difference when comparing same roles (isolates pay decisions)  
**Explained:** Caused by tenure/performance differences (OK)  
**Unexplained:** Can't be explained by legitimate factors (FLAG)

---

## What's Included

| What | Where |
|------|-------|
| Methodology | `/docs/FRAMEWORK.md` |
| Case study | `/docs/CASE_STUDY.md` |
| Research papers | `/docs/RESEARCH.md` |
| Project overview | `/README.md` |
| Setup guide | `/GETTING_STARTED.md` |
| Full summary | `/PROJECT_SUMMARY.md` |

---

## Troubleshooting

**Frontend won't load?**
```bash
cd frontend
npm install
npm run dev
```

**Backend won't start?**
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python3 -m uvicorn main:app --reload
```

**CORS error?**
Make sure both servers are running:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

**Data not loading?**
Check browser console (F12) for errors. Verify CSV has required columns.

---

## Next Steps

✓ Try the demo (5 min)  
✓ Read the methodology (`/docs/FRAMEWORK.md`) (10 min)  
✓ Review the case study (`/docs/CASE_STUDY.md`) (10 min)  
✓ Upload your own data (5 min)  
✓ Download reports & share with leadership  

---

## Questions?

- **How does it work?** → `/docs/FRAMEWORK.md`
- **Show me an example** → `/docs/CASE_STUDY.md`
- **Which papers?** → `/docs/RESEARCH.md`
- **API details?** → http://localhost:8000/docs

---

**Status:** ✅ Ready to use  
**Demo data:** ✅ Included (TechCorp, 102 employees)  
**Documentation:** ✅ Complete  
**Deployment:** ✅ Ready for production  

Enjoy! 🎯
