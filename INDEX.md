# Pay Equity Analyzer - Complete Documentation Index

## 🚀 START HERE

**Just want to run it?**
→ Read [QUICKSTART.md](QUICKSTART.md) (5 min)

**Want to understand it?**
→ Read [COMPLETE.md](COMPLETE.md) (10 min)

**Ready to use it?**
→ Run `./run.sh` and open http://localhost:5173

---

## 📚 Documentation Map

### Quick Reference (5-10 minutes)
- [QUICKSTART.md](QUICKSTART.md) — Start here (commands + demo)
- [COMPLETE.md](COMPLETE.md) — Status & overview

### Getting Started (15-30 minutes)
- [README.md](README.md) — Project overview
- [GETTING_STARTED.md](GETTING_STARTED.md) — Setup & customization

### Deep Dive (1-2 hours)
- [docs/FRAMEWORK.md](docs/FRAMEWORK.md) — 5-step methodology
- [docs/CASE_STUDY.md](docs/CASE_STUDY.md) — TechCorp analysis walkthrough
- [docs/RESEARCH.md](docs/RESEARCH.md) — Academic papers & case studies

### Reference
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) — What was built (technical details)
- [INDEX.md](INDEX.md) — This file

---

## 🎯 By Goal

### "I want to try it right now"
1. Open [QUICKSTART.md](QUICKSTART.md)
2. Run the commands
3. Click "Load Sample Data" in the UI

**Time:** 5 minutes

### "I want to understand what this does"
1. Read [COMPLETE.md](COMPLETE.md) (overview)
2. Read [docs/FRAMEWORK.md](docs/FRAMEWORK.md) (methodology)
3. Read [docs/CASE_STUDY.md](docs/CASE_STUDY.md) (example)

**Time:** 30 minutes

### "I want to use it with my own data"
1. Read [GETTING_STARTED.md](GETTING_STARTED.md)
2. Prepare your CSV (format explained)
3. Upload via web UI

**Time:** 15 minutes + prep time

### "I want to understand the research"
1. Read [docs/RESEARCH.md](docs/RESEARCH.md) (papers & case studies)
2. Review paper links
3. Read [docs/FRAMEWORK.md](docs/FRAMEWORK.md) (methodology grounded in papers)

**Time:** 45 minutes

### "I want to deploy this"
1. Read [GETTING_STARTED.md](GETTING_STARTED.md) → Deployment section
2. Follow platform-specific instructions
3. Update CORS origins & API URLs

**Time:** 30 minutes

---

## 📋 File Structure

```
pay-equity-tool/
├── 🎯 QUICKSTART.md          ← START HERE (5 min)
├── ✅ COMPLETE.md            ← Status & overview (10 min)
├── 📖 INDEX.md               ← This file
├── README.md                 ← Project overview
├── GETTING_STARTED.md        ← Setup & deployment
├── PROJECT_SUMMARY.md        ← Technical details
│
├── backend/
│   ├── main.py              # FastAPI app
│   ├── analysis.py          # 5-step analysis (this is the core!)
│   ├── models.py            # Data models
│   ├── synthetic_data.py    # Demo dataset
│   └── requirements.txt      # Python deps
│
├── frontend/
│   ├── src/App.jsx          # React UI
│   ├── src/App.css          # Styling
│   └── ...other files...
│
├── docs/
│   ├── FRAMEWORK.md         # 5-step methodology (6 pages)
│   ├── CASE_STUDY.md        # TechCorp analysis (8 pages)
│   └── RESEARCH.md          # Papers & references (4 pages)
│
├── .claude/launch.json      # Launch config
├── run.sh                    # Start script
└── venv/                     # Python virtual env
```

---

## 🔧 Quick Commands

```bash
# Start everything (easiest)
./run.sh

# Or start manually:

# Terminal 1: Backend
source venv/bin/activate
cd backend
python3 -m uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Then open: http://localhost:5173
```

---

## 📊 What This Tool Does

1. **Uploads** employee compensation data (CSV or JSON)
2. **Validates** data quality
3. **Analyzes** wage gaps using Oaxaca decomposition
4. **Identifies** unexplained gaps (potential discrimination)
5. **Recommends** remediation with costs & timeline

**Result:** Actionable report for leadership

---

## 💡 Key Concepts

**Unadjusted Gap:** Raw difference in median pay (all roles combined)
- Example: Women earn 5% less overall

**Controlled Gap:** Difference comparing same roles/levels
- Example: Women in PM L2 earn 7% less than men in PM L2
- Isolates pay decisions from job choice

**Explained Gap:** Due to tenure, performance, etc. (OK)
- Example: Women are newer on average → earn 2% less (normal)

**Unexplained Gap:** Can't be explained by legitimate factors (FLAG)
- Example: 7% gap despite equal tenure & performance → potential issue

---

## 📖 Reading Guide

### For Executives
- Read [QUICKSTART.md](QUICKSTART.md) (5 min)
- Run demo
- Read [docs/CASE_STUDY.md](docs/CASE_STUDY.md) (TechCorp findings)

### For HR Leaders
- Read [QUICKSTART.md](QUICKSTART.md) (5 min)
- Read [GETTING_STARTED.md](GETTING_STARTED.md) (setup & use)
- Read [docs/FRAMEWORK.md](docs/FRAMEWORK.md) (full methodology)
- Prepare your data

### For Developers
- Read [README.md](README.md) (overview)
- Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) (technical details)
- Explore [backend/analysis.py](backend/analysis.py) (core logic)
- Deploy using [GETTING_STARTED.md](GETTING_STARTED.md)

### For Researchers
- Read [docs/FRAMEWORK.md](docs/FRAMEWORK.md) (methodology)
- Read [docs/RESEARCH.md](docs/RESEARCH.md) (papers)
- Explore [backend/analysis.py](backend/analysis.py) (implementation)

---

## ✅ Quality Checklist

- ✅ Fully functional 5-step analysis
- ✅ Interactive web UI with charts
- ✅ REST API (FastAPI)
- ✅ Synthetic demo data included
- ✅ Complete documentation (25+ pages)
- ✅ Tested end-to-end
- ✅ Production-ready code
- ✅ Deployment guides
- ✅ Research-backed methodology

---

## 🎓 Research Behind This

**Academic Foundation:**
- Oaxaca, R. (1973) — Wage decomposition methodology
- Blau & Kahn (2017) — Gender wage gap analysis

**Corporate Validation:**
- Salesforce — $5-6M/year audits (successful proactive approach)
- Microsoft — Achieved zero controlled gaps at scale
- Google — $118M settlement (reactive approach = expensive)
- Oracle — Ongoing litigation (resistance to audits = costly)

---

## 🚀 Next Actions

### Right Now (5 min)
```bash
cd /Users/divyanshkhanduja/Desktop/pay-equity-tool
./run.sh
# Open http://localhost:5173
# Click "Load Sample Data"
```

### Today (1 hour)
- [ ] Try the demo
- [ ] Read FRAMEWORK.md
- [ ] Understand the 5 steps

### This Week
- [ ] Prepare your employee data
- [ ] Upload & analyze
- [ ] Review findings

### Next Week
- [ ] Share report with leadership
- [ ] Plan remediation
- [ ] Deploy to production

---

## 🤔 Questions?

| Question | Answer |
|----------|--------|
| How do I start? | → [QUICKSTART.md](QUICKSTART.md) |
| What is this? | → [COMPLETE.md](COMPLETE.md) |
| How does it work? | → [docs/FRAMEWORK.md](docs/FRAMEWORK.md) |
| Show me an example | → [docs/CASE_STUDY.md](docs/CASE_STUDY.md) |
| What papers? | → [docs/RESEARCH.md](docs/RESEARCH.md) |
| How do I set it up? | → [GETTING_STARTED.md](GETTING_STARTED.md) |
| Technical details? | → [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) |
| API endpoints? | Visit http://localhost:8000/docs |

---

## 📞 Support

**All questions answered in documentation:**
- Setup issues → [GETTING_STARTED.md](GETTING_STARTED.md) → Troubleshooting
- Analysis questions → [docs/FRAMEWORK.md](docs/FRAMEWORK.md)
- Example questions → [docs/CASE_STUDY.md](docs/CASE_STUDY.md)
- Research questions → [docs/RESEARCH.md](docs/RESEARCH.md)

---

## ✨ Status

**Development:** ✅ Complete  
**Testing:** ✅ All systems verified  
**Documentation:** ✅ 25+ pages  
**Deployment:** ✅ Ready for production  
**Demo Data:** ✅ Included (TechCorp)  

**Next action:** Run `./run.sh` and open http://localhost:5173

---

**Last updated:** July 2024  
**Version:** 1.0  
**License:** MIT  

Enjoy! 🎯
