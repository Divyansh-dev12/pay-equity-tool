import React, { useState } from 'react';
import { formatINR } from './format';

/**
 * Interactive budget planner.
 * totalPayroll: sum of all base salaries in current view
 * remediationCost: total cost to fix underpaid / below-median employees
 */
export default function BudgetPlanner({ totalPayroll, remediationCost, filtered = false }) {
  const [pct, setPct] = useState(() => {
    if (!totalPayroll || !remediationCost) return 5;
    // Default to pace that gives ~2 years
    return Math.min(Math.max(Math.ceil((remediationCost / totalPayroll) * 100 * 2), 1), 20);
  });

  if (!totalPayroll || !remediationCost) return null;

  const annualBudget = Math.round(totalPayroll * pct / 100);
  const years = annualBudget > 0 ? remediationCost / annualBudget : Infinity;
  const wholeYears = Math.ceil(years);
  const gapPct = ((remediationCost / totalPayroll) * 100).toFixed(1);
  const oneYearPct = Math.ceil((remediationCost / totalPayroll) * 100);

  const resultClass = years <= 1 ? 'result-good' : years <= 2 ? 'result-warn' : 'result-slow';
  const yearLabel = years <= 1
    ? '✅ This cycle (under 1 year)'
    : years < 1.5
      ? `✅ ~${(years * 12).toFixed(0)} months`
      : `${wholeYears} years`;

  return (
    <div className="panel budget-planner">
      <h2>💰 Budget planner — how fast can we close this gap?
        {filtered && <span className="filter-note">filtered view</span>}
      </h2>

      <div className="budget-summary-row">
        <div className="budget-ctx"><span>Total payroll</span><strong>{formatINR(totalPayroll)}</strong></div>
        <div className="budget-ctx"><span>Cost to fix gap</span><strong>{formatINR(remediationCost)}</strong></div>
        <div className="budget-ctx"><span>Gap as % of payroll</span><strong>{gapPct}%</strong></div>
      </div>

      <div className="budget-slider-row">
        <label>Annual remediation budget (% of payroll):</label>
        <div className="budget-slider-controls">
          <input type="number" min={1} max={50} step={1} value={pct}
            onChange={e => setPct(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
            className="budget-pct-input" />
          <span className="budget-pct-badge">{pct}%</span>
          <span className="budget-amount-label">= {formatINR(annualBudget)} / yr</span>
        </div>
      </div>

      <div className={`budget-result ${resultClass}`}>
        <span>Time to close the full gap at this budget:</span>
        <strong>{yearLabel}</strong>
      </div>

      <div className="budget-tips">
        {years <= 1 && (
          <div className="budget-tip tip-good">
            ✅ At <strong>{pct}%</strong> of payroll ({formatINR(annualBudget)}/yr), the full remediation cost is
            covered in <strong>one compensation cycle</strong>. This is a credible ask for leadership approval.
          </div>
        )}
        {years > 1 && oneYearPct <= 15 && (
          <div className="budget-tip tip-suggest">
            💡 Leadership option: increase to <strong>{oneYearPct}% of payroll</strong> ({formatINR(Math.round(totalPayroll * oneYearPct / 100))}/yr)
            to close the entire gap in <strong>1 year</strong>.
          </div>
        )}
        {years > 2 && (
          <div className="budget-tip tip-warn">
            ⚠️ At {pct}%, remediation takes {wholeYears} years. Underpaid employees face attrition risk in the
            interim. Consider front-loading the highest-shortfall cases even at a lower total budget.
          </div>
        )}
        {years > 1 && years <= 2 && (
          <div className="budget-tip tip-suggest">
            💡 At {pct}%, you close the gap over {Math.ceil(years * 12)} months — manageable across 2 review cycles.
            Split: fix highest-risk (largest shortfall) employees in Year 1, remainder in Year 2.
          </div>
        )}
      </div>
    </div>
  );
}
