# Pay Equity Audit Framework: A 5-Step Methodology for Identifying and Remediating Wage Gaps

## Overview & Context

Pay equity audits are standard practice for large employers, but most are conducted using outdated methodologies that miss structural biases. This framework provides a defensible, reproducible approach to identifying wage gaps that account for legitimate job factors (role, level, tenure) while flagging inequitable compensation decisions.

This framework is designed for:
- Companies with 100+ employees across multiple roles and levels
- HR teams with access to compensation data
- Consultants building a pay equity audit capability
- Organizations preparing for external equity audits or litigation defense

**Outcome:** A documented report identifying wage gaps, root causes, and prioritized remediation recommendations.

### Why This Matters

**The Business Case:**
- **Wage gap exposure:** Companies with uncontrolled pay gaps face recruitment challenges, employee attrition, and reputational risk
- **Regulatory risk:** Multiple jurisdictions (US, UK, India) now mandate pay equity disclosure or auditing
- **Talent cost:** Fixing a 10% gap costs 2–3% of payroll; not fixing it costs 5–8% in turnover + legal

**Common Mistakes in Pay Equity Audits:**
1. **Using unadjusted gaps** — comparing men's avg salary to women's avg without accounting for role/level differences
2. **Ignoring occupational segregation** — women concentrated in lower-paying roles, which appears as wage gap even if pay decisions are fair
3. **No statistical rigor** — calling a 3% difference a "gap" when it's within normal noise
4. **No remediation plan** — identifying gaps but not fixing them

This framework addresses all four.

---

## STEP 1: DATA PREPARATION & VALIDATION

### What to Collect (Employee-Level Data)

**Minimum required:**
- ☑ Employee ID (anonymized)
- ☑ Job Title
- ☑ Job Level / Grade (e.g., L1–L5)
- ☑ Base Salary (in consistent currency)
- ☑ Tenure (years employed)
- ☑ Gender (self-reported or HR records)

**Recommended:**
- Department
- Location (city/country)
- Bonus (if applicable)
- Equity / Stock Options (if applicable)
- Hire Date
- Performance Rating (if comparing within level)

### Data Quality Checks

- **Duplicates:** Remove same employee listed twice
- **Missing values:** Mark as "Not Disclosed" rather than assuming
- **Outliers:** Flag extreme salaries (e.g., CEO at $5M vs. IC at $100K); analyze separately
- **Currency conversion:** If multi-country, convert to single currency using consistent rate
- **Consistency:** Ensure "Job Level" matches role (all SDEs with L3+, not L1)

**Output:** Clean dataset, ready for analysis. Document any decisions (e.g., "excluded 2 contractors; excluded C-suite").

---

## STEP 2: DESCRIPTIVE BREAKDOWN

Understanding the composition of your workforce.

### Key Outputs

**TABLE 1: Headcount by Role + Gender**
```
Role             Male    Female  Total      % Female
Software Eng     45      15      60         25%
Product Mgr      12      8       20         40%
Data Science     8       5       13         38%
Finance          5       7       12         58%
TOTAL            70      35      105        33%
```

**TABLE 2: Median Salary by Role + Gender**
```
Role             Male Median  Female Med.  Difference
Software Eng     ₹25L         ₹23L         -8%
Product Mgr      ₹35L         ₹34L         -3%
Data Science     ₹30L         ₹29L         -3%
Finance          ₹20L         ₹21L         +5%
```

### Key Insights to Document

- **Unadjusted gap:** Overall difference in median pay (all roles combined)
- **Occupational segregation:** Are women concentrated in lower-paying roles? (e.g., more women in Finance/HR, fewer in Eng)
- **Biggest gaps:** Which role has the largest gender pay difference?

---

## STEP 3: CONTROLLED WAGE GAP ANALYSIS

Comparing like-for-like roles (accounting for role/level differences).

### Rationale

If women are concentrated in lower-paying roles, the unadjusted gap is not discrimination; it's segregation. A "controlled" gap only compares people in identical or similar roles, isolating pay decisions.

**Methodology:** Based on Oaxaca (1973) wage decomposition.

### Method

For each role + level combination with N ≥ 5:
1. Calculate median salary for males
2. Calculate median salary for females
3. Adjusted gap = (Female Median - Male Median) / Male Median

### Example

**Role:** Software Engineer, Level 3  
**Males (n=8):** ₹23L, ₹24L, ₹25L, ₹25L, ₹26L, ₹27L, ₹28L, ₹30L → **Median = ₹25.5L**  
**Females (n=6):** ₹22L, ₹23L, ₹24L, ₹25L, ₹26L, ₹27L → **Median = ₹24.5L**  

**Controlled Gap** = (24.5 - 25.5) / 25.5 = **-3.9%**

### Interpretation

- **Negative** = women earn less (potential issue)
- **Positive** = women earn more (not an issue)
- **<2%** = noise, not significant
- **2–5%** = worth investigating
- **>5%** = flag for remediation

---

## STEP 4: FLAG OUTLIERS & IDENTIFY ROOT CAUSES

For each gap ≥ 2%, investigate:

### Questions to Ask

**1. Is it a seniority thing?**
- Compare tenure: Do underpaid women have less experience?
- If yes: Not discrimination, just natural pay progression
- If no: Potential issue

**2. Is it a performance thing?**
- Compare performance ratings: Are underpaid women rated lower?
- If yes: Legitimate (assuming ratings are unbiased)
- If no: Potential issue

**3. Is it a hire date thing?**
- Compare when hired: Did underpaid women join at lower salaries?
- If yes: Check if it's negotiation bias or banding issue
- If no: Potential issue

**4. Is it occupational segregation?**
- Are women concentrated in lower-paying sub-roles within the role?
- Example: Women are "backend engineers" (pays less), men are "AI/ML engineers" (pays more)

### Example Root Cause Analysis

**Gap:** SDE L3, -3.9% (women earn less)

| Factor | Analysis | Explains Gap? |
|--------|----------|---------------|
| **Tenure** | Women avg 2.5 yrs, Men avg 3.0 yrs | ✓ ~1.5% |
| **Performance** | Women avg 4.2, Men avg 4.3 | ✗ Minimal |
| **Hire date** | Women hired 6mo ago avg, Men hired 18mo ago | ✓ ~2% |
| **Result** | 3.9% gap mostly explained by tenure (newer hires earn less) | ✓ Monitor only |

---

vs.

**Gap:** Product Manager L2, -7.2% (women earn less)

| Factor | Analysis | Explains Gap? |
|--------|----------|---------------|
| **Tenure** | Women avg 4.5 yrs, Men avg 4.0 yrs | ✗ Women MORE senior |
| **Performance** | Women avg 4.5, Men avg 4.1 | ✗ Women outperform |
| **Hire date** | All hired 4+ years ago | ✗ No difference |
| **Result** | 7.2% gap is NOT explained by legitimate factors | ✗ **Immediate remediation** |

---

## STEP 5: REMEDIATION RECOMMENDATIONS & PRIORITIZATION

### Action Plan by Priority

**IMMEDIATE (Adjust within 90 days):**
- Gaps >5% with no valid explanation
- Gaps affecting high-retention-risk employees
- Gaps affecting leadership pipeline (underpaid high-performers)

**Cost formula:** Gap % × Salary × # of employees

**Example:** 7% gap for 1 Product Manager at ₹40L = ₹2.8L/year

**MEDIUM-TERM (Adjust within 6–12 months):**
- Gaps 2–5% with partial explanation
- Consolidate into annual salary review + merit budget

**MONITORING:**
- Gaps <2% or explained by tenure/performance
- Monitor in next audit (annual)

### Example Remediation Plan

| Issue | Action | Cost | Timeline | Rationale |
|-------|--------|------|----------|-----------|
| **3 female SDEs at L3** underpaid by avg 4% | Adjust to median L3 male salary | ₹3L/year | Next payroll | Tenure/performance don't explain gap |
| **1 female PM at L2** underpaid by 7% | Immediate adjustment to aligned level | ₹2.8L/year | Next month | High performer; new to role |
| **Finance team** (58% F) 3% lower avg | Investigate hiring/negotiation process | ₹0 | 60 days | May indicate systemic issue at source |

**Total Year 1 Immediate:** ₹7.5L (2.1% of payroll)

---

## How to Use This Framework

**For Consultants:**
1. Customize to your firm's methodology
2. Add case studies
3. Build a playbook for client implementation

**For Companies:**
1. Gather data per Step 1
2. Follow Steps 2–5 in order
3. Use remediation plan as board-approved action plan

### Questions This Framework Answers

✓ Do we have a pay gap?  
✓ Is it real or statistical noise?  
✓ What's causing it?  
✓ How much will it cost to fix?  
✓ What's the priority order?  

### Caveats

- This framework identifies wage gaps, **not discrimination** (legal determination)
- Results are only as good as input data quality
- Gender is binary in this framework (expand as needed)
- Does not account for protected leave, part-time status, or commissions (customize per org)

---

## References

**Academic Methodology:**
1. **Oaxaca, R. (1973).** "Male-Female Wage Differentials in Urban Labor Markets." *International Economic Review*, 14(3): 693–709.
   - Foundational paper on wage decomposition
   - Separates explained vs unexplained wage gaps
   - [Full text](https://www.jstor.org/stable/2525981)

2. **Blau, F. D., & Kahn, L. M. (2017).** "The Gender Wage Gap: Extent, Trends, and Explanations." *Journal of Economic Literature*, 55(3): 789–865.
   - Shows occupational segregation is major driver of gaps
   - Demonstrates gaps are most persistent at top of wage distribution
   - [Full text](https://www.aeaweb.org/articles?id=10.1257%2Fjel.20160995)

---

**Version:** 1.0  
**Last updated:** July 2024
