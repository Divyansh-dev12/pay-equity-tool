# Case Study: TechCorp Pay Equity Audit

## Scenario Setup

**Company:** TechCorp (hypothetical tech company)  
**Size:** 102 employees (after data cleaning)  
**Roles:** Software Engineer, Product Manager, Data Scientist, Finance, Design  
**Gender split:** 33% female, 67% male  
**Locations:** Delhi (60%), Bangalore (40%)  
**Analysis date:** July 2024  

---

## STEP 1: DATA PREPARATION & VALIDATION

### Output

```
✓ Data prepared: 102 employees
✓ Exclusions: 1 CEO (outlier), 2 contractors (not comparable)
✓ Final dataset: 102 employees
✓ No duplicates found
✓ No missing critical values
✓ 3 outliers flagged (analyzed separately)
✓ Data quality: PASS
```

### Key Findings

All employee records contain:
- ✓ Base salary (in consistent INR)
- ✓ Job title, level, and tenure
- ✓ Gender (self-reported)
- ✓ Department and location

---

## STEP 2: DESCRIPTIVE BREAKDOWN

### TABLE 1: Headcount by Role + Gender

| Role | Male | Female | Total | % Female |
|------|------|--------|-------|----------|
| Software Engineer | 28 | 7 | 35 | 20% |
| Product Manager | 12 | 6 | 18 | 33% |
| Data Scientist | 9 | 6 | 15 | 40% |
| Finance | 8 | 12 | 20 | 60% |
| Design | 7 | 7 | 14 | 50% |
| **TOTAL** | **64** | **38** | **102** | **37%** |

### TABLE 2: Median Salary by Role + Gender (INR, Lakhs)

| Role | Male Median | Female Median | Difference | Gap % |
|------|-------------|---------------|------------|-------|
| Software Engineer | ₹25.5L | ₹23.8L | -₹1.7L | -6.7% |
| Product Manager | ₹35.2L | ₹32.7L | -₹2.5L | -7.1% |
| Data Scientist | ₹28.1L | ₹27.9L | -₹0.2L | -0.7% |
| Finance | ₹19.8L | ₹20.5L | +₹0.7L | +3.5% |
| Design | ₹21.4L | ₹21.2L | -₹0.2L | -0.9% |

### Key Insights

**Overall unadjusted gap:** -5.2% (women earn 5.2% less on average)

**Occupational segregation observed:**
- ✗ Software Engineering is only 20% female (well below company average of 37%)
- ✓ Finance is 60% female (above company average)
- This segregation contributes ~2-3% of the overall unadjusted gap

**Biggest unadjusted gaps:**
1. Product Manager: -7.1%
2. Software Engineer: -6.7%

---

## STEP 3: CONTROLLED WAGE GAP ANALYSIS

Removing the effect of occupational segregation by analyzing like-for-like roles.

### Controlled Gaps by Role + Level

#### Software Engineer (all levels combined, N=35)
- Males (n=28): Median ₹25.5L
- Females (n=7): Median ₹23.8L
- **Controlled gap: -6.7%** ← FLAG (≥2%)

#### Product Manager (all levels combined, N=18)
- Males (n=12): Median ₹35.2L
- Females (n=6): Median ₹32.7L
- **Controlled gap: -7.1%** ← FLAG (≥2%)

#### Data Scientist (all levels combined, N=15)
- Males (n=9): Median ₹28.1L
- Females (n=6): Median ₹27.9L
- **Controlled gap: -0.7%** → OK (no action)

#### Finance (all levels combined, N=20)
- Males (n=8): Median ₹19.8L
- Females (n=12): Median ₹20.5L
- **Controlled gap: +3.5%** → OK (women earn more)

#### Design (all levels combined, N=14)
- Males (n=7): Median ₹21.4L
- Females (n=7): Median ₹21.2L
- **Controlled gap: -0.9%** → OK (no action)

### Summary

- **Gaps ≥2%:** 2 roles (Software Engineer -6.7%, Product Manager -7.1%)
- **Gaps 0.5–2%:** 1 role (Data Science -0.7%)
- **No gaps:** 2 roles (Finance +3.5%, Design -0.9%)
- **Total flagged:** 2 roles requiring investigation

---

## STEP 4: ROOT CAUSE ANALYSIS

### Finding 1: Software Engineer Gap (-6.7%)

**Employees affected:**
- 7 females, 28 males
- Female median: ₹23.8L
- Male median: ₹25.5L

**Root cause investigation:**

| Factor | Finding | Explains Gap? |
|--------|---------|---------------|
| **Tenure** | Females avg 2.1 yrs, Males avg 2.8 yrs | ✓ ~2.1% |
| **Performance** | Female avg rating 4.0, Male avg 4.1 | ✗ Minimal |
| **Level distribution** | Similar (most at L2/L3) | ✗ No |
| **Hire timing** | Similar hire dates (2021-2023) | ~ Partially |
| **Explained by factors above** | ~2% of 6.7% | **~30% explained** |
| **Unexplained residual** | ~4.7% gap remains | **70% UNEXPLAINED** |

**Assessment:** Partially explained by tenure (women are newer on average). However, 4.7% unexplained gap suggests:
1. Potential negotiation bias at hire (women hired at lower bands)
2. Slower salary progression for women
3. Occupational segregation within role (women in lower-paying specializations)

**Recommendation:** INVESTIGATE + MONITOR
- Review hiring offers for last 2 years (negotiation practices)
- Analyze specialization within role (backend vs. AI/ML vs. frontend)
- Plan adjustment if gap persists in next review cycle

---

### Finding 2: Product Manager Gap (-7.1%) ← CRITICAL

**Employees affected:**
- 6 females, 12 males
- Female median: ₹32.7L
- Male median: ₹35.2L

**Root cause investigation:**

| Factor | Finding | Explains Gap? |
|--------|---------|---------------|
| **Tenure** | Females avg 4.3 yrs, Males avg 4.1 yrs | ✗ Women MORE senior |
| **Performance** | Female avg rating 4.3, Male avg 4.0 | ✗ Women outperform |
| **Level distribution** | Similar (mostly L2/L3) | ✗ No |
| **Hire timing** | All hired 2020-2021 (similar) | ✗ No |
| **Explained by factors above** | None | **0% explained** |
| **Unexplained gap** | Full 7.1% gap | **100% UNEXPLAINED** |

**Assessment:** **7.1% gap is NOT explained by legitimate factors.** In fact:
- Women are MORE senior on average
- Women have HIGHER performance ratings
- Women are in identical level distribution

**This is a pay decision gap.**

Likely root causes:
1. **Negotiation bias:** Women hired at lower bands (not negotiated as aggressively)
2. **Promotion timing:** Men promoted faster despite equal tenure
3. **Salary increase patterns:** Men received larger raises over time

**Recommendation:** IMMEDIATE REMEDIATION
- Adjust 6 female PMs to male median (₹35.2L)
- Cost: ~₹15L additional per year (₹2.5L × 6 employees)
- Timeline: Next payroll cycle (30 days)
- Business case: Retention of high-performing PMs; avoid litigation risk

---

## STEP 5: REMEDIATION PLAN & PRIORITIZATION

### Action Plan

#### IMMEDIATE (Within 30 days)

**Action 1: Adjust Product Manager salaries**
- **Affected:** 6 female PMs at L2/L3
- **Current state:** ₹32.7L median
- **Target:** ₹35.2L (male median)
- **Cost:** ~₹15L/year (₹2.5L × 6 employees)
- **Timeline:** Next payroll cycle
- **Rationale:** 7% gap is unexplained by tenure/performance. Adjustment brings to equity, prevents flight risk, demonstrates commitment to fairness.
- **Success metric:** Year-over-year attrition in PM role should decrease

---

#### MEDIUM-TERM (Within 6 months)

**Action 2: Investigate Software Engineer compensation**
- **Affected:** 7 female Software Engineers
- **Current gap:** -6.7% (mostly explained by tenure, but 4.7% unexplained)
- **Investigation scope:**
  - Review hiring offers from 2021-2023: Did women negotiate less?
  - Analyze specialization within role: Are women in lower-paying sub-roles?
  - Check salary progression: Did women receive smaller raises?
- **Cost:** ~₹0 (audit + policy review)
- **Timeline:** Complete by Dec 2024
- **Remediation:** If gap is due to negotiation bias, adjust offers going forward + consider targeted raises

**Action 3: Hiring & Promotion Process Audit**
- **Scope:** Review PM and SDE hiring/promotion decisions for bias
- **Questions to answer:**
  - Do women negotiate less (or are offered lower bands)?
  - Are promotion timelines different by gender?
  - Are performance ratings applied consistently?
- **Cost:** $0 (internal HR audit)
- **Timeline:** Complete by Dec 2024
- **Owner:** HR + Finance

---

#### MONITORING (Ongoing)

**Action 4: Data Scientist, Finance, Design roles**
- **Finding:** No unexplained gaps (all <2%)
- **Action:** Monitor in annual audit
- **Timeline:** Next audit (July 2025)

---

### Financial Summary

| Timeline | Action | Cost | Type |
|----------|--------|------|------|
| **Immediate** | PM salary adjustment | ₹15L/year | Salary |
| **Medium-term** | SDE investigation + potential adjustment | ₹0-5L/year | TBD |
| **Medium-term** | Hiring process audit | ₹0 | Process |
| **Total Year 1** | | **₹15L** | Base adjustment |

**As % of payroll:** 15L ÷ (102 employees × ₹27L avg) = 5.4%

*(Note: This is front-loaded in Year 1; ongoing cost is ~2-3% of payroll for future adjustments)*

---

## Key Takeaways

✓ **Overall gap is 5.2%, but 70% is explained by occupational segregation** (women in lower-paying roles, not discrimination in pay decisions)

✓ **Controlled gaps identify the real issues:** 2 roles with unexplained gaps

✓ **Product Manager gap (7.1%) is critical:** 100% unexplained, affecting high-performing women → **Immediate action needed**

✓ **Software Engineer gap (6.7%) is partially explained:** Tenure accounts for ~2%, leaving ~4.7% unexplained → **Investigate root cause; monitor for negotiation bias**

✓ **Total cost to remediate:** ₹15L (4% of payroll) in Year 1, declining in subsequent years

✓ **Timeline:** PM adjustments within 30 days; full investigation complete by end of 2024

---

## Conclusion

This audit demonstrates how a systematic, methodology-driven approach identifies real pay equity issues that aggregate data masks. TechCorp's unadjusted gap of 5.2% appears significant, but controlled analysis shows only ~2 roles have unexplained gaps requiring immediate attention.

**The 5-step framework enables:**
- ✓ Defensible decisions backed by data
- ✓ Targeted remediation (not broad salary increases)
- ✓ Clear communication to leadership + employees
- ✓ Reduced litigation risk
- ✓ Demonstrated commitment to fair pay

**Recommendation:** Execute immediate PM adjustments, complete investigation by year-end, and repeat audit annually.

---

**Analysis prepared by:** Pay Equity Analyzer  
**Methodology:** Oaxaca (1973) wage decomposition  
**Date:** July 2024
