import React, { useState } from 'react';
import { formatINR } from './format';

export default function BudgetPlanner({ totalPayroll, remediationCost, filtered = false }) {
  const [pct, setPct] = useState(() => {
    if (!totalPayroll || !remediationCost) return 5;
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
    ? '✅ Within one compensation cycle'
    : years < 1.5
      ? `✅ ~${(years * 12).toFixed(0)} months`
      : `${wholeYears} review cycles`;

  return (
    <div className="panel budget-planner">
      <h2>💰 Pay Equity Remediation Planner
        {filtered && <span className="filter-note">filtered view</span>}
      </h2>

      <div className="budget-summary-row">
        <div className="budget-ctx"><span>Total fixed pay</span><strong>{formatINR(totalPayroll)}</strong></div>
        <div className="budget-ctx"><span>Equity adjustment cost</span><strong>{formatINR(remediationCost)}</strong></div>
        <div className="budget-ctx"><span>Gap as % of fixed pay</span><strong>{gapPct}%</strong></div>
      </div>

      <div className="budget-slider-row">
        <label>Annual equity budget (% of total fixed pay):</label>
        <div className="budget-slider-controls">
          <input type="number" min={1} max={50} step={1} value={pct}
            onChange={e => setPct(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
            className="budget-pct-input" />
          <span className="budget-pct-badge">{pct}%</span>
          <span className="budget-amount-label">= {formatINR(annualBudget)} p.a.</span>
        </div>
      </div>

      <div className={`budget-result ${resultClass}`}>
        <span>Estimated time to complete equity adjustment:</span>
        <strong>{yearLabel}</strong>
      </div>

      <div className="budget-tips">
        {years <= 1 && (
          <div className="budget-tip tip-good">
            ✅ At <strong>{pct}%</strong> of total fixed pay ({formatINR(annualBudget)} p.a.), the full equity
            adjustment can be completed within <strong>one compensation review cycle</strong> — a credible case for leadership sign-off.
          </div>
        )}
        {years > 1 && oneYearPct <= 15 && (
          <div className="budget-tip tip-suggest">
            💡 Leadership option: an equity budget of <strong>{oneYearPct}% of fixed pay</strong> ({formatINR(Math.round(totalPayroll * oneYearPct / 100))} p.a.)
            closes the full gap within <strong>one compensation cycle</strong>.
          </div>
        )}
        {years > 2 && (
          <div className="budget-tip tip-warn">
            ⚠️ At {pct}%, the equity adjustment spans {wholeYears} compensation cycles. Employees below range carry
            attrition and engagement risk in the interim — consider front-loading the highest-shortfall cases regardless of total budget.
          </div>
        )}
        {years > 1 && years <= 2 && (
          <div className="budget-tip tip-suggest">
            💡 At {pct}%, the equity adjustment completes over {Math.ceil(years * 12)} months — spanning two review cycles.
            Recommended split: address highest-shortfall employees in Cycle 1, remainder in Cycle 2.
          </div>
        )}
      </div>
    </div>
  );
}
