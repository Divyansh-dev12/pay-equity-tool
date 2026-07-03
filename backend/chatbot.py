"""
Pay-equity assistant — comprehensive rule-based engine covering 100+ CHRO questions.

Priority:
  1. TAUGHT answers  (what users corrected via the Teach button)
  2. LLM             (Claude, if ANTHROPIC_API_KEY is set)
  3. DATA queries    (reads employee rows for individual/aggregate queries)
  4. RULE answers    (100+ patterns covering all CHRO-level pay equity topics)
"""

import os
import re
import json
from typing import Dict, List, Optional

TAUGHT_FILE = os.path.join(os.path.dirname(__file__), 'taught_answers.json')
STOP = {'the', 'a', 'an', 'is', 'are', 'was', 'of', 'to', 'in', 'on', 'for', 'and',
        'or', 'what', 'who', 'whom', 'whose', 'which', 'how', 'me', 'my', 'our',
        'we', 'you', 'i', 'this', 'that', 'it', 'do', 'does', 'can', 'tell', 'show',
        'about', 'with', 'has', 'have', 'be', 'by', 'at', 's', 'employee', 'employees'}


# ------------------------------------------------------------------ helpers
def _isf(g): return str(g or '').strip().lower() in ('female', 'f')
def _ism(g): return str(g or '').strip().lower() in ('male', 'm')


def _lakh(n) -> str:
    try:
        v = float(n)
        sign = '-' if v < 0 else ''
        v = abs(v)
        if v >= 1_00_00_000:
            return f'{sign}₹{v/1_00_00_000:.2f} Cr'
        if v >= 1_00_000:
            return f'{sign}₹{v/1_00_000:.1f} L'
        return f'{sign}₹' + format(int(round(v)), ',d')
    except Exception:
        return '₹0'


def _pct(n) -> str:
    try:
        return f'{float(n):+.1f}%'
    except Exception:
        return '—'


def _mean(a): return sum(a) / len(a) if a else 0
def _median(a):
    if not a:
        return 0
    s = sorted(a); m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _keywords(q: str):
    return set(w for w in re.findall(r'[a-z0-9]+', (q or '').lower())
               if w not in STOP and len(w) > 2)


def _any(ql, *terms): return any(t in ql for t in terms)
def _word(ql, *terms):
    """Match whole-word terms only (avoids 'hi' matching 'which' or 'this')."""
    return any(re.search(r'\b' + re.escape(t) + r'\b', ql) for t in terms)


# ------------------------------------------------------------------ teaching store
def load_taught() -> List[Dict]:
    try:
        with open(TAUGHT_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def teach(question: str, answer: str) -> int:
    items = load_taught()
    items.append({'question': question, 'answer': answer,
                  'keywords': sorted(_keywords(question))})
    with open(TAUGHT_FILE, 'w') as f:
        json.dump(items, f, indent=2)
    return len(items)


def _match_taught(question: str) -> Optional[str]:
    kws = _keywords(question)
    if not kws:
        return None
    best, best_score = None, 0.0
    for it in load_taught():
        ik = set(it.get('keywords') or _keywords(it.get('question', '')))
        if not ik:
            continue
        score = len(kws & ik) / len(kws | ik)
        if score > best_score:
            best, best_score = it, score
    return best['answer'] if best and best_score >= 0.5 else None


# ------------------------------------------------------------------ data-aware queries
def _known_functions(ctx: Dict) -> List[str]:
    """Collect all unique function names from by_function list AND employee rows."""
    seen = {}
    for f in ctx.get('by_function', []):
        seen[f['name'].lower()] = f['name']
    for e in ctx.get('employees', []):
        fn = e.get('function', '')
        if fn:
            seen[fn.lower()] = fn
    return list(seen.values())


def _extract_filters(ql: str, ctx: Dict) -> Dict:
    filt = {}
    if re.search(r'\b(women|woman|female)\b', ql):
        filt['gender'] = 'Female'
    elif re.search(r'\b(men|man|male)\b', ql):
        filt['gender'] = 'Male'
    for fn in _known_functions(ctx):
        name = fn.lower()
        if name in ql or any(w in ql for w in name.split() if len(w) > 3):
            filt['function'] = fn
            break
    m = re.search(r'\bl([1-5])\b', ql)
    if m:
        filt['level'] = 'L' + m.group(1)
    return filt


def _scope(filt: Dict) -> str:
    tail = []
    if filt.get('function'):
        tail.append('in ' + filt['function'])
    if filt.get('level'):
        tail.append('at ' + filt['level'])
    if filt.get('gender'):
        who = 'women' if filt['gender'] == 'Female' else 'men'
        return ' among ' + who + ((' ' + ' '.join(tail)) if tail else '')
    return (' ' + ' '.join(tail)) if tail else ''


def _apply(emps, filt):
    out = emps
    if filt.get('gender') == 'Female':
        out = [e for e in out if _isf(e.get('gender'))]
    elif filt.get('gender') == 'Male':
        out = [e for e in out if _ism(e.get('gender'))]
    if filt.get('function'):
        out = [e for e in out if e.get('function') == filt['function']]
    if filt.get('level'):
        out = [e for e in out if e.get('level') == filt['level']]
    return out


def _describe(label, e, filt):
    line = (f"The {label} employee{_scope(filt)} is **{e.get('id','?')}** "
            f"({e.get('title','')}, {e.get('gender','')}) at {_lakh(e.get('salary',0))} fixed pay.")
    if e.get('cohort_median'):
        diff = e.get('salary', 0) - e['cohort_median']
        line += f" That is {_lakh(diff)} ({_pct(diff / e['cohort_median'] * 100)}) vs their cohort median."
    return line


def _data_answer(q: str, ctx: Dict) -> Optional[str]:
    emps = ctx.get('employees')
    if not emps:
        return None
    ql = q.lower()

    # Specific employee id
    idm = re.search(r'(emp\s*\d+)', ql)
    if idm:
        eid = idm.group(1).replace(' ', '').upper()
        e = next((x for x in emps if str(x.get('id', '')).upper() == eid), None)
        return _describe('requested', e, {}) if e else f"I couldn't find an employee with id {eid}."

    filt = _extract_filters(ql, ctx)
    subset = _apply(emps, filt)
    sals = [e.get('salary', 0) for e in subset]
    wants_pay = _any(ql, 'pay', 'salary', 'paid', 'earn', 'compensation', 'ctc', 'wage', 'income', 'fixed')

    # Lowest / highest paid
    if subset and _any(ql, 'lowest', 'least', 'minimum', 'bottom', 'worst paid', 'least paid') and (wants_pay or 'who' in ql):
        return _describe('lowest-paid', min(subset, key=lambda x: x.get('salary', 0)), filt)
    if subset and _any(ql, 'highest', 'most', 'maximum', 'top', 'best paid', 'most paid', 'highest paid') and (wants_pay or 'who' in ql):
        return _describe('highest-paid', max(subset, key=lambda x: x.get('salary', 0)), filt)

    # Counts
    if _any(ql, 'how many', 'count', 'number of', 'total number', 'how much people', 'headcount'):
        if _any(ql, 'below median', 'under median', 'below the median'):
            n = sum(1 for e in subset if e.get('below'))
            return f"**{n}** of {len(subset)} employees{_scope(filt)} are paid below their cohort median."
        if _any(ql, 'underpaid', 'flagged', 'below model', 'below prediction', 'below predicted'):
            n = sum(1 for e in subset if e.get('underpaid'))
            return f"**{n}** employees{_scope(filt)} are flagged as paid below the model's prediction."
        return f"There are **{len(subset)}** employees{_scope(filt)}."

    # Average / median pay
    if wants_pay and _any(ql, 'average', 'mean', 'typical', 'avg') and subset:
        fem = [e for e in subset if _isf(e.get('gender'))]
        mal = [e for e in subset if _ism(e.get('gender'))]
        base = f"The average fixed pay{_scope(filt)} is **{_lakh(_mean(sals))}** (across {len(subset)} people)."
        if fem and mal and not filt.get('gender'):
            base += f" Women: {_lakh(_mean([e.get('salary',0) for e in fem]))}, Men: {_lakh(_mean([e.get('salary',0) for e in mal]))}."
        return base
    if wants_pay and _any(ql, 'median') and subset:
        fem = [e for e in subset if _isf(e.get('gender'))]
        mal = [e for e in subset if _ism(e.get('gender'))]
        base = f"The median fixed pay{_scope(filt)} is **{_lakh(_median(sals))}** (across {len(subset)} people)."
        if fem and mal and not filt.get('gender'):
            base += f" Women: {_lakh(_median([e.get('salary',0) for e in fem]))}, Men: {_lakh(_median([e.get('salary',0) for e in mal]))}."
        return base

    # Pay range
    if wants_pay and _any(ql, 'range', 'spread', 'min to max', 'minimum to maximum', 'band') and subset:
        return (f"Pay range{_scope(filt)}: **{_lakh(min(sals))}** to **{_lakh(max(sals))}** "
                f"(median {_lakh(_median(sals))}, across {len(subset)} employees).")

    # Below median list
    if _any(ql, 'below median', 'under median') and subset:
        below = [e for e in subset if e.get('below')]
        if below:
            names = ', '.join(e.get('id', '?') for e in below[:8])
            more = f" …and {len(below)-8} more" if len(below) > 8 else ''
            return f"**{len(below)}** employees{_scope(filt)} sit below cohort median: {names}{more}."
        return f"No employees{_scope(filt)} are below their cohort median."

    # Underpaid / flagged list
    if _any(ql, 'underpaid', 'flagged', 'who needs a raise', 'who needs remediation', 'below model') and subset:
        flagged = [e for e in subset if e.get('underpaid')]
        if flagged:
            names = ', '.join(e.get('id', '?') for e in flagged[:8])
            more = f" …and {len(flagged)-8} more" if len(flagged) > 8 else ''
            return f"**{len(flagged)}** flagged for underpayment{_scope(filt)}: {names}{more}. See the remediation roster below."
        return f"No employees{_scope(filt)} are flagged as underpaid by the model."

    # Gender breakdown for a filtered subset
    if filt and _any(ql, 'breakdown', 'split', 'composition', 'gender', 'how many women', 'how many men') and subset:
        fem = [e for e in subset if _isf(e.get('gender'))]
        mal = [e for e in subset if _ism(e.get('gender'))]
        return (f"{len(subset)} employees{_scope(filt)}: **{len(fem)} women** "
                f"(median {_lakh(_median([e.get('salary',0) for e in fem]))}) and "
                f"**{len(mal)} men** (median {_lakh(_median([e.get('salary',0) for e in mal]))}).")

    # Named filter with pay question → full summary
    if filt and wants_pay and subset:
        return (f"For {len(subset)} employees{_scope(filt)}: median **{_lakh(_median(sals))}**, "
                f"average **{_lakh(_mean(sals))}**, range {_lakh(min(sals))}–{_lakh(max(sals))}.")

    if filt and not subset:
        return f"No employees match that filter{_scope(filt)}."
    return None


# ------------------------------------------------------------------ 100+ rule patterns
def _find_function(ql, by_function):
    for row in by_function:
        if row['name'].lower() in ql:
            return row
        for w in row['name'].lower().split():
            if len(w) > 3 and w in ql:
                return row
    return None


def _rule_answer(q: str, ctx: Dict) -> str:  # noqa: C901
    ql = q.lower().strip()
    method = ctx.get('method', 'regression')
    is_regression = method == 'regression'
    cg = ctx.get('controlled_gap_pct')
    ug = ctx.get('uncontrolled_gap_pct')
    r2 = ctx.get('r_squared')
    gap = ctx.get('gender_gap_vs_median_pct')
    by_fn = ctx.get('by_function', [])
    fc, mc = ctx.get('female_count', 0), ctx.get('male_count', 0)
    n_rem = ctx.get('remediation_count')
    cost_rem = ctx.get('remediation_cost')

    # ---- greeting / help ----
    if _word(ql, 'hi', 'hello', 'hey', 'help') or _any(ql, 'what can you', 'what do you do', 'capabilities', 'guide me'):
        return ("Hi! I answer from your **live pay equity data**. Ask me anything:\n"
                "• *Who is the lowest paid in Sales?*\n"
                "• *What is the controlled gap and why does it matter?*\n"
                "• *Which function should we fix first?*\n"
                "• *How much will remediation cost?*\n"
                "• *Is the gap statistically significant?*\n"
                "• *What should I tell the board?*\n"
                "• *What is the business case for fixing this?*\n"
                "Hit **✏️ Teach me** on any answer to correct or personalise it.")

    # ---- single function deep-dive ----
    comparative = _any(ql, 'worst', 'biggest', 'largest', 'best', 'most fair', 'which function',
                       'compare all', 'all function', 'each function', 'every function')
    fn_obj = _find_function(ql, by_fn)
    if fn_obj and not comparative:
        gk = 'adjusted_gap_pct' if 'adjusted_gap_pct' in fn_obj else 'gap_vs_median_pct'
        g = fn_obj.get(gk, 0)
        parts = [f"**{fn_obj['name']}**: like-for-like gap of **{_pct(g)}**."]
        if fn_obj.get('female_median') and fn_obj.get('male_median'):
            parts.append(f"Women median {_lakh(fn_obj['female_median'])} vs men {_lakh(fn_obj['male_median'])}.")
        if fn_obj.get('verdict'):
            parts.append(fn_obj['verdict'])
        severity = 'Needs attention.' if abs(g) > 5 else 'Monitor.' if abs(g) > 2 else 'Healthy range.'
        parts.append(severity)
        return ' '.join(parts)

    # ---- all functions summary ----
    if _any(ql, 'all function', 'every function', 'each function', 'function summary',
            'function breakdown', 'compare function', 'list function', 'function gap', 'by function'):
        if by_fn:
            gk = 'adjusted_gap_pct' if 'adjusted_gap_pct' in by_fn[0] else 'gap_vs_median_pct'
            lines = [f"• **{f['name']}**: {_pct(f.get(gk, 0))}" for f in sorted(by_fn, key=lambda x: x.get(gk, 0))]
            return "Pay gap by function (most negative = women paid less):\n" + '\n'.join(lines)

    # ---- worst / biggest gap function ----
    if _any(ql, 'worst', 'biggest gap', 'largest gap', 'most concerning', 'highest gap',
            'where is the problem', 'where should we focus', 'most urgent', 'priority area',
            'where is the issue', 'biggest problem', 'red flag', 'alarming', 'most severe'):
        w = ctx.get('worst_function')
        if w:
            g = w.get('adjusted_gap_pct', w.get('gap_vs_median_pct', 0))
            return (f"The biggest gap is in **{w['name']}** at **{_pct(g)}**. "
                    f"This is where remediation should start — run a root-cause review on pay-setting practices "
                    f"and offers made in this function. Check whether the gap is at a specific level (L3/L4) or spread across all levels.")

    # ---- best / most equitable function ----
    if _any(ql, 'best', 'most equitable', 'most fair', 'smallest gap', 'doing well',
            'model department', 'exemplary', 'good example', 'benchmark internally', 'leading'):
        b = ctx.get('best_function')
        if b:
            g = b.get('adjusted_gap_pct', b.get('gap_vs_median_pct', 0))
            return (f"**{b['name']}** is the most equitable function at **{_pct(g)}**. "
                    f"Study what they're doing differently — structured pay bands, transparent levelling, "
                    f"or manager training. Use it as an internal proof point and benchmark for other functions.")

    # ---- controlled / like-for-like gap ----
    if _any(ql, 'controlled', 'like-for-like', 'like for like', 'adjusted gap', 'comparable',
            'same job', 'apples to apples', 'after controlling', 'after adjustment', 'unexplained',
            'explained gap', 'role-adjusted', 'level-adjusted', 'holding everything'):
        if cg is not None:
            severity = 'significant and requires immediate action' if abs(cg) > 5 else \
                       'moderate — worth a structured remediation plan' if abs(cg) > 2 else \
                       'relatively small but worth monitoring'
            direction = 'women earn less than men' if cg < 0 else 'women earn more than men'
            return (f"The **controlled (like-for-like) gap is {_pct(cg)}** — this is the pay difference between "
                    f"two people doing the *same* job at the *same* level, with the same tenure, performance, function, and location. "
                    f"In plain terms: {direction} even in identical roles. At {abs(cg):.1f}%, this is **{severity}**. "
                    f"This is the number that matters for pay equity action — not the raw gap.")
        return "The controlled gap isn't available in this view. Switch to the Regression model for the like-for-like number."

    # ---- uncontrolled / raw gap ----
    if _any(ql, 'uncontrolled', 'raw gap', 'overall gap', 'unadjusted', 'total gap', 'headline gap',
            'surface level', 'basic difference', 'simple gap', 'plain gap', 'gross gap'):
        if ug is not None:
            return (f"The **uncontrolled (raw) gap is {_pct(ug)}** — this is the simple average pay difference "
                    f"before accounting for job level, role, or experience. It blends two separate issues: "
                    f"(1) direct pay unfairness for the same role, and "
                    f"(2) representation gaps (fewer women in senior roles). "
                    f"A large raw gap with a small controlled gap typically means the problem is pipeline — "
                    f"not enough women at senior levels — rather than direct pay discrimination.")
        return "The uncontrolled gap isn't available here. Check the Regression model which shows both raw and controlled gaps."

    # ---- difference between controlled and uncontrolled ----
    if ('difference between' in ql and _any(ql, 'controlled', 'uncontrolled', 'raw', 'adjusted')) or \
       (_any(ql, 'controlled') and _any(ql, 'uncontrolled', 'raw')) or \
       _any(ql, 'two gap', 'two number', 'why two', 'gap mean', 'what does gap mean', 'explain gap'):
        if cg is not None and ug is not None:
            diff = abs(ug - cg)
            return (f"**Raw gap ({_pct(ug)})** = plain pay difference before accounting for role or seniority. "
                    f"It includes both representation effects and actual pay inequity.\n\n"
                    f"**Controlled gap ({_pct(cg)})** = the gap for two people doing the *same* job at the *same* level "
                    f"with the same profile — like-for-like. This isolates direct pay discrimination.\n\n"
                    f"The gap narrows by {diff:.1f}pp from raw to controlled, meaning most of the difference "
                    f"is driven by **job composition** (representation), not direct pay unfairness. "
                    f"Both need fixing: controlled gap via pay corrections, raw gap via promotion pipeline.")
        return ("**Raw gap** = plain difference before role/seniority adjustment. "
                "**Controlled gap** = same job, level, tenure, performance, location — pure pay inequity. "
                "Large raw + small controlled = pipeline problem. Large controlled = direct pay problem.")

    # ---- R² / model quality ----
    if _any(ql, 'r2', 'r²', 'r squared', 'model accuracy', 'model fit', 'model quality',
            'how reliable', 'how accurate', 'variance explained', 'trust the model',
            'confident in the model', 'model strength', 'explain variance', 'how much does model explain'):
        if r2 is not None:
            quality = ('excellent — highly reliable controlled gap' if r2 >= 0.8 else
                       'strong fit' if r2 >= 0.7 else
                       'good fit' if r2 >= 0.6 else
                       'moderate — consider adding more variables')
            tip = '' if r2 >= 0.7 else ' Consider adding role family or sub-function as a variable to improve fit.'
            return (f"R² is **{r2:.2f}** — the model explains **{r2*100:.0f}% of why pay differs** between employees "
                    f"using level, tenure, performance, function, and location. That's a **{quality}**.{tip} "
                    f"The higher R², the more confident you can be that the controlled gap is real, not noise.")
        if not is_regression:
            return ("The median model has no R² — it directly compares each person to their cohort median without fitting "
                    "a regression. No accuracy metric needed: if your pay is ₹10L and the cohort median is ₹12L, "
                    "you're 16.7% below — fully transparent, no model trust required.")

    # ---- p-value / statistical significance ----
    if _any(ql, 'p-value', 'p value', 'statistically significant', 'significance level',
            'is the gap real', 'is the gap significant', 'chance', 'random', 'conclusive', 'proven',
            'confidence interval', 'noise', 'margin of error', 'significant at'):
        if cg is not None:
            return (f"Statistical significance tells you whether the gap is real or just random variation. "
                    f"A p-value below 0.05 means less than 5% chance this gap appeared by chance — it's real. "
                    f"Your controlled gap is {_pct(cg)}. Check the **Model details (coefficients)** section "
                    f"at the bottom of the page — the gender row shows the exact p-value. "
                    f"If p {'<' } 0.05, the gap is statistically significant and legally/operationally actionable.")
        return "Check the Model details (coefficients) section — the gender row p-value below 0.05 means a statistically significant gap."

    # ---- gender coefficient ----
    if _any(ql, 'gender coefficient', 'gender penalty', 'female coefficient', 'gender factor',
            'gender variable', 'gender impact on pay', 'what does gender show in model'):
        if cg is not None:
            return (f"The gender coefficient in the regression is **{_pct(cg)}** — this is the controlled gap. "
                    f"It's the pay premium or penalty associated purely with being female, after holding level, tenure, "
                    f"performance, function, and location constant. "
                    f"{'Negative = women paid less for equivalent work.' if cg < 0 else 'Positive = women paid more for equivalent work.'} "
                    f"See exact value and p-value in the Model details section.")
        return "The gender coefficient is in the Model details (coefficients) section at the bottom of this page."

    # ---- what drives pay / coefficients ----
    if _any(ql, 'coefficient', 'what drives pay', 'factor', 'driver', 'what explains pay',
            'what determines pay', 'what affect pay', 'pay driver', 'level impact', 'tenure impact',
            'performance impact', 'how does level affect', 'how much does'):
        return ("The model learns **how much each factor contributes to pay**. Typically:\n"
                "• **Job level** is the single biggest driver — L4 vs L1 gap is often 3-5×.\n"
                "• **Job function** is second — Engineering typically pays 30-50% more than HR at the same level.\n"
                "• **Tenure** adds an increment per year — the coefficient shows the ₹ value per year.\n"
                "• **Performance rating** adds a merit premium.\n"
                "• **Location** adjusts for city cost of living.\n"
                "• **Gender coefficient** = the unexplained gap after all above are controlled. That's your pay equity number.\n"
                "See the full breakdown in the **Model details (coefficients)** section.")

    # ---- model methodology ----
    if _any(ql, 'how does the model work', 'how does regression work', 'methodology', 'explain the model',
            'ols', 'ordinary least squares', 'multiple regression', 'how is gap calculated',
            'how calculated', 'formula', 'math behind', 'technically how', 'model work'):
        return ("**How the regression model works:**\n"
                "1. Every employee's base salary is the dependent variable.\n"
                "2. We fit an OLS (Ordinary Least Squares) regression: salary = β₀ + β₁·level + β₂·tenure + β₃·performance + β₄·function + β₅·location + β₆·gender + ε.\n"
                "3. The model learns the 'price' of each factor — e.g. β₂ tells you how much each year of tenure adds to predicted pay.\n"
                "4. The **gender coefficient (β₆)** is the pay difference *after all other factors are held equal* — that's the controlled gap.\n"
                "5. Each employee's predicted salary is computed. Those paid >15% below prediction are flagged for remediation.\n"
                "6. R² tells you how well the model fits your actual pay data.")

    # ---- representation / workforce composition ----
    if _any(ql, 'representation', 'diversity', 'workforce composition', 'gender split', 'gender ratio',
            'percentage women', 'percentage female', 'what percent', 'how diverse', 'gender mix',
            'female percentage', 'women percentage'):
        if fc + mc:
            fem_pct = fc / (fc + mc) * 100
            return (f"**{fc} women, {mc} men** ({fem_pct:.0f}% women). "
                    f"Women's median pay: {_lakh(ctx.get('female_median', 0))}, "
                    f"Men's median pay: {_lakh(ctx.get('male_median', 0))}. "
                    f"Check whether representation at L4/L5 mirrors overall representation — "
                    f"a gap at senior levels is the main driver of the uncontrolled pay gap.")

    # ---- remediation cost ----
    if _any(ql, 'remediation cost', 'cost to fix', 'how much will it cost', 'budget needed',
            'total budget', 'investment needed', 'fix budget', 'salary budget', 'raise budget',
            'cost of closing', 'what will it cost', 'how much to fix', 'fixing cost'):
        if n_rem is not None and cost_rem is not None:
            return (f"Closing the gaps for the **{n_rem} employees** flagged as underpaid costs approximately "
                    f"**{_lakh(cost_rem)} per year** in additional fixed pay. "
                    f"This is the minimum to bring all flagged employees to their model-predicted pay. "
                    f"Note: this is fixed pay only — add ~15-20% for employer PF/gratuity contributions. "
                    f"The number is typically a fraction of the business risk from attrition and legal exposure.")
        return "The remediation cost isn't available in the current view. Check the Regression model for underpaid count and total cost."

    # ---- who needs remediation ----
    if _any(ql, 'who needs', 'who should get', 'who is underpaid', 'flagged employee',
            'underpaid people', 'need a raise', 'who to prioritize', 'remediation list',
            'who needs salary', 'salary increase list', 'who to fix first'):
        if n_rem is not None:
            return (f"**{n_rem} employees** are flagged as paid below the model's prediction. "
                    f"Total remediation: ~{_lakh(cost_rem or 0)}/yr. "
                    f"See the **Remediation roster** table on this page — sorted by shortfall size. "
                    f"**Prioritise**: (1) largest % shortfall, (2) flagged women, (3) high performers. "
                    f"Address the top 20 in the current review cycle; budget the rest for the next cycle.")
        return "The remediation roster is in the Regression model view. It lists every employee paid below model prediction."

    # ---- how to prioritise remediation ----
    if _any(ql, 'prioritize', 'prioritise', 'where to start', 'sequence', 'order of priority',
            'which employees first', 'triage', 'most urgent employees', 'remediation plan'):
        return ("**Remediation prioritisation framework:**\n"
                "1. **Largest % shortfall** — employees furthest below their predicted pay face the highest unfairness and attrition risk.\n"
                "2. **High performers paid below median** — they have the most market options; fix their pay first.\n"
                "3. **Women at L3+ in functions with the largest gap** — senior women drive the biggest downstream impact.\n"
                "4. **Functions with the largest controlled gap** — systemic functions need structural fixes (pay bands), not just individual raises.\n"
                "Set a hard deadline: all corrections in within one quarter of the audit.")

    # ---- recommended actions / next steps ----
    if _any(ql, 'recommend', 'what should', 'next step', 'action plan', 'advice', 'suggest',
            'do next', 'roadmap', 'strategy', 'how to fix', 'how to close', 'improve pay equity',
            'what to do', 'fix this', '90 days', 'immediate', 'what now', 'plan of action',
            'action item', 'intervention'):
        rec = ctx.get('recommendation') or {}
        if rec.get('actions'):
            return (f"**{rec.get('pattern', 'Recommended actions')}** (severity: {rec.get('severity', '—')}).\n"
                    + '\n'.join(f'• {a}' for a in rec['actions']))
        return ("**Immediate actions for pay equity:**\n"
                "• Raise pay for all employees flagged below model prediction — set a 60-day deadline.\n"
                "• Focus on the highest-gap function first — root-cause review + pay band introduction.\n"
                "• Set structured pay bands (min/mid/max) by level to prevent future drift.\n"
                "• Train hiring managers on offer-setting: require documented justification for sub-band offers.\n"
                "• Schedule quarterly monitoring with this same model.")

    # ---- what to tell the board / leadership ----
    if _word(ql, 'board') or _any(ql, 'tell leadership', 'tell the ceo', 'chro report', 'executive brief',
            'c-suite', 'stakeholder', 'present this', 'communicate to leadership', 'narrative',
            'story to tell', 'how to explain', 'pitch', 'top line', 'board pack', 'brief the board'):
        lines = ["**Board-ready narrative:**"]
        if ug is not None:
            lines.append(f"• Our raw gender pay gap is **{_pct(ug)}** — reflects both pay and representation differences.")
        if cg is not None:
            lines.append(f"• The like-for-like gap (same role, level, profile) is **{_pct(cg)}** — this is the direct equity issue.")
        if n_rem and cost_rem:
            lines.append(f"• **{n_rem} employees** require salary corrections at ~**{_lakh(cost_rem)}/yr** total.")
        lines.append("• We have a clear remediation plan with timelines and budget already quantified.")
        lines.append("• Our most equitable function proves it's achievable — we're scaling those practices.")
        if r2:
            lines.append(f"• Methodology is rigorous: OLS regression with R²={r2:.2f} — statistically sound.")
        return '\n'.join(lines)

    # ---- legal / compliance ----
    if _any(ql, 'legal', 'law', 'compliance', 'regulation', 'audit risk', 'liability',
            'equality', 'pay transparency law', 'mandatory', 'required by law', 'fine', 'penalty',
            'labour law', 'labor law', 'statutory', 'reportable', 'legal risk', 'sue'):
        return ("**Legal & compliance context (India):**\n"
                "• **Equal Remuneration Act (1976)** mandates equal pay for equal work across gender — a significant controlled gap is legally actionable.\n"
                "• **SEBI BRSR** (Business Responsibility & Sustainability Reporting): listed companies (top 1000 by market cap) must disclose gender pay gap metrics.\n"
                "• Several state labour departments are increasing enforcement of equal remuneration provisions.\n"
                "• A documented audit with a remediation plan is your best legal defence — it shows good faith.\n"
                "• Proactively fixing gaps reduces litigation risk, improves BRSR scores, and protects employer brand.")

    # ---- ESG / investor / ratings ----
    if _any(ql, 'esg', 'investor', 'esg rating', 'brsr', 'sustainability report', 'responsible',
            'glassdoor', 'employer brand', 'msci', 'sustainalytics', 'rating agency'):
        return ("Pay equity is a **Tier-1 ESG metric**. Investors and rating agencies (MSCI, Sustainalytics, BRSR) score on:\n"
                "1. Whether a gap exists (and its size)\n"
                "2. Whether you've measured it rigorously\n"
                "3. Whether you have a remediation plan with timelines\n"
                "Publishing your controlled gap with a remediation timeline is a **positive ESG signal** even if the current gap is non-zero — "
                "it signals governance maturity. Companies with no disclosed audit are scored more harshly than those that disclose and plan.")

    # ---- business case / ROI ----
    if _any(ql, 'why does this matter', 'business case', 'why should we', 'roi', 'return on investment',
            'impact of pay equity', 'why pay equity', 'benefit of fixing', 'cost of inaction', 'why bother'):
        return ("**Business case for pay equity:**\n"
                "• **Attrition cost**: underpaid high performers — typically women — are most likely to leave. "
                "Replacing a senior hire costs 6-18 months of salary.\n"
                "• **Legal exposure**: a significant controlled gap is actionable under the Equal Remuneration Act.\n"
                "• **Talent acquisition**: 73% of candidates now research pay equity before accepting offers (LinkedIn 2024).\n"
                "• **ESG/BRSR score**: investors and institutions explicitly rate pay equity governance.\n"
                "• **Productivity**: pay fairness is a top-3 driver of employee trust and engagement.\n"
                "The remediation cost is typically 0.1-0.5% of total payroll — far less than the liability.")

    # ---- attrition / retention risk ----
    if _any(ql, 'attrition', 'retention', 'turnover', 'resign', 'leave', 'flight risk',
            'who might leave', 'turnover risk', 'losing employees', 'talent risk', 'employee risk'):
        if n_rem:
            return (f"The **{n_rem} employees flagged as underpaid** are your highest attrition risk — "
                    f"especially those who are high performers. They have the best market options and the most to gain from leaving. "
                    f"Research shows underpaid employees are 2.8× more likely to job-search actively. "
                    f"Fixing their pay now costs {_lakh(cost_rem or 0)}/yr; losing and replacing them could cost 5-10× that.")
        return ("Employees paid significantly below their predicted or cohort median are at elevated attrition risk. "
                "High performers who are underpaid have both the motivation and the market options to leave. "
                "Pay equity remediation is retention spending — not just a fairness exercise.")

    # ---- pipeline / representation gap ----
    if _any(ql, 'pipeline', 'women in leadership', 'senior women', 'gender pipeline',
            'leadership diversity', 'representation at senior', 'progression gap', 'promotion gap',
            'fewer women at top', 'glass ceiling'):
        return ("A large **raw gap** with a small **controlled gap** is the pipeline signal — "
                "women are underrepresented in senior, higher-paying roles.\n"
                "To close the pipeline gap:\n"
                "• Track **promotion rates** by gender — are women advancing at the same rate?\n"
                "• Audit **stretch assignment and sponsorship** practices — do women get equal access?\n"
                "• Set **representation targets** for L4+ and hold business leaders accountable.\n"
                "• Check whether part-time / flexible work policies inadvertently cap women's level progression.")

    # ---- pay bands / structure ----
    if _any(ql, 'pay band', 'salary band', 'pay range', 'salary structure', 'grade',
            'pay scale', 'pay grid', 'compensation structure', 'band width', 'midpoint', 'salary range'):
        return ("Pay bands (salary ranges per level/function) are the **most effective structural fix** for pay equity. "
                "They constrain manager discretion in offer-setting — the largest source of gap creation.\n"
                "**Best practice:**\n"
                "• Set min/mid/max per level. Use the median model output as the midpoint anchor.\n"
                "• Require documented justification for any offer outside the band.\n"
                "• Flag outliers quarterly via this model — anyone below band minimum gets immediate correction.\n"
                "• Publish band ranges to employees (pay transparency reduces negotiation-based gaps).")

    # ---- pay transparency ----
    if _any(ql, 'pay transparency', 'salary transparency', 'open salary', 'publish salaries',
            'share pay ranges', 'disclose ranges', 'tell employees their range', 'share bands'):
        return ("Pay transparency — sharing salary ranges with employees — reduces negotiation-based gaps, "
                "one of the leading causes of the controlled gap. "
                "Options from low to high transparency:\n"
                "1. **Band ranges on job postings** (most common, low risk)\n"
                "2. **Share band ranges with current employees** on request\n"
                "3. **Publish full band table** internally\n"
                "Research shows even step 1 narrows the pay gap by 2-4pp over 3 years. "
                "Several EU countries mandate step 1-2 — India is likely to follow.")

    # ---- communication to employees ----
    if _any(ql, 'communicate to employees', 'tell employees', 'share with team', 'employee transparency',
            'employee communication', 'how to talk to staff', 'what to say to staff', 'disclose to employees'):
        return ("**Employee communication guidance:**\n"
                "• **Do acknowledge** you've run an audit — silence signals inaction and erodes trust.\n"
                "• Share the **controlled gap** (not the raw gap) — the raw gap can mislead without context.\n"
                "• Explain what factors were controlled for — employees deserve to understand the methodology.\n"
                "• Share your **remediation timeline and commitment** to quarterly monitoring.\n"
                "• Avoid sharing individual comparisons publicly — handle individually via HR/manager 1:1.\n"
                "• Frame it as: 'We found an issue, we're fixing it, here's the timeline.' Not 'We're clean.'")

    # ---- how often to run ----
    if _any(ql, 'how often', 'frequency', 'when to run', 'quarterly', 'annual cycle', 'schedule audit',
            'review cycle', 'recurring', 'repeat', 'run again', 'when to re-run'):
        return ("**Recommended audit cadence:**\n"
                "• **Annual deep audit** — full regression + median model after the performance review cycle. "
                "Catches structural drift and gives budget time to remediate.\n"
                "• **Quarterly spot-check** — median model run to catch drift between full audits.\n"
                "• **Trigger-based audit** — run after: M&A integration, major org restructure, or when attrition spikes in a function.\n"
                "• Tie the annual audit to the compensation review cycle so remediation costs are built into the next budget.")

    # ---- tenure ----
    if _any(ql, 'tenure', 'years of service', 'experience effect', 'seniority premium',
            'how long employed', 'does tenure matter', 'experience premium', 'tenure gap',
            'years of experience'):
        return ("Tenure is one of the **legitimate pay drivers** the model controls for — "
                "employees with longer tenure typically earn more, and that's factored out. "
                "If men in your company have systematically longer average tenure, it partially explains "
                "the raw gap without being discriminatory. "
                "**What to watch:** if women have shorter tenure *because* they leave due to undervaluation, "
                "that's a systemic issue — attrition itself becomes a pay equity problem. "
                "Check the gender coefficient (controlled gap) — if it's still negative after tenure is controlled, "
                "that's direct pay discrimination, not just a tenure effect.")

    # ---- performance ----
    if _any(ql, 'performance rating', 'rating impact', 'high performer paid', 'low performer',
            'appraisal impact', 'does performance matter', 'performance coefficient',
            'performance and pay', 'merit pay'):
        return ("Performance rating is **controlled for** in the regression model — so a high-rated woman is only "
                "compared to a high-rated man at the same level. The gap can't be explained away by 'men perform better.'\n"
                "Things to check:\n"
                "• Are women rated lower on average despite equivalent output? (rating bias)\n"
                "• Does the performance coefficient make sense — is high performance clearly rewarded?\n"
                "• Are all employees on the same rating scale? Inconsistent scales across functions pollute results.")

    # ---- what is median model ----
    if not is_regression and _any(ql, 'how does median', 'median model work', 'how is position calculated',
                                  'cohort', 'what is cohort', 'how cohort defined', 'benchmark source'):
        return ("**How the median model works:**\n"
                "1. Employees are grouped into **cohorts** (function × level) — e.g. 'Engineering L3'.\n"
                "2. For each cohort, a median salary is calculated — either from your uploaded benchmark CSV "
                "or computed directly from your employee data.\n"
                "3. Each employee's position vs median is: (their salary − cohort median) / cohort median × 100%.\n"
                "4. **0% = exactly at median**. Positive = above, negative = below.\n"
                "5. The gender gap is women's average position minus men's average position across all cohorts.\n"
                "No statistics or model assumptions required — 100% transparent and easy to explain.")

    # ---- model comparison ----
    if _any(ql, 'which model should', 'regression vs median', 'median vs regression',
            'difference between model', 'which is better model', 'when to use which model',
            'both models', 'compare models', 'choose model'):
        return ("**Regression vs Median — when to use each:**\n\n"
                "**Regression (more rigorous):**\n"
                "• Controls for tenure, performance, location — gives the purest controlled gap.\n"
                "• Best for CHRO, board, legal, and regulator presentations.\n"
                "• Can flag individual employees paid below model prediction.\n"
                "• Requires interpretation (R², p-values, coefficients).\n\n"
                "**Median (simpler, transparent):**\n"
                "• Direct comparison: 'here's your cohort median, here's where you sit.'\n"
                "• Best for line-manager conversations and employee-facing communication.\n"
                "• Easy to upload your own market medians.\n"
                "• No model assumptions — any CHRO can defend it without a stats background.\n\n"
                "**Use both**: regression for governance decisions, median for communication.")

    # ---- gender gap summary ----
    if _any(ql, 'what is our gap', 'what is the gap', 'our pay gap', 'gender pay gap',
            'overall pay gap', 'headline number', 'bottom line', 'tldr', 'summary',
            'what is the pay equity situation', 'give me the overview', 'quick summary'):
        if cg is not None and ug is not None:
            flag = 'warrants remediation' if abs(cg) > 3 else 'manageable but worth monitoring'
            return (f"**Pay equity summary:**\n"
                    f"• **Raw gap: {_pct(ug)}** — plain difference before adjustment (includes representation effects).\n"
                    f"• **Controlled gap: {_pct(cg)}** — same role, level, tenure, performance, location.\n"
                    f"• A controlled gap of {_pct(cg)} means women in identical roles earn {abs(cg):.1f}% "
                    f"{'less' if cg < 0 else 'more'} than men — this **{flag}**.\n"
                    f"• Model fit: R² = {r2:.2f if r2 else '—'} — {'reliable' if r2 and r2 >= 0.65 else 'moderate'}.")
        if gap is not None:
            return (f"**Median model summary:**\n"
                    f"• Gender gap vs median: **{_pct(gap)}** (women's average position minus men's).\n"
                    f"• {ctx.get('female_below_median_pct', '?')}% of women are below cohort median vs "
                    f"{ctx.get('male_below_median_pct', '?')}% of men.")

    # ---- median model gap ----
    if not is_regression and _any(ql, 'median', 'position', 'below median', 'cohort median',
                                  'vs median', 'against median', 'above median', 'median gap'):
        if gap is not None:
            return (f"Against the median line, the gender gap is **{_pct(gap)}**. "
                    f"{ctx.get('female_below_median_pct', '?')}% of women are below their cohort median vs "
                    f"{ctx.get('male_below_median_pct', '?')}% of men. "
                    f"Each cohort is defined as function × level, so Sales L2 women are compared only to Sales L2 peers.")

    # ---- sample / synthetic data ----
    if _any(ql, 'sample data', 'synthetic data', 'test data', 'fake data', 'is this real data',
            'how was data generated', 'generate data', '340 employees', 'demo data'):
        return ("The sample dataset is **synthetic Indian compensation data** with 340 employees across 8 functions "
                "(Sales, Engineering, Product Management, HR, Finance, Operations, Marketing, Legal) at levels L1–L5. "
                "It's designed with deliberate pay equity scenarios: some functions are fair, some deliberately favour men, "
                "some favour women — so all model outputs have meaningful numbers to explore. "
                "Upload your own CSV to analyze your real workforce.")

    # ---- data upload / what data needed ----
    if _any(ql, 'what data do', 'data needed', 'data required', 'what columns', 'what fields',
            'upload format', 'csv format', 'template', 'data format', 'input format', 'what to upload'):
        return ("**Required columns for the employee CSV:**\n"
                "`employee_id`, `job_title`, `job_level` (L1–L5), `base_salary` (annual fixed pay in INR), "
                "`gender` (Male/Female), `job_function`, `location`, `tenure_years`, `performance_rating`\n\n"
                "**Median model additionally:** a second CSV with `job_function`, `job_level`, `median_salary` "
                "(your market benchmark — or leave blank and the model computes from your data).\n\n"
                "Download the template directly from the upload screen.")

    # ---- fallback ----
    if cg is not None:
        return (f"The controlled (like-for-like) gap is **{_pct(cg)}**. "
                f"I can answer questions about: what this number means, which function to fix first, "
                f"remediation cost and prioritisation, statistical significance, what to tell the board, "
                f"legal compliance, specific employees (try: *'who is lowest paid in Sales?'*), "
                f"or how the model works. What would you like to know?")
    if gap is not None:
        return (f"The gender gap vs median is **{_pct(gap)}**. Ask me about: a specific function, "
                f"specific employees, who's below median, the remediation plan, what to tell leadership, "
                f"or how the median model works.")
    return ("Ask me about the pay gap, a specific function, individual employees, remediation cost, "
            "what to tell the board, legal compliance, or how the model works.")


# ------------------------------------------------------------------ optional LLM
def _llm_answer(question: str, ctx: Dict) -> str:
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        return ''
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        # Trim employees list to keep context small
        ctx_trim = {k: v for k, v in ctx.items() if k != 'employees'}
        if ctx.get('employees'):
            ctx_trim['employees_count'] = len(ctx['employees'])
            ctx_trim['employees_sample'] = ctx['employees'][:10]
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=600,
            system=("You are a senior compensation & benefits analyst with expertise in pay equity. "
                    "Answer ONLY from the JSON context provided — never invent figures not present. "
                    "Be specific, quantitative, and actionable. Use ₹ for Indian rupees. "
                    "Format with **bold** for key numbers."),
            messages=[{"role": "user", "content": f"Context:\n{json.dumps(ctx_trim)}\n\nQuestion: {question}"}],
        )
        return msg.content[0].text
    except Exception:
        return ''


def _resolve_with_history(question: str, history: List[Dict]) -> str:
    """Expand a vague follow-up using recent conversation history."""
    ql = question.lower().strip()
    followup_triggers = ['what about', 'and in', 'how about', 'same for', 'what of', 'for ']
    if not any(ql.startswith(t) for t in followup_triggers) and len(ql.split()) > 4:
        return question
    for turn in reversed(history or []):
        if turn.get('role') == 'user':
            prev = turn.get('text', '')
            trailing = re.sub(r'^(what about|and in|how about|same for|what of|for)\s+', '', ql)
            if trailing and trailing != ql:
                return f"{prev.rstrip('?')} — and {trailing}?"
            break
    return question


def answer(question: str, ctx: Dict, history: Optional[List[Dict]] = None) -> Dict:
    ctx = ctx or {}
    q = _resolve_with_history(question or '', history or [])

    taught = _match_taught(q)
    if taught:
        return {'answer': taught, 'engine': 'learned'}

    llm = _llm_answer(q, ctx)
    if llm:
        return {'answer': llm, 'engine': 'claude'}

    data = _data_answer(q, ctx)
    if data:
        return {'answer': data, 'engine': 'data'}

    return {'answer': _rule_answer(q, ctx), 'engine': 'rules'}
