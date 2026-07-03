import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, ReferenceLine, LabelList,
  PieChart, Pie, LineChart, Line,
} from 'recharts';
import { API_URL, formatINR, pct, posNegColor } from './format';
import { applyFilters, filteredMedianStats, median, isF, isM, payByLevel, headcountByLevel } from './analytics';
import ExploreDashboard from './ExploreDashboard';
import Insights from './Insights';
import ChatBot from './ChatBot';
import BudgetPlanner from './BudgetPlanner';
import ExportReport from './ExportReport';

const PAGE_SIZE = 500;

export default function MedianDashboard({ onHome, savedData, onDataChange }) {
  const [data, setData] = useState(savedData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [source, setSource] = useState(savedData ? 'Restored from last session' : null);
  const [useBenchmark, setUseBenchmark] = useState(true);
  const [filter, setFilter] = useState({});
  const [empFile, setEmpFile] = useState(null);

  function handleData(d, src) { setData(d); setSource(src); setFilter({}); onDataChange(d); }

  async function loadSample() {
    setLoading(true); setError(null);
    try {
      const s = await (await fetch(`${API_URL}/api/sample-data`)).json();
      let median_table = null;
      if (useBenchmark) median_table = (await (await fetch(`${API_URL}/api/sample-median`)).json()).data;
      const res = await fetch(`${API_URL}/api/analyze-median`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employees: s.data, median_table }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Analysis failed');
      handleData(await res.json(), `Sample dataset · ${s.rows} employees`);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function uploadCsv(medianFile) {
    if (!empFile) { setError('Please choose an employee CSV first.'); return; }
    setLoading(true); setError(null);
    try {
      const fd = new FormData(); fd.append('file', empFile);
      if (medianFile) fd.append('median_file', medianFile);
      const res = await fetch(`${API_URL}/api/analyze-median-upload`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error((await res.json()).detail || 'Analysis failed');
      handleData(await res.json(), `Uploaded · ${empFile.name}${medianFile ? ' + medians' : ''}`);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  function clearData() { setData(null); setSource(null); setFilter({}); onDataChange(null); }

  return (
    <div className="app">
      <div className="topbar">
        <button className="btn btn-ghost" onClick={onHome}>← Home</button>
        <div className="topbar-title">
          <h1>📊 Linear (Median) Model</h1>
          {source && <span className="topbar-sub">{source}</span>}
        </div>
        {data && <button className="btn btn-ghost" onClick={clearData}>↻ Change data</button>}
      </div>

      {!data && (
        <div className="datasource">
          <div className="ds-card">
            <h3>Try it instantly</h3>
            <p>Compare the sample workforce against a median line.</p>
            <label className="check">
              <input type="checkbox" checked={useBenchmark} onChange={e => setUseBenchmark(e.target.checked)} />
              Use sample market medians (uncheck to compute from the data)
            </label>
            <button className="btn btn-primary" onClick={loadSample} disabled={loading}>
              {loading ? 'Analysing…' : '▶ Load sample data'}
            </button>
          </div>
          <div className="ds-or">or</div>
          <div className="ds-card">
            <h3>Upload your data</h3>
            <label className="upload-row"><span>1. Employee CSV (required)</span>
              <input type="file" accept=".csv" onChange={e => setEmpFile(e.target.files[0])} /></label>
            <label className="upload-row"><span>2. Median benchmark CSV (optional)</span>
              <input type="file" accept=".csv" id="medianFile" /></label>
            <p className="mono-hint">Median file columns: job_function, job_level, median_salary</p>
            <button className="btn btn-primary" disabled={loading || !empFile}
              onClick={() => uploadCsv(document.getElementById('medianFile').files[0])}>
              {loading ? 'Analysing…' : 'Analyse uploaded data'}
            </button>
            <div className="download-row">
              <a className="dl-link" href={`${API_URL}/api/template/employee`}>⬇ Employee template</a>
              <a className="dl-link" href={`${API_URL}/api/template/median`}>⬇ Median template</a>
              <a className="dl-link" href={`${API_URL}/api/download/sample-median`}>⬇ Sample medians</a>
            </div>
          </div>
          {error && <div className="error-banner">❌ {error}</div>}
        </div>
      )}

      {data && <Results data={data} filter={filter} setFilter={setFilter} />}
    </div>
  );
}

function Results({ data, filter, setFilter }) {
  const s = data.summary;
  const sourceLabel = data.median_source === 'uploaded' ? 'uploaded market benchmark' : 'medians computed from your data';

  const hasFilter = !!(filter.function || filter.level || filter.gender);

  const allEmployees = useMemo(
    () => [...data.employees].sort((a, b) => a.gap_pct - b.gap_pct),
    [data]
  );

  const filteredEmployees = useMemo(
    () => applyFilters(allEmployees, filter),
    [allEmployees, filter]
  );

  const fs = useMemo(() => filteredMedianStats(filteredEmployees), [filteredEmployees]);

  // Compute median salaries per gender for MF chips
  const femaleEmps = useMemo(() => filteredEmployees.filter(e => isF(e.gender)), [filteredEmployees]);
  const maleEmps = useMemo(() => filteredEmployees.filter(e => isM(e.gender)), [filteredEmployees]);
  const femaleMedSalary = useMemo(() => median(femaleEmps.map(e => e.base_salary)), [femaleEmps]);
  const maleMedSalary = useMemo(() => median(maleEmps.map(e => e.base_salary)), [maleEmps]);
  const rawGapPct = maleMedSalary > 0 ? +((femaleMedSalary - maleMedSalary) / maleMedSalary * 100).toFixed(1) : 0;

  // Cost impact computations
  const belowMedianEmps = useMemo(() => filteredEmployees.filter(e => e.below_median), [filteredEmployees]);
  const aboveMedianEmps = useMemo(() => filteredEmployees.filter(e => e.gap_pct > 15), [filteredEmployees]);
  const totalPayroll = useMemo(() => filteredEmployees.reduce((s, e) => s + (e.base_salary || 0), 0), [filteredEmployees]);
  const belowMedianCost = useMemo(
    () => belowMedianEmps.reduce((s, e) => s + Math.abs(e.gap_rupees || 0), 0),
    [belowMedianEmps]
  );
  const aboveMedianExcess = useMemo(
    () => aboveMedianEmps.reduce((s, e) => s + Math.max(0, e.gap_rupees || 0), 0),
    [aboveMedianEmps]
  );

  // By-function callouts
  const worst = data.by_function[0];
  const best = [...data.by_function].sort((a, b) => Math.abs(a.gap_vs_median_pct) - Math.abs(b.gap_vs_median_pct))[0];

  // Roster 3-way toggle
  const [rosterFilter, setRosterFilter] = useState('all'); // 'all' | 'below' | 'above'
  const [rosterPage, setRosterPage] = useState(0);

  const rosterRows = useMemo(() => {
    if (rosterFilter === 'below') return [...belowMedianEmps].sort((a, b) => a.gap_pct - b.gap_pct);
    if (rosterFilter === 'above') return [...aboveMedianEmps].sort((a, b) => b.gap_pct - a.gap_pct);
    return filteredEmployees;
  }, [filteredEmployees, belowMedianEmps, aboveMedianEmps, rosterFilter]);

  const totalRosterPages = Math.ceil(rosterRows.length / PAGE_SIZE);
  const pageRows = rosterRows.slice(rosterPage * PAGE_SIZE, (rosterPage + 1) * PAGE_SIZE);

  useMemo(() => { setRosterPage(0); }, [filter, rosterFilter]);

  const displayGap = hasFilter ? fs.genderGapVsMedianPct : s.gender_gap_vs_median_pct;
  const displayFemBelow = hasFilter ? fs.femaleBelowPct : s.female_below_median_pct;
  const displayMalBelow = hasFilter ? fs.maleBelowPct : s.male_below_median_pct;

  const reportData = useMemo(() => {
    const filterLabel = [
      filter.function && `Function: ${filter.function}`,
      filter.level && `Level: ${filter.level}`,
      filter.gender && `Gender: ${filter.gender}`,
    ].filter(Boolean).join(' · ') || 'All employees';
    return {
      model: 'median',
      filterLabel,
      hasFilter,
      kpis: [
        { label: 'Gender gap vs median', value: pct(displayGap), isNegative: displayGap < -1 },
        { label: 'Women below median', value: `${displayFemBelow}%`, isNegative: displayFemBelow > displayMalBelow + 5 },
        { label: 'Men below median', value: `${displayMalBelow}%` },
        { label: 'Below median (total)', value: String(belowMedianEmps.length), isNegative: belowMedianEmps.length > 0 },
        { label: 'Cost to bring to median', value: fmtL(belowMedianCost), isNegative: belowMedianCost > 0 },
        { label: 'Total payroll', value: fmtL(totalPayroll) },
      ],
      insights: data.insights,
      recommendations: data.recommendations,
    };
  }, [filter, hasFilter, displayGap, displayFemBelow, displayMalBelow, belowMedianEmps, belowMedianCost, totalPayroll, data.insights, data.recommendations]);

  const buildContext = () => ({
    method: 'median',
    gender_gap_vs_median_pct: displayGap,
    female_below_median_pct: displayFemBelow,
    male_below_median_pct: displayMalBelow,
    female_count: hasFilter ? fs.femaleCount : s.female_count,
    male_count: hasFilter ? fs.maleCount : s.male_count,
    below_median_count: belowMedianEmps.length,
    below_median_cost: belowMedianCost,
    above_median_count: aboveMedianEmps.length,
    total_payroll: totalPayroll,
    by_function: data.by_function.map(f => ({ name: f.name, gap_vs_median_pct: f.gap_vs_median_pct })),
    worst_function: worst,
    best_function: best,
    employees: filteredEmployees.map(e => ({
      id: e.employee_id, title: e.job_title, function: e.job_function,
      level: e.job_level, gender: e.gender, salary: e.base_salary,
      cohort_median: e.cohort_median, gap: e.gap_rupees, below: e.below_median,
      above: e.gap_pct > 15,
    })),
  });

  return (
    <div className="results">
      {/* 1. Filter banner */}
      {hasFilter && (
        <div className="filter-active-banner">
          🔎 Filtered view · {filteredEmployees.length} of {data.employees.length} employees — all stats reflect this filter.
          <button onClick={() => setFilter({})}>Clear filter ×</button>
        </div>
      )}

      {/* 2. Stat cards */}
      <div className="cards">
        <StatCard value={hasFilter ? fs.total : s.total_employees} label="Headcount reviewed"
          sub={hasFilter ? `of ${s.total_employees} total` : null} />
        <StatCard value={pct(displayGap)} label="Gender pay gap vs midpoint"
          color={posNegColor(displayGap)}
          hint={`Women's avg pay positioning minus men's vs cohort midpoint${hasFilter ? ' · filtered' : ''}`} />
        <StatCard value={`${displayFemBelow}%`} label="Women below midpoint"
          hint={`vs ${displayMalBelow}% of men${hasFilter ? ' · filtered' : ''}`} />
        <StatCard value={hasFilter ? `${belowMedianEmps.length}` : s.cohorts} label={hasFilter ? 'Below midpoint (filtered)' : 'Cohorts (function × grade)'}
          hint={hasFilter ? `${aboveMedianEmps.length} above range (>15%)` : null} />
      </div>

      {/* 3. AI Insights */}
      <Insights insights={data.insights} />

      {/* 4. About this methodology */}
      <div className="panel">
        <h2>About this methodology</h2>
        <div className="explain-grid">
          <Explainer title="The cohort midpoint" icon="📏">
            Every employee's fixed pay is benchmarked against the <strong>median of their cohort</strong> (function + grade),
            using the <strong>{sourceLabel}</strong>.
          </Explainer>
          <Explainer title="Pay positioning vs midpoint" icon="🧭">
            <strong>0%</strong> = fixed pay exactly at cohort midpoint.{' '}
            <span style={{ color: '#2f9e44', fontWeight: 700 }}>Positive</span> = above midpoint,{' '}
            <span style={{ color: '#e03131', fontWeight: 700 }}>negative</span> = below.
          </Explainer>
          <Explainer title="Why this model" icon="💡">
            No statistical assumptions required — audit-ready and straightforward to present to leadership or an external reviewer.
          </Explainer>
          <Explainer title="Interpreting the gender pay gap" icon="⚖️">
            <strong>Gender pay gap vs midpoint</strong> = women's average pay positioning minus men's.
            A negative figure means women sit further below the fair pay line.
          </Explainer>
        </div>
      </div>

      {/* 5. Male vs Female summary chips */}
      <div className="panel">
        <h2>Pay positioning by gender {hasFilter && <span className="filter-note">filtered</span>}</h2>
        <div className="mf-summary">
          <div className="mf-chip mf-male">
            <span>Men — median fixed pay</span>
            <strong>{formatINR(Math.round(maleMedSalary))}</strong>
            <small>{hasFilter ? fs.maleCount : s.male_count} employees · avg {displayMalBelow}% below midpoint</small>
          </div>
          <div className="mf-chip mf-female">
            <span>Women — median fixed pay</span>
            <strong>{formatINR(Math.round(femaleMedSalary))}</strong>
            <small>{hasFilter ? fs.femaleCount : s.female_count} employees · avg {displayFemBelow}% below midpoint</small>
          </div>
          <div className="mf-chip mf-gap" style={{ borderColor: posNegColor(rawGapPct) }}>
            <span>Unadjusted pay gap (women vs men)</span>
            <strong style={{ color: posNegColor(rawGapPct) }}>{pct(rawGapPct)}</strong>
            <small>gender pay gap vs midpoint: {pct(displayGap)}</small>
          </div>
        </div>
      </div>

      {/* 6. Best / Worst callouts */}
      <div className="callouts">
        <MedianCallout kind="good" title="Best-practice function" fn={best} />
        <MedianCallout kind="bad" title="Highest-risk function" fn={worst} />
      </div>

      {/* 7. Charts */}
      <div className="panel">
        <h2>Pay positioning vs cohort midpoint</h2>
        <p className="panel-hint">
          Average pay positioning above/below cohort midpoint, by function.{' '}
          <span style={{ color: '#2f9e44' }}>Above 0 = above midpoint</span>,{' '}
          <span style={{ color: '#e03131' }}>below 0 = below midpoint</span>.
        </p>
        <PositionChart rows={data.by_function} />
      </div>

      <div className="panel">
        <h2>Gender pay gap by function</h2>
        <p className="panel-hint">
          Women's average positioning minus men's vs cohort midpoint.{' '}
          <span style={{ color: '#2f9e44' }}>Green = women at or above men</span>,{' '}
          <span style={{ color: '#e03131' }}>red = women below</span>. Click to filter.
        </p>
        <GapChart rows={data.by_function} field="gap_vs_median_pct" selected={filter.function}
          onSelect={(name) => setFilter(f => ({ ...f, function: f.function === name ? null : name }))} />
      </div>

      {/* 8. Interactive Explorer */}
      <div className="panel">
        <ExploreDashboard rows={data.employees} filter={filter} setFilter={setFilter} />
      </div>

      {/* 8b. Analytics charts */}
      <ExportReport reportData={reportData} />
      <MedianAnalytics employees={filteredEmployees} summary={s} fs={fs} hasFilter={hasFilter}
        belowMedianCost={belowMedianCost} belowCount={belowMedianEmps.length}
        aboveCount={aboveMedianEmps.length} totalPayroll={totalPayroll} />

      {/* 9. Recommended actions */}
      {data.recommendations && (
        <div className="panel actions-panel">
          <h2>Recommended Actions</h2>
          <div className={`rec-banner sev-${(data.recommendations.severity || '').toLowerCase()}`}>
            <div className="rec-head">
              <span className="rec-pattern">{data.recommendations.pattern}</span>
              <span className="rec-sev">Severity: {data.recommendations.severity}</span>
            </div>
            <p>{data.recommendations.message}</p>
          </div>
          <ol className="action-list">
            {data.recommendations.actions.map((a, i) => <li key={i}>{a}</li>)}
          </ol>
        </div>
      )}

      {/* 10. Cost impact */}
      <div className="panel cost-impact-panel">
        <h2>💸 Equity Remediation Cost {hasFilter && <span className="filter-note">filtered</span>}</h2>
        <div className="cost-impact-grid">
          <div className="cost-item cost-underpaid">
            <span>⚠️ Employees below cohort midpoint</span>
            <strong>{belowMedianEmps.length}</strong>
            <em>Annual equity adjustment to midpoint: <b>{formatINR(belowMedianCost)}</b></em>
          </div>
          <div className="cost-item cost-overpaid">
            <span>📈 Above-range employees (&gt;15% vs midpoint)</span>
            <strong>{aboveMedianEmps.length}</strong>
            <em>Above-range excess pay: <b>{formatINR(aboveMedianExcess)}</b></em>
          </div>
          <div className="cost-item cost-payroll">
            <span>Total fixed pay {hasFilter ? '(filtered)' : ''}</span>
            <strong>{formatINR(totalPayroll)}</strong>
            <em>Equity gap = <b>{totalPayroll > 0 ? ((belowMedianCost / totalPayroll) * 100).toFixed(1) : '0'}%</b> of total fixed pay</em>
          </div>
          {aboveMedianEmps.length > 0 && belowMedianCost > 0 && (
            <div className="cost-item cost-net">
              <span>💡 Attrition offset opportunity</span>
              <strong>{formatINR(Math.min(aboveMedianExcess, belowMedianCost))}</strong>
              <em>If above-range employees exit naturally, backfilling at midpoint rates could offset a portion of the equity adjustment cost.</em>
            </div>
          )}
        </div>
      </div>

      {/* 11. Budget planner */}
      <BudgetPlanner totalPayroll={totalPayroll} remediationCost={belowMedianCost} filtered={hasFilter} />

      {/* 12. Employee roster with 3-way toggle */}
      <div className="panel">
        <div className="roster-head">
          <h2>
            Employee Pay Detail
            {hasFilter && <span className="filter-note">filtered</span>}
            <span className="count-badge">{rosterRows.length}</span>
          </h2>
        </div>
        <QuickRosterFilter allRows={data.employees} filter={filter} setFilter={setFilter} />
        <div className="roster-filter-tabs">
          <button className={rosterFilter === 'all' ? 'tab active' : 'tab'}
            onClick={() => setRosterFilter('all')}>
            Full headcount ({filteredEmployees.length})
          </button>
          <button className={rosterFilter === 'below' ? 'tab active tab-warn' : 'tab'}
            onClick={() => setRosterFilter('below')}>
            ⚠️ Below midpoint ({belowMedianEmps.length})
          </button>
          <button className={rosterFilter === 'above' ? 'tab active tab-above' : 'tab'}
            onClick={() => setRosterFilter('above')}>
            📈 Above range &gt;15% ({aboveMedianEmps.length})
          </button>
        </div>
        <p className="panel-hint">
          {rosterFilter === 'all' && 'Full headcount sorted by pay positioning vs cohort midpoint (furthest below first). ⚠️ = below midpoint, 📈 = above range.'}
          {rosterFilter === 'below' && 'Employees whose fixed pay falls below their cohort midpoint. Sorted by largest shortfall.'}
          {rosterFilter === 'above' && 'Employees paid more than 15% above their cohort midpoint. Sorted by largest overage.'}
          {totalRosterPages > 1 && ` · Page ${rosterPage + 1} of ${totalRosterPages} (${PAGE_SIZE}/page)`}
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th><th>Function</th><th>Level</th><th>Gender</th>
                <th>Fixed pay</th><th>Cohort median</th><th>Gap ₹</th><th>Gap %</th>
                {rosterFilter === 'all' && <th>Status</th>}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((e, i) => (
                <tr key={i} className={e.below_median ? 'below' : e.gap_pct > 15 ? 'above-model' : ''}>
                  <td className="mono">{e.employee_id}</td>
                  <td>{e.job_function}</td>
                  <td>{e.job_level}</td>
                  <td>{e.gender}</td>
                  <td>{formatINR(e.base_salary)}</td>
                  <td>{formatINR(e.cohort_median)}</td>
                  <td style={{ color: posNegColor(e.gap_rupees), fontWeight: 600 }}>
                    {e.gap_rupees < 0 ? `-${formatINR(Math.abs(e.gap_rupees))}` : formatINR(e.gap_rupees)}
                  </td>
                  <td style={{ color: posNegColor(e.gap_pct), fontWeight: 600 }}>{e.gap_pct.toFixed(1)}%</td>
                  {rosterFilter === 'all' && (
                    <td>{e.below_median ? '⚠️ Below' : e.gap_pct > 15 ? '📈 Above' : '✓'}</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {totalRosterPages > 1 && (
          <div className="pagination">
            <button onClick={() => setRosterPage(p => Math.max(0, p - 1))} disabled={rosterPage === 0}>← Prev</button>
            <span>Page {rosterPage + 1} / {totalRosterPages}</span>
            <button onClick={() => setRosterPage(p => Math.min(totalRosterPages - 1, p + 1))} disabled={rosterPage >= totalRosterPages - 1}>Next →</button>
          </div>
        )}
      </div>

      {/* 13. Chatbot */}
      <ChatBot buildContext={buildContext} model="median" />
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

function MedianAnalytics({ employees, summary, fs, hasFilter, belowMedianCost, belowCount, aboveCount, totalPayroll }) {
  const femCount = hasFilter ? fs.femaleCount : (summary.female_count || 0);
  const malCount = hasFilter ? fs.maleCount : (summary.male_count || 0);

  const genderPieData = [
    { name: 'Women', value: femCount },
    { name: 'Men', value: malCount },
  ];

  // Pay by level line chart
  const payLevelData = useMemo(() => payByLevel(employees), [employees]);

  // Headcount by level
  const headcountData = useMemo(() => headcountByLevel(employees), [employees]);

  // Below-median pct by function (F vs M grouped bar)
  const belowByFn = useMemo(() => {
    const acc = {};
    employees.forEach(e => {
      const fn = e.job_function || 'Other';
      if (!acc[fn]) acc[fn] = { name: fn, f: 0, fTotal: 0, m: 0, mTotal: 0 };
      if (isF(e.gender)) { acc[fn].fTotal++; if (e.below_median) acc[fn].f++; }
      else if (isM(e.gender)) { acc[fn].mTotal++; if (e.below_median) acc[fn].m++; }
    });
    return Object.values(acc).map(r => ({
      name: r.name,
      Women: r.fTotal ? +(r.f / r.fTotal * 100).toFixed(0) : 0,
      Men: r.mTotal ? +(r.m / r.mTotal * 100).toFixed(0) : 0,
    })).sort((a, b) => b.Women - a.Women);
  }, [employees]);

  // Status distribution pie (below / above / at-median)
  const statusPie = useMemo(() => {
    const below = employees.filter(e => e.below_median).length;
    const above = employees.filter(e => e.gap_pct > 15).length;
    const atMed = employees.length - below - above;
    return [
      { name: 'Below median', value: below },
      { name: 'At/near median', value: atMed },
      { name: 'Above >15%', value: above },
    ].filter(d => d.value > 0);
  }, [employees]);

  return (
    <div className="panel analytics-panel">
      <h2>📊 Pay Equity Overview {hasFilter && <span className="filter-note">filtered</span>}</h2>

      {/* Totals row */}
      <div className="analytics-totals">
        <div className="a-total"><span>Headcount reviewed</span><strong>{employees.length}</strong></div>
        <div className="a-total"><span>Total fixed pay</span><strong>{fmtL(totalPayroll)}</strong></div>
        <div className="a-total warn"><span>Below midpoint</span><strong>{belowCount}</strong></div>
        <div className="a-total warn"><span>Equity adj. cost</span><strong>{fmtL(belowMedianCost)}</strong></div>
        <div className="a-total good"><span>Above range &gt;15%</span><strong>{aboveCount}</strong></div>
        <div className="a-total"><span>Gap as % of fixed pay</span><strong>{totalPayroll > 0 ? ((belowMedianCost / totalPayroll) * 100).toFixed(1) : 0}%</strong></div>
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

        {/* 2. Pay positioning status pie */}
        <div className="analytics-card">
          <h3>Pay positioning vs midpoint</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={statusPie} cx="50%" cy="50%" outerRadius={75} dataKey="value"
                label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                labelLine={false}>
                <Cell fill={RED} />
                <Cell fill={GREEN} />
                <Cell fill={BLUE} />
              </Pie>
              <Tooltip formatter={(v, n) => [v + ' employees', n]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 3. Below-median % by function — F vs M */}
        <div className="analytics-card">
          <h3>% below median by function</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={belowByFn} margin={{ top: 10, right: 20, left: 0, bottom: 50 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" angle={-30} textAnchor="end" interval={0} height={60} tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => v + '%'} tick={{ fontSize: 11 }} width={36} />
              <Tooltip formatter={v => v + '%'} />
              <Legend />
              <Bar dataKey="Women" fill={PINK} radius={[3, 3, 0, 0]} />
              <Bar dataKey="Men" fill={BLUE} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 4. Median pay by level */}
        <div className="analytics-card">
          <h3>Median pay by level</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={payLevelData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={fmtL} width={54} tick={{ fontSize: 11 }} />
              <Tooltip formatter={v => fmtL(v)} />
              <Legend />
              <Line type="monotone" dataKey="Women" stroke={PINK} strokeWidth={2.5} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="Men" stroke={BLUE} strokeWidth={2.5} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
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

function MedianCallout({ kind, title, fn }) {
  if (!fn) return null;
  return (
    <div className={`callout callout-${kind}`}>
      <div className="callout-label">{kind === 'good' ? '✅' : '⚠️'} {title}</div>
      <div className="callout-fn">{fn.name}</div>
      <div className="callout-gap" style={{ color: posNegColor(fn.gap_vs_median_pct) }}>
        {pct(fn.gap_vs_median_pct)} <span>gap vs median</span>
      </div>
      <div className="callout-verdict">
        {kind === 'good' ? 'Most balanced — replicate their pay practices' : 'Prioritise corrections here first'}
      </div>
    </div>
  );
}

function PositionChart({ rows }) {
  const chartData = rows.map(r => ({
    name: r.name.replace('Management', 'Mgmt'),
    Women: r.female_position_pct,
    Men: r.male_position_pct,
  }));
  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" angle={-30} textAnchor="end" interval={0} height={70} tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v) => v + '%'} width={50} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v) => pct(v)} />
        <Legend />
        <ReferenceLine y={0} stroke="#495057" />
        <Bar dataKey="Men" fill="#4c6ef5" radius={[3, 3, 0, 0]} />
        <Bar dataKey="Women" fill="#e64980" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function GapChart({ rows, field, selected, onSelect }) {
  const chartData = rows.map(r => ({ name: r.name, gap: r[field] }));
  const height = Math.max(220, chartData.length * 42);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 60, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tickFormatter={(v) => v + '%'} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v) => pct(v)} />
        <ReferenceLine x={0} stroke="#495057" strokeWidth={1.5} />
        <Bar dataKey="gap" cursor="pointer" onClick={(d) => onSelect(d.name)} radius={[3, 3, 3, 3]}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={posNegColor(d.gap)} opacity={selected && selected !== d.name ? 0.35 : 1}
              stroke={selected === d.name ? '#212529' : 'none'} strokeWidth={2} />
          ))}
          <LabelList dataKey="gap" position="right" formatter={(v) => pct(v)} style={{ fontSize: 12, fontWeight: 600 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
