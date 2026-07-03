import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, ReferenceLine, LabelList,
  PieChart, Pie,
  LineChart, Line, AreaChart, Area,
} from 'recharts';
import { API_URL, formatINR, pct, gapColor } from './format';
import { applyFilters, filteredRegressionStats, median, isF, isM, payByLevel, headcountByLevel } from './analytics';
import ExploreDashboard from './ExploreDashboard';
import Insights from './Insights';
import ChatBot from './ChatBot';
import BudgetPlanner from './BudgetPlanner';
import ExportReport from './ExportReport';

const PAGE_SIZE = 500;

export default function RegressionDashboard({ onHome, savedData, onDataChange }) {
  const [data, setData] = useState(savedData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [source, setSource] = useState(savedData ? 'Restored from last session' : null);
  const [filter, setFilter] = useState({});

  function handleData(d, src) { setData(d); setSource(src); setFilter({}); onDataChange(d); }

  async function loadSample() {
    setLoading(true); setError(null);
    try {
      const s = await (await fetch(`${API_URL}/api/sample-data`)).json();
      const res = await fetch(`${API_URL}/api/analyze-json`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employees: s.data }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Analysis failed');
      handleData(await res.json(), `Sample dataset · ${s.rows} employees`);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function uploadCsv(file) {
    if (!file) return;
    setLoading(true); setError(null);
    try {
      const fd = new FormData(); fd.append('file', file);
      const res = await fetch(`${API_URL}/api/analyze`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error((await res.json()).detail || 'Analysis failed');
      handleData(await res.json(), `Uploaded · ${file.name}`);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  function clearData() { setData(null); setSource(null); setFilter({}); onDataChange(null); }

  return (
    <div className="app">
      <div className="topbar">
        <button className="btn btn-ghost" onClick={onHome}>← Home</button>
        <div className="topbar-title">
          <h1>📈 Regression Model</h1>
          {source && <span className="topbar-sub">{source}</span>}
        </div>
        {data && <button className="btn btn-ghost" onClick={clearData}>↻ Change data</button>}
      </div>

      {!data && <DataSource loading={loading} error={error} onSample={loadSample} onUpload={uploadCsv} />}
      {data && <Results data={data} filter={filter} setFilter={setFilter} />}
    </div>
  );
}

function DataSource({ loading, error, onSample, onUpload }) {
  const [file, setFile] = useState(null);
  return (
    <div className="datasource">
      <div className="ds-card">
        <h3>Try it instantly</h3>
        <p>Load a synthetic Indian compensation dataset with several built-in scenarios.</p>
        <button className="btn btn-primary" onClick={onSample} disabled={loading}>
          {loading ? 'Analysing…' : '▶ Load sample data'}
        </button>
      </div>
      <div className="ds-or">or</div>
      <div className="ds-card">
        <h3>Upload your CSV</h3>
        <p className="mono-hint">employee_id, job_title, job_level, base_salary, gender, job_function, location, tenure_years, performance_rating</p>
        <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} disabled={loading} />
        <button className="btn btn-primary" style={{ marginTop: 10 }}
          onClick={() => onUpload(file)} disabled={loading || !file}>
          {loading ? 'Analysing…' : 'Analyse uploaded data'}
        </button>
        <div className="download-row">
          <a className="dl-link" href={`${API_URL}/api/template/employee`}>⬇ Download blank template</a>
          <a className="dl-link" href={`${API_URL}/api/download/sample-employees`}>⬇ Download sample data</a>
        </div>
      </div>
      {error && <div className="error-banner">❌ {error}</div>}
    </div>
  );
}

function Results({ data, filter, setFilter }) {
  const stats = data.model_stats;
  const rec = data.recommendations;
  const bd = data.breakdowns;
  const gs = bd.gender_summary;
  const controlled = rec.controlled_gap_pct;
  const uncontrolled = rec.uncontrolled_gap_pct;
  const r2 = stats.r_squared;

  const hasFilter = !!(filter.function || filter.level || filter.gender);

  const filteredPredictions = useMemo(
    () => applyFilters(data.predictions, filter),
    [data, filter]
  );

  const fs = useMemo(() => filteredRegressionStats(filteredPredictions), [filteredPredictions]);

  // Overpaid: actual > predicted * 1.15 (>15% above model)
  const overpaidRows = useMemo(
    () => filteredPredictions.filter(p => p.predicted_salary > 0 && p.base_salary > p.predicted_salary * 1.15),
    [filteredPredictions]
  );

  // Underpaid rows
  const underpaidRows = useMemo(
    () => filteredPredictions.filter(p => p.is_underpaid_outlier),
    [filteredPredictions]
  );

  const totalPayroll = useMemo(
    () => filteredPredictions.reduce((s, p) => s + (p.base_salary || 0), 0),
    [filteredPredictions]
  );

  const overpaidExcess = useMemo(
    () => overpaidRows.reduce((s, p) => s + (p.base_salary - p.predicted_salary * 1.15), 0),
    [overpaidRows]
  );

  // Roster: 3-way toggle
  const [rosterFilter, setRosterFilter] = useState('all'); // 'all' | 'underpaid' | 'overpaid'
  const [rosterPage, setRosterPage] = useState(0);

  const rosterRows = useMemo(() => {
    let base;
    if (rosterFilter === 'underpaid') base = underpaidRows;
    else if (rosterFilter === 'overpaid') base = overpaidRows;
    else base = filteredPredictions;
    return [...base].sort((a, b) => {
      if (rosterFilter === 'overpaid') return (b.base_salary - b.predicted_salary) - (a.base_salary - a.predicted_salary);
      return (b.gap_dollars || 0) - (a.gap_dollars || 0);
    });
  }, [filteredPredictions, underpaidRows, overpaidRows, rosterFilter]);

  const totalRosterPages = Math.ceil(rosterRows.length / PAGE_SIZE);
  const pageRows = rosterRows.slice(rosterPage * PAGE_SIZE, (rosterPage + 1) * PAGE_SIZE);

  useMemo(() => { setRosterPage(0); }, [filter, rosterFilter]);

  const displayFemaleMedian = hasFilter ? fs.femaleMedian : gs.female_median;
  const displayMaleMedian = hasFilter ? fs.maleMedian : gs.male_median;
  const displayRawGap = hasFilter ? fs.rawGapPct : gs.uncontrolled_gap_pct;
  const displayRemCount = hasFilter ? fs.underpaidCount : data.anomalies.underpaid_count;
  const displayRemCost = hasFilter ? fs.remediationCost : data.anomalies.total_remediation_cost;

  const reportData = useMemo(() => {
    const filterLabel = [
      filter.function && `Function: ${filter.function}`,
      filter.level && `Level: ${filter.level}`,
      filter.gender && `Gender: ${filter.gender}`,
    ].filter(Boolean).join(' · ') || 'All employees';
    return {
      model: 'regression',
      filterLabel,
      hasFilter,
      kpis: [
        { label: 'Controlled gap (like-for-like)', value: pct(controlled), isNegative: controlled < -1 },
        { label: 'Raw gap (uncontrolled)', value: pct(displayRawGap), isNegative: displayRawGap < -1 },
        { label: 'Employees analysed', value: String(hasFilter ? fs.total : stats.observations) },
        { label: 'Underpaid employees', value: String(displayRemCount), isNegative: displayRemCount > 0 },
        { label: 'Cost to fix gap', value: fmtL(displayRemCost), isNegative: displayRemCost > 0 },
        { label: 'Total payroll', value: fmtL(totalPayroll) },
      ],
      insights: data.insights,
      recommendations: rec.recommendations[0],
    };
  }, [filter, hasFilter, controlled, displayRawGap, fs, stats, displayRemCount, displayRemCost, totalPayroll, data.insights, rec]);

  const buildContext = () => ({
    method: 'regression',
    controlled_gap_pct: controlled,
    uncontrolled_gap_pct: uncontrolled,
    r_squared: r2,
    worst_function: bd.worst_function,
    best_function: bd.best_function,
    by_function: bd.by_function,
    remediation_count: displayRemCount,
    remediation_cost: displayRemCost,
    overpaid_count: overpaidRows.length,
    overpaid_excess: overpaidExcess,
    total_payroll: totalPayroll,
    female_count: hasFilter ? fs.femaleCount : gs.female_count,
    male_count: hasFilter ? fs.maleCount : gs.male_count,
    female_median: displayFemaleMedian,
    male_median: displayMaleMedian,
    recommendation: rec.recommendations[0],
    employees: filteredPredictions.map(p => ({
      id: p.employee_id, title: p.job_title, function: p.job_function,
      level: p.job_level, gender: p.gender, salary: p.base_salary,
      gap: p.gap_dollars, underpaid: p.is_underpaid_outlier,
      overpaid: overpaidRows.some(o => o.employee_id === p.employee_id),
    })),
  });

  return (
    <div className="results">
      {/* 1. Filter banner */}
      {hasFilter && (
        <div className="filter-active-banner">
          🔎 Filtered view · {filteredPredictions.length} of {data.predictions.length} employees — all stats reflect this filter.
          <button onClick={() => setFilter({})}>Clear filter ×</button>
        </div>
      )}

      {/* 2. Stat cards */}
      <div className="cards">
        <StatCard value={hasFilter ? fs.total : stats.observations} label="Employees analysed"
          sub={hasFilter ? `of ${stats.observations} total` : null} />
        <StatCard value={pct(controlled)} label="Controlled gap (like-for-like)" color={gapColor(controlled)}
          hint="Model-wide · gap after making role, level, tenure, performance & location equal" />
        <StatCard value={pct(displayRawGap)} label="Raw gap (uncontrolled)" color={gapColor(displayRawGap)}
          hint={hasFilter ? 'Filtered view' : 'Plain difference in typical pay, before adjustment'} />
        <StatCard value={r2 == null ? '—' : r2.toFixed(2)} label="Model fit (R²)"
          hint="Model-wide · share of pay differences the model explains" />
      </div>

      {/* 3. AI Insights */}
      <Insights insights={data.insights} />

      {/* Data quality checks */}
      {data.data_quality && <DataQuality dq={data.data_quality} />}

      {/* 4. How to read this */}
      <div className="panel">
        <h2>How to read this</h2>
        <div className="explain-grid">
          <Explainer title="What is R²?" icon="🎯">
            R² is <strong>{r2 == null ? '—' : (r2 * 100).toFixed(0)}%</strong> — the model explains that share
            of why fixed pay differs. Closer to 100% = more trustworthy the controlled gap.
          </Explainer>
          <Explainer title="How we predict pay" icon="🧮">
            We learn how much <strong>level, tenure, performance, function and location</strong> are worth,
            predict what each person <em>should</em> earn, and the leftover gender difference is the <strong>controlled gap</strong>.
          </Explainer>
          <Explainer title="Uncontrolled gap" icon="📏">
            The <strong>raw</strong> difference in typical pay — reflects pay <em>and</em> representation.
          </Explainer>
          <Explainer title="Controlled gap" icon="⚖️">
            The gap for <strong>the same job, level and profile</strong> — the like-for-like number. Negative = women paid less.
          </Explainer>
        </div>
      </div>

      {/* 5. Male vs Female summary chips */}
      <div className="panel">
        <h2>Male vs Female fixed pay {hasFilter && <span className="filter-note">filtered</span>}</h2>
        <div className="mf-summary">
          <div className="mf-chip mf-male">
            <span>Men — median fixed pay</span>
            <strong>{formatINR(displayMaleMedian)}</strong>
            <small>{hasFilter ? fs.maleCount : gs.male_count} employees</small>
          </div>
          <div className="mf-chip mf-female">
            <span>Women — median fixed pay</span>
            <strong>{formatINR(displayFemaleMedian)}</strong>
            <small>{hasFilter ? fs.femaleCount : gs.female_count} employees</small>
          </div>
          <div className="mf-chip mf-gap" style={{ borderColor: gapColor(displayRawGap) }}>
            <span>Raw difference (women vs men)</span>
            <strong style={{ color: gapColor(displayRawGap) }}>{pct(displayRawGap)}</strong>
            <small>unadjusted median gap</small>
          </div>
        </div>
      </div>

      {/* 6. Best / Worst callouts */}
      <div className="callouts">
        <Callout kind="good" title="Following the right approach" fn={bd.best_function} />
        <Callout kind="bad" title="Biggest gap to fix" fn={bd.worst_function} />
      </div>

      {/* 7. Interactive Explorer (charts + filter) */}
      <div className="panel">
        <ExploreDashboard rows={data.predictions} filter={filter} setFilter={setFilter} />
      </div>

      {/* 7b. Analytics charts */}
      <ExportReport reportData={reportData} />
      <RegressionAnalytics predictions={filteredPredictions} gs={gs} fs={fs} hasFilter={hasFilter} />

      {/* 8. Recommended actions */}
      <div className="panel actions-panel">
        <h2>Recommended actions</h2>
        <div className={`rec-banner sev-${(rec.recommendations[0].severity || '').toLowerCase()}`}>
          <div className="rec-head">
            <span className="rec-pattern">{rec.recommendations[0].pattern}</span>
            <span className="rec-sev">Severity: {rec.recommendations[0].severity}</span>
          </div>
          <p>{rec.recommendations[0].message}</p>
        </div>
        <ol className="action-list">
          {rec.recommendations[0].actions.map((a, i) => <li key={i}>{a}</li>)}
        </ol>
      </div>

      {/* 9. Cost impact */}
      <div className="panel cost-impact-panel">
        <h2>💸 Cost impact to close the gap {hasFilter && <span className="filter-note">filtered</span>}</h2>
        <div className="cost-impact-grid">
          <div className="cost-item cost-underpaid">
            <span>⚠️ Underpaid employees</span>
            <strong>{displayRemCount}</strong>
            <em>Annual cost to fix: <b>{formatINR(displayRemCost)}</b></em>
          </div>
          <div className="cost-item cost-overpaid">
            <span>📈 Above-model employees (&gt;15% over predicted)</span>
            <strong>{overpaidRows.length}</strong>
            <em>Market over-positioning: <b>{formatINR(overpaidExcess)}</b></em>
          </div>
          <div className="cost-item cost-payroll">
            <span>Total payroll {hasFilter ? '(filtered)' : ''}</span>
            <strong>{formatINR(totalPayroll)}</strong>
            <em>Gap = <b>{totalPayroll > 0 ? ((displayRemCost / totalPayroll) * 100).toFixed(1) : '0'}%</b> of payroll</em>
          </div>
          {overpaidRows.length > 0 && displayRemCost > 0 && (
            <div className="cost-item cost-net">
              <span>💡 Natural rebalancing offset</span>
              <strong>{formatINR(Math.min(overpaidExcess, displayRemCost))}</strong>
              <em>If above-model employees turn over, replacements at predicted rates could offset this.</em>
            </div>
          )}
        </div>
      </div>

      {/* 10. Budget planner */}
      <BudgetPlanner totalPayroll={totalPayroll} remediationCost={displayRemCost} filtered={hasFilter} />

      {/* 11. Employee roster with 3-way toggle */}
      <div className="panel">
        <div className="roster-head">
          <h2>
            Employee roster
            {hasFilter && <span className="filter-note">filtered</span>}
            <span className="count-badge">{rosterRows.length}</span>
          </h2>
        </div>
        <QuickRosterFilter allRows={data.predictions} filter={filter} setFilter={setFilter} />
        <div className="roster-filter-tabs">
          <button className={rosterFilter === 'all' ? 'tab active' : 'tab'}
            onClick={() => setRosterFilter('all')}>
            All employees ({filteredPredictions.length})
          </button>
          <button className={rosterFilter === 'underpaid' ? 'tab active tab-warn' : 'tab'}
            onClick={() => setRosterFilter('underpaid')}>
            ⚠️ Underpaid ({underpaidRows.length})
          </button>
          <button className={rosterFilter === 'overpaid' ? 'tab active tab-above' : 'tab'}
            onClick={() => setRosterFilter('overpaid')}>
            📈 Above model ({overpaidRows.length})
          </button>
        </div>
        <p className="panel-hint">
          {rosterFilter === 'all' && 'All employees. ⚠️ rows = below model prediction, 📈 = significantly above (+15%). Sorted by shortfall size.'}
          {rosterFilter === 'underpaid' && 'Employees paid below what the model predicts for their profile. Sorted by largest shortfall first.'}
          {rosterFilter === 'overpaid' && 'Employees paid >15% above model prediction. These are at market over-positioning risk — if they leave, backfills would cost less. Sorted by excess pay (largest first).'}
          {totalRosterPages > 1 && ` · Page ${rosterPage + 1} of ${totalRosterPages} (${PAGE_SIZE}/page)`}
        </p>
        <RosterTable rows={pageRows} rosterFilter={rosterFilter} overpaidIds={new Set(overpaidRows.map(r => r.employee_id))} />
        {totalRosterPages > 1 && (
          <div className="pagination">
            <button onClick={() => setRosterPage(p => Math.max(0, p - 1))} disabled={rosterPage === 0}>← Prev</button>
            <span>Page {rosterPage + 1} / {totalRosterPages}</span>
            <button onClick={() => setRosterPage(p => Math.min(totalRosterPages - 1, p + 1))} disabled={rosterPage >= totalRosterPages - 1}>Next →</button>
          </div>
        )}
      </div>

      {/* 12. Model details / Coefficients */}
      <CoefficientTable coeffs={data.coefficients} r2={r2} />

      {/* 13. Chatbot */}
      <ChatBot buildContext={buildContext} model="regression" />
    </div>
  );
}

// ---------- Sub-components ----------

function StatCard({ value, label, color, hint, sub }) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={color ? { color } : undefined}>{value}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

function Explainer({ title, icon, children }) {
  return (<div className="explainer"><div className="explainer-title">{icon} {title}</div><p>{children}</p></div>);
}

function Callout({ kind, title, fn }) {
  if (!fn) return null;
  return (
    <div className={`callout callout-${kind}`}>
      <div className="callout-label">{kind === 'good' ? '✅' : '⚠️'} {title}</div>
      <div className="callout-fn">{fn.name}</div>
      <div className="callout-gap" style={{ color: gapColor(fn.adjusted_gap_pct) }}>{pct(fn.adjusted_gap_pct)} <span>like-for-like</span></div>
      <div className="callout-verdict">{fn.verdict}</div>
    </div>
  );
}

function DataQuality({ dq }) {
  const checks = [];
  if (dq.missing_salary_pct > 5) checks.push({ tone: 'warn', msg: `${dq.missing_salary_pct?.toFixed(1)}% of salary values are missing — results may be less reliable.` });
  if (dq.sample_size < 30) checks.push({ tone: 'warn', msg: `Only ${dq.sample_size} employees — results are directional, not statistically robust.` });
  if (dq.female_pct < 10) checks.push({ tone: 'warn', msg: `Women are only ${dq.female_pct?.toFixed(0)}% of the workforce — controlled gap has wide confidence intervals.` });
  if (dq.salary_range_ratio > 20) checks.push({ tone: 'info', msg: `Salary range is very wide (${dq.salary_range_ratio?.toFixed(0)}× between min/max) — make sure you have not mixed currencies or pay types.` });
  if (!checks.length) return null;
  return (
    <div className="panel dq-panel">
      <h2>⚠️ Data quality notes</h2>
      <ul className="dq-list">
        {checks.map((c, i) => <li key={i} className={`dq-item dq-${c.tone}`}>{c.msg}</li>)}
      </ul>
    </div>
  );
}

function RosterTable({ rows, rosterFilter, overpaidIds }) {
  if (!rows.length) return (
    <p className="empty">
      {rosterFilter === 'underpaid' ? 'No employees flagged below model prediction ✓' :
       rosterFilter === 'overpaid' ? 'No employees significantly above model prediction.' :
       'No employees in this view.'}
    </p>
  );
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Employee</th><th>Title</th><th>Function</th><th>Level</th><th>Gender</th>
            <th>Actual pay</th><th>Predicted</th><th>Shortfall / Excess</th><th>%</th>
            {rosterFilter === 'all' && <th>Status</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const gapPct = r.predicted_salary
              ? ((r.predicted_salary - r.base_salary) / r.base_salary * 100)
              : 0;
            const isOverpaid = overpaidIds.has(r.employee_id);
            const rowClass = r.is_underpaid_outlier ? 'below' : isOverpaid ? 'above-model' : '';
            return (
              <tr key={i} className={rowClass}>
                <td className="mono">{r.employee_id}</td>
                <td>{r.job_title}</td>
                <td>{r.job_function}</td>
                <td>{r.job_level}</td>
                <td>{r.gender}</td>
                <td>{formatINR(r.base_salary)}</td>
                <td>{formatINR(r.predicted_salary)}</td>
                <td className={r.gap_dollars < 0 ? 'neg' : r.gap_dollars > 0 ? 'pos' : ''}>
                  {r.is_underpaid_outlier ? `-${formatINR(Math.abs(r.gap_dollars))}` : formatINR(r.gap_dollars)}
                </td>
                <td className={gapPct > 0 ? 'neg' : gapPct < -10 ? 'pos-strong' : ''}>
                  {Math.abs(gapPct).toFixed(1)}% {gapPct > 0 ? '↓' : gapPct < -10 ? '↑' : ''}
                </td>
                {rosterFilter === 'all' && (
                  <td>
                    {r.is_underpaid_outlier ? '⚠️ Underpaid' : isOverpaid ? '📈 Above model' : '✓'}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------- Quick filter bar (above roster) ----------
function QuickRosterFilter({ allRows, filter, setFilter }) {
  const functions = useMemo(() => [...new Set(allRows.map(r => r.job_function))].filter(Boolean).sort(), [allRows]);
  const levels = useMemo(() => [...new Set(allRows.map(r => r.job_level))].filter(Boolean).sort(), [allRows]);
  const hasAny = !!(filter.function || filter.level || filter.gender);
  return (
    <div className="quick-filter-bar">
      <span className="qf-label">🔍 Filter roster:</span>
      <select className="qf-select" value={filter.function || ''}
        onChange={e => setFilter(f => ({ ...f, function: e.target.value || null }))}>
        <option value="">All functions</option>
        {functions.map(fn => <option key={fn} value={fn}>{fn}</option>)}
      </select>
      <select className="qf-select" value={filter.level || ''}
        onChange={e => setFilter(f => ({ ...f, level: e.target.value || null }))}>
        <option value="">All levels</option>
        {levels.map(l => <option key={l} value={l}>{l}</option>)}
      </select>
      <select className="qf-select" value={filter.gender || ''}
        onChange={e => setFilter(f => ({ ...f, gender: e.target.value || null }))}>
        <option value="">All genders</option>
        <option value="Female">Female</option>
        <option value="Male">Male</option>
      </select>
      {hasAny && <button className="qf-clear" onClick={() => setFilter({})}>Clear all ×</button>}
    </div>
  );
}

// ---------- Analytics charts panel ----------
const PINK = '#e64980', BLUE = '#4c6ef5', RED = '#e03131', GREEN = '#2f9e44';
const fmtL = v => {
  if (!v) return '₹0';
  if (Math.abs(v) >= 1e7) return `₹${(v / 1e7).toFixed(1)}Cr`;
  if (Math.abs(v) >= 1e5) return `₹${(v / 1e5).toFixed(0)}L`;
  return `₹${Math.round(v / 1000)}K`;
};

function RegressionAnalytics({ predictions, gs, fs, hasFilter }) {
  const genderPieData = useMemo(() => [
    { name: 'Women', value: hasFilter ? fs.femaleCount : gs.female_count },
    { name: 'Men', value: hasFilter ? fs.maleCount : gs.male_count },
  ], [predictions, gs, fs, hasFilter]);

  const payLevelData = useMemo(() => payByLevel(predictions), [predictions]);

  const remByFn = useMemo(() => {
    const acc = {};
    predictions.filter(p => p.is_underpaid_outlier).forEach(p => {
      const fn = p.job_function || 'Other';
      acc[fn] = (acc[fn] || 0) + Math.abs(p.gap_dollars || 0);
    });
    return Object.entries(acc)
      .map(([name, cost]) => ({ name, cost: Math.round(cost) }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 8);
  }, [predictions]);

  const headcountData = useMemo(() => headcountByLevel(predictions), [predictions]);

  const totalPayroll = useMemo(() => predictions.reduce((s, p) => s + (p.base_salary || 0), 0), [predictions]);
  const underpaidCost = useMemo(() => predictions.filter(p => p.is_underpaid_outlier).reduce((s, p) => s + Math.abs(p.gap_dollars || 0), 0), [predictions]);
  const underpaidCount = useMemo(() => predictions.filter(p => p.is_underpaid_outlier).length, [predictions]);
  const overpaidCount = useMemo(() => predictions.filter(p => p.predicted_salary > 0 && p.base_salary > p.predicted_salary * 1.15).length, [predictions]);

  return (
    <div className="panel analytics-panel">
      <h2>📊 Analytics overview {hasFilter && <span className="filter-note">filtered</span>}</h2>

      {/* Totals row */}
      <div className="analytics-totals">
        <div className="a-total"><span>Total employees</span><strong>{predictions.length}</strong></div>
        <div className="a-total"><span>Total payroll</span><strong>{fmtL(totalPayroll)}</strong></div>
        <div className="a-total warn"><span>Underpaid</span><strong>{underpaidCount}</strong></div>
        <div className="a-total warn"><span>Cost to fix</span><strong>{fmtL(underpaidCost)}</strong></div>
        <div className="a-total good"><span>Above model</span><strong>{overpaidCount}</strong></div>
        <div className="a-total"><span>Gap % of payroll</span><strong>{totalPayroll > 0 ? ((underpaidCost / totalPayroll) * 100).toFixed(1) : 0}%</strong></div>
      </div>

      <div className="analytics-grid">
        {/* 1. Gender split pie */}
        <div className="analytics-card">
          <h3>Gender split</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={genderPieData} cx="50%" cy="50%" outerRadius={75} dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}>
                <Cell fill={PINK} />
                <Cell fill={BLUE} />
              </Pie>
              <Tooltip formatter={(v, n) => [v + ' employees', n]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 2. Median pay by level — F vs M line */}
        <div className="analytics-card">
          <h3>Median pay by level</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={payLevelData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={fmtL} width={54} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => fmtL(v)} />
              <Legend />
              <Line type="monotone" dataKey="Women" stroke={PINK} strokeWidth={2.5} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="Men" stroke={BLUE} strokeWidth={2.5} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 3. Remediation cost by function */}
        <div className="analytics-card">
          <h3>Remediation cost by function</h3>
          {remByFn.length === 0
            ? <p className="empty">No underpaid employees in this view ✓</p>
            : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={remByFn} layout="vertical" margin={{ top: 5, right: 60, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={fmtL} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => fmtL(v)} />
                  <Bar dataKey="cost" fill={RED} radius={[0, 4, 4, 0]}>
                    <LabelList dataKey="cost" position="right" formatter={fmtL} style={{ fontSize: 11 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )
          }
        </div>

        {/* 4. Headcount by level (stacked bar) */}
        <div className="analytics-card">
          <h3>Headcount by level</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={headcountData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Women" stackId="a" fill={PINK} radius={[0, 0, 0, 0]} />
              <Bar dataKey="Men" stackId="a" fill={BLUE} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function CoefficientTable({ coeffs, r2 }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(coeffs);
  return (
    <div className="panel">
      <h2 className="collapsible" onClick={() => setOpen(!open)}>
        {open ? '▾' : '▸'} Model details (coefficients) <span className="panel-hint-inline">for the technically curious</span>
      </h2>
      {open && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Factor</th><th>Coefficient</th><th>Plain English</th><th>p-value</th><th>Significant?</th></tr></thead>
            <tbody>
              {entries.map(([name, c], i) => (
                <tr key={i} className={c.significant ? '' : 'muted'}>
                  <td className="mono">{name}</td><td className="mono">{c.coefficient.toFixed(4)}</td>
                  <td>{c.plain_english}</td><td className="mono">{c.p_value.toFixed(4)}</td>
                  <td>{c.significant ? '✅ Yes (p < 0.05)' : '— No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
