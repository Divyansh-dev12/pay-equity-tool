"""
Insight generation for the Pay Equity Studio.
Produces ranked observations using standard C&B nomenclature.
Pure functions, no external calls — deterministic and grounded in the data.
"""

from typing import Dict, List


def _lakh(n) -> str:
    try:
        v = float(n)
        if abs(v) >= 1_00_00_000:
            return f'₹{v/1_00_00_000:.2f} Cr'
        if abs(v) >= 1_00_000:
            return f'₹{v/1_00_000:.1f} L'
        return '₹' + format(int(round(v)), ',d')
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

    # Headline adjusted gap
    if cg <= -5:
        out.append({
            'title': 'Material adjusted pay gap — immediate action required',
            'text': (f'Women are paid {abs(cg):.1f}% less than men on a like-for-like basis after '
                     f'controlling for grade, tenure, performance, function and location. '
                     f'This exceeds the threshold typically flagged in a pay equity audit.'),
            'tone': 'critical'
        })
    elif cg <= -2:
        out.append({
            'title': 'Adjusted pay gap — targeted equity correction warranted',
            'text': (f'A {abs(cg):.1f}% adjusted gap favours men. The disparity is not organisation-wide '
                     f'but concentrated in specific functions where corrective action is recommended.'),
            'tone': 'warning'
        })
    elif cg >= 2:
        out.append({
            'title': 'Adjusted gap favours women — review for over-correction',
            'text': (f'On a like-for-like basis, women are paid {cg:.1f}% more than men. '
                     f'Confirm this is intentional and not a residual effect of prior remediation cycles.'),
            'tone': 'warning'
        })
    else:
        out.append({
            'title': 'Adjusted pay gap within acceptable range',
            'text': (f'The like-for-like adjusted gap stands at {cg:.1f}% — fixed pay is broadly '
                     f'equitable across comparable grades, functions and profiles.'),
            'tone': 'good'
        })

    # Adjusted vs unadjusted gap story
    if abs(ug) - abs(cg) >= 3:
        out.append({
            'title': 'Headline gap is driven by grade distribution, not pay rates',
            'text': (f'The unadjusted gap ({ug:.1f}%) is significantly wider than the adjusted gap ({cg:.1f}%). '
                     f'The difference reflects how men and women are distributed across grades and functions '
                     f'— a pipeline issue — rather than unequal pay for equivalent roles.'),
            'tone': 'info'
        })

    # Worst / best function
    if worst and worst.get('adjusted_gap_pct', 0) <= -3:
        out.append({
            'title': f'Priority function for equity review: {worst["name"]}',
            'text': (f'{worst["name"]} carries the largest adjusted pay gap at {worst["adjusted_gap_pct"]:.1f}% '
                     f'({worst["female_count"]} women, {worst["male_count"]} men). '
                     f'Recommend prioritising this function in the upcoming compensation review cycle.'),
            'tone': 'critical' if worst['adjusted_gap_pct'] <= -5 else 'warning'
        })
    if best:
        out.append({
            'title': f'Benchmark function: {best["name"]}',
            'text': (f'{best["name"]} demonstrates the most equitable pay positioning '
                     f'({best["adjusted_gap_pct"]:+.1f}% adjusted gap). '
                     f'Use its pay-setting practices as the internal benchmark for other functions.'),
            'tone': 'good'
        })

    # Equity adjustment scope
    n = anomalies.get('underpaid_count', 0)
    cost = anomalies.get('total_remediation_cost', 0)
    if n:
        out.append({
            'title': 'Equity adjustment scope',
            'text': (f'{n} employees are paid below their predicted pay range for their grade and profile. '
                     f'Bringing these individuals to range requires approximately {_lakh(cost)} '
                     f'in additional annual fixed pay.'),
            'tone': 'info'
        })

    # Model reliability
    out.append({
        'title': 'Model reliability',
        'text': (f'The regression model accounts for {r2*100:.0f}% of fixed pay variation (R² = {r2:.2f}). ' +
                 ('High model confidence — the adjusted pay gap is statistically reliable.'
                  if r2 >= 0.7
                  else 'Moderate model confidence — treat the adjusted gap as directional and supplement with a cohort-level review.')),
        'tone': 'info'
    })

    # Gender representation
    fc, mc = gs.get('female_count', 0), gs.get('male_count', 0)
    if fc + mc:
        share = fc / (fc + mc) * 100
        out.append({
            'title': 'Gender representation',
            'text': (f'Women represent {share:.0f}% of the reviewed headcount ({fc} of {fc+mc}). '
                     f'Track representation alongside pay equity — grade-level pipeline and pay rates '
                     f'are both components of total reward fairness.'),
            'tone': 'info'
        })
    return out


def median_insights(result: Dict) -> List[Dict]:
    out = []
    s = result.get('summary', {})
    gap = s.get('gender_gap_vs_median_pct', 0.0)
    fbelow = s.get('female_below_median_pct', 0.0)
    mbelow = s.get('male_below_median_pct', 0.0)
    src = ('your uploaded market benchmark'
           if result.get('median_source') == 'uploaded'
           else 'cohort midpoints computed from internal data')
    by_fn = result.get('by_function', [])

    # Headline positioning gap
    if gap <= -3:
        out.append({
            'title': "Women's pay positioning below cohort midpoint",
            'text': (f'On average, women sit {abs(gap):.1f}% further below their cohort midpoint than men '
                     f'(benchmarked against {src}).'),
            'tone': 'critical' if gap <= -5 else 'warning'
        })
    elif gap >= 3:
        out.append({
            'title': 'Women positioned above cohort midpoint — confirm intent',
            'text': (f'Women average {gap:.1f}% above cohort midpoint relative to men — a favourable outcome. '
                     f'Confirm this is intentional and not an artefact of grade or tenure mix.'),
            'tone': 'warning'
        })
    else:
        out.append({
            'title': 'Pay positioning broadly balanced at cohort midpoint',
            'text': (f'Women and men sit within {abs(gap):.1f}% of each other relative to cohort midpoint — '
                     f'equitable pay positioning across grades and functions.'),
            'tone': 'good'
        })

    # Below-midpoint concentration
    if fbelow - mbelow >= 8:
        out.append({
            'title': 'Disproportionate below-midpoint concentration for women',
            'text': (f'{fbelow:.0f}% of women are below their cohort midpoint vs {mbelow:.0f}% of men — '
                     f'a {fbelow-mbelow:.0f} percentage-point differential that warrants correction '
                     f'in the upcoming salary review.'),
            'tone': 'warning'
        })

    # Worst / best function
    if by_fn:
        worst = by_fn[0]
        if worst.get('gap_vs_median_pct', 0) <= -3:
            out.append({
                'title': f'Highest-risk function: {worst["name"]}',
                'text': (f'{worst["name"]} shows the widest pay positioning gap vs cohort midpoint '
                         f'at {worst["gap_vs_median_pct"]:.1f}%. Prioritise this function for corrective action.'),
                'tone': 'warning'
            })
        best = min(by_fn, key=lambda r: abs(r.get('gap_vs_median_pct', 0)))
        out.append({
            'title': f'Best-practice function: {best["name"]}',
            'text': (f'{best["name"]} shows the most balanced pay positioning '
                     f'({best["gap_vs_median_pct"]:+.1f}% vs midpoint). '
                     f'Use its offer and review guidelines as the internal standard.'),
            'tone': 'good'
        })

    # Methodology note
    out.append({
        'title': 'About this methodology',
        'text': ('The pay positioning model requires no statistical assumptions — it measures directly '
                 'where each employee sits vs the fair pay line for their cohort. '
                 'Results are audit-ready and straightforward to present to leadership or an external reviewer.'),
        'tone': 'info'
    })
    return out


def median_recommendations(result: Dict) -> Dict:
    """Generate structured recommended-actions block for the median model."""
    s = result.get('summary', {})
    gap = s.get('gender_gap_vs_median_pct', 0.0)
    fbelow = s.get('female_below_median_pct', 0.0)
    mbelow = s.get('male_below_median_pct', 0.0)
    by_fn = result.get('by_function', [])
    worst = by_fn[0] if by_fn else None

    if gap <= -5 or fbelow - mbelow >= 15:
        severity, pattern = 'High', 'Systemic below-midpoint pay positioning for women'
        actions = [
            f'Immediate correction: bring all women below cohort midpoint in the highest-gap function '
            f'({worst["name"] if worst else "identified function"}) to at least the cohort midpoint within 60 days.',
            'Establish a pay floor policy: no employee to remain below 90% of cohort midpoint after the next salary review cycle.',
            f'Quantify total equity adjustment budget — {fbelow:.0f}% of women are below midpoint vs {mbelow:.0f}% of men.',
            'Conduct root-cause analysis on offer-letter practices and mid-cycle promotion increases in flagged functions.',
            'Implement structured pay bands per grade to prevent future drift below midpoint.',
        ]
    elif gap <= -2 or fbelow - mbelow >= 8:
        severity, pattern = 'Medium', 'Moderate pay positioning gap — corrections required in next review cycle'
        actions = [
            'Prioritise women with the largest shortfall vs cohort midpoint for salary corrections in the upcoming compensation review.',
            f'Focus on {worst["name"] if worst else "the highest-gap function"} — widest pay positioning differential between genders.',
            "Set a monitoring threshold: flag any cohort where women's average pay position drops below −5% and trigger a mid-cycle review.",
            'Review offer guidelines to ensure new hires are placed at or above cohort midpoint for their grade.',
            'Share pay band midpoints with HRBPs and hiring managers to reduce below-midpoint placements at offer stage.',
        ]
    else:
        severity, pattern = 'Low', 'Pay positioning broadly equitable — maintain and monitor'
        actions = [
            'Run the pay positioning model quarterly to detect any drift early.',
            'Consider publishing pay range midpoints internally to reinforce pay transparency.',
            f'Keep {worst["name"] if worst else "at-risk functions"} under active monitoring — small gaps can compound across review cycles.',
            'Track promotion rates and grade distribution by gender alongside pay positioning — pipeline equity drives pay equity.',
            'Set an ongoing target: maintain gender pay gap vs midpoint within ±2% across all cohorts.',
        ]

    return {
        'pattern': pattern,
        'severity': severity,
        'message': (f'Gender pay gap vs cohort midpoint: {gap:+.1f}%. '
                    f'{fbelow:.0f}% of women are below cohort midpoint vs {mbelow:.0f}% of men.'),
        'actions': actions,
    }
