"""
AI-style insight generation. Turns the computed numbers into a ranked list of
plain-language observations a comp & ben professional would want to see first.

Each insight is {title, text, tone} where tone in {critical, warning, good, info}.
Pure functions, no external calls — deterministic and grounded in the data.
"""

from typing import Dict, List


def _fmt_inr(n) -> str:
    try:
        return '₹' + format(int(round(n)), ',d').replace(',', ',')  # grouped
    except Exception:
        return '₹0'


def _lakh(n) -> str:
    try:
        v = float(n)
        if abs(v) >= 1_00_00_000:
            return f'₹{v/1_00_00_000:.2f} Cr'
        if abs(v) >= 1_00_000:
            return f'₹{v/1_00_000:.1f} L'
        return _fmt_inr(v)
    except Exception:
        return '₹0'


def regression_insights(model_stats: Dict, recommendations: Dict,
                        breakdowns: Dict, anomalies: Dict) -> List[Dict]:
    out = []
    cg = recommendations.get('controlled_gap_pct', 0.0)
    ug = recommendations.get('uncontrolled_gap_pct', 0.0)
    r2 = model_stats.get('r_squared') or 0.0
    gs = breakdowns.get('gender_summary', {})
    worst = breakdowns.get('worst_function')
    best = breakdowns.get('best_function')

    # Headline gap
    if cg <= -5:
        out.append({'title': 'Systemic like-for-like gap',
                    'text': f'Women are paid {abs(cg):.1f}% less than men for comparable roles after controlling for level, tenure, performance, function and location. This is above the threshold that usually signals systemic bias.',
                    'tone': 'critical'})
    elif cg <= -2:
        out.append({'title': 'Real but contained gap',
                    'text': f'A {abs(cg):.1f}% like-for-like gap favours men. Not company-wide bias, but concentrated in specific pockets worth fixing.',
                    'tone': 'warning'})
    elif cg >= 2:
        out.append({'title': 'Gap favours women',
                    'text': f'On a like-for-like basis women are paid {cg:.1f}% more. Worth confirming this is intentional and not an over-correction.',
                    'tone': 'warning'})
    else:
        out.append({'title': 'Like-for-like pay is balanced',
                    'text': f'The controlled gap is only {cg:.1f}% — pay is broadly equitable for comparable work.',
                    'tone': 'good'})

    # Controlled vs uncontrolled story
    if abs(ug) - abs(cg) >= 3:
        out.append({'title': 'Representation drives the raw gap',
                    'text': f'The raw gap ({ug:.1f}%) is much larger than the like-for-like gap ({cg:.1f}%). Most of the headline difference comes from how men and women are distributed across levels and functions, not unequal pay for the same job.',
                    'tone': 'info'})

    # Worst / best function
    if worst and worst.get('adjusted_gap_pct', 0) <= -3:
        out.append({'title': f'Biggest gap: {worst["name"]}',
                    'text': f'{worst["name"]} has the largest like-for-like gap at {worst["adjusted_gap_pct"]:.1f}% ({worst["female_count"]} women, {worst["male_count"]} men). Start remediation here.',
                    'tone': 'critical' if worst['adjusted_gap_pct'] <= -5 else 'warning'})
    if best:
        out.append({'title': f'Model function: {best["name"]}',
                    'text': f'{best["name"]} is the most equitable function ({best["adjusted_gap_pct"]:+.1f}%). Use its pay-setting practices as the template for others.',
                    'tone': 'good'})

    # Remediation cost
    n = anomalies.get('underpaid_count', 0)
    cost = anomalies.get('total_remediation_cost', 0)
    if n:
        out.append({'title': 'Remediation scope',
                    'text': f'{n} employees are paid below what the model predicts for their profile. Closing those shortfalls costs about {_lakh(cost)} in annual fixed pay.',
                    'tone': 'info'})

    # Model trust
    out.append({'title': 'How much to trust this',
                'text': f'The model explains {r2*100:.0f}% of pay variation (R² = {r2:.2f}). ' +
                        ('That is a strong fit, so the controlled gap is reliable.' if r2 >= 0.7
                         else 'That is a moderate fit — treat the controlled gap as directional.'),
                'tone': 'info'})

    # Representation quick check
    fc, mc = gs.get('female_count', 0), gs.get('male_count', 0)
    if fc + mc:
        share = fc / (fc + mc) * 100
        out.append({'title': 'Workforce mix',
                    'text': f'Women are {share:.0f}% of the analysed workforce ({fc} of {fc+mc}). Track this alongside pay — representation is the other half of equity.',
                    'tone': 'info'})
    return out


def median_recommendations(result: Dict) -> Dict:
    """Generate a structured recommended-actions block for the median model."""
    s = result.get('summary', {})
    gap = s.get('gender_gap_vs_median_pct', 0.0)
    fbelow = s.get('female_below_median_pct', 0.0)
    mbelow = s.get('male_below_median_pct', 0.0)
    by_fn = result.get('by_function', [])
    worst = by_fn[0] if by_fn else None

    if gap <= -5 or fbelow - mbelow >= 15:
        severity, pattern = 'High', 'Systemic below-median positioning for women'
        actions = [
            f'Immediate review: raise all women below cohort median in the worst-gap function ({worst["name"] if worst else "identified function"}) within 60 days.',
            'Set hard-floor policy: no employee to remain below 90% of cohort median after the next review cycle.',
            f'Budget for corrections: {fbelow:.0f}% of women are below median vs {mbelow:.0f}% of men — quantify the total correction cost.',
            'Run root-cause analysis on offer-setting and promotion practices in flagged functions.',
            'Introduce structured pay bands per level to constrain future drift below median.',
        ]
    elif gap <= -2 or fbelow - mbelow >= 8:
        severity, pattern = 'Medium', 'Moderate positioning gap — targeted remediation needed'
        actions = [
            f'Prioritise women paid furthest below cohort median for salary corrections in the next compensation cycle.',
            f'Focus on {worst["name"] if worst else "the highest-gap function"} — widest gap between genders vs median.',
            'Set a monitoring threshold: flag any cohort where women\'s median position drops below −5% and trigger review.',
            'Review offer-setting guidelines: ensure new hires land at or above cohort median for their level.',
            'Share band midpoints with managers to reduce discretionary underpaying.',
        ]
    else:
        severity, pattern = 'Low', 'Broadly balanced — maintain and monitor'
        actions = [
            'Continue quarterly median model runs to catch any drift early.',
            'Publish band ranges internally to reinforce pay transparency.',
            f'Monitor {worst["name"] if worst else "at-risk functions"} closely — even a small gap can widen without structured pay bands.',
            'Track promotion rates by gender alongside pay position — pipeline and pay equity are linked.',
            'Set an aspirational target: {"<"}2% gender gap vs median by next audit.',
        ]

    return {
        'pattern': pattern,
        'severity': severity,
        'message': (f'Gender gap vs median: {gap:+.1f}%. '
                    f'{fbelow:.0f}% of women are below their cohort median vs {mbelow:.0f}% of men.'),
        'actions': actions,
    }


def median_insights(result: Dict) -> List[Dict]:
    out = []
    s = result.get('summary', {})
    gap = s.get('gender_gap_vs_median_pct', 0.0)
    fbelow = s.get('female_below_median_pct', 0.0)
    mbelow = s.get('male_below_median_pct', 0.0)
    src = 'your uploaded benchmark' if result.get('median_source') == 'uploaded' else 'medians computed from the data'
    by_fn = result.get('by_function', [])

    if gap <= -3:
        out.append({'title': 'Women sit below the median line',
                    'text': f'On average women are {abs(gap):.1f}% further below their cohort median than men (measured against {src}).',
                    'tone': 'critical' if gap <= -5 else 'warning'})
    elif gap >= 3:
        out.append({'title': 'Women sit above the median line',
                    'text': f'Women are on average {gap:.1f}% above cohort median relative to men — a reverse gap worth understanding.',
                    'tone': 'warning'})
    else:
        out.append({'title': 'Both genders near the median',
                    'text': f'Women and men sit within {abs(gap):.1f}% of each other against the median line — broadly balanced.',
                    'tone': 'good'})

    if fbelow - mbelow >= 8:
        out.append({'title': 'More women below median',
                    'text': f'{fbelow:.0f}% of women are paid below their cohort median vs {mbelow:.0f}% of men — a {fbelow-mbelow:.0f} point difference.',
                    'tone': 'warning'})

    if by_fn:
        worst = by_fn[0]
        if worst.get('gap_vs_median_pct', 0) <= -3:
            out.append({'title': f'Widest gap: {worst["name"]}',
                        'text': f'{worst["name"]} shows the widest gap versus median at {worst["gap_vs_median_pct"]:.1f}%.',
                        'tone': 'warning'})
        best = min(by_fn, key=lambda r: abs(r.get('gap_vs_median_pct', 0)))
        out.append({'title': f'Most balanced: {best["name"]}',
                    'text': f'{best["name"]} is closest to parity against the median ({best["gap_vs_median_pct"]:+.1f}%).',
                    'tone': 'good'})

    out.append({'title': 'Why this model',
                'text': 'The median model needs no statistical assumptions — it simply asks "is this person above or below the fair line for their cohort?" — so it is easy to explain and defend.',
                'tone': 'info'})
    return out
