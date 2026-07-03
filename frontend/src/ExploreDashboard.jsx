import React, { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, ReferenceLine, LabelList,
} from 'recharts';
import { formatINR, formatCompact, pct, gapColor } from './format';
import {
  applyFilters, kpis, byFunction, headcountByLevel, payByLevel, histogram,
} from './analytics';

/**
 * Power BI-style cross-filtering explorer.
 * `rows` need base_salary, job_function, job_level, gender.
 * `filter` / `setFilter` lift state so the parent can share it with the chatbot.
 */
export default function ExploreDashboard({ rows, filter, setFilter }) {
  const filtered = useMemo(() => applyFilters(rows, filter), [rows, filter]);

  const k = useMemo(() => kpis(filtered), [filtered]);
  const fnData = useMemo(() => byFunction(filtered), [filtered]);
  const hcData = useMemo(() => headcountByLevel(filtered), [filtered]);
  const payLvl = useMemo(() => payByLevel(filtered), [filtered]);
  const hist = useMemo(() => histogram(filtered), [filtered]);

  const toggle = (dim, val) =>
    setFilter(f => ({ ...f, [dim]: f[dim] === val ? null : val }));

  const active = [
    filter.function && ['function', filter.function],
    filter.level && ['level', filter.level],
    filter.gender && ['gender', filter.gender],
  ].filter(Boolean);

  const mfBar = fnData.map(d => ({ name: d.name.replace('Management', 'Mgmt'), Men: d.maleMedian, Women: d.femaleMedian }));

  return (
    <div className="explore">
      <div className="explore-head">
        <h2>🔎 Interactive explorer</h2>
        <p className="panel-hint">Click any bar to filter — every chart and metric below updates together (cross-filter).</p>
        <div className="filter-bar">
          {active.length === 0 && <span className="filter-empty">No filters · showing all {rows.length}</span>}
          {active.map(([dim, val]) => (
            <span key={dim} className="filter-chip" onClick={() => setFilter(f => ({ ...f, [dim]: null }))}>
              {dim}: {val} ×
            </span>
          ))}
          {active.length > 0 &&
            <button className="filter-reset" onClick={() => setFilter({})}>Reset all</button>}
        </div>
      </div>

      {/* KPI strip (recomputes) */}
      <div className="mini-kpis">
        <Mini value={k.total} label="Employees" />
        <Mini value={`${k.femalePct}%`} label="Women" sub={`${k.femaleCount}F · ${k.maleCount}M`} />
        <Mini value={formatCompact(k.femaleMedian)} label="Women median" color="#e64980" />
        <Mini value={formatCompact(k.maleMedian)} label="Men median" color="#4c6ef5" />
        <Mini value={pct(k.rawGapPct)} label="Raw gap" color={gapColor(k.rawGapPct)} />
      </div>

      <div className="chart-grid">
        {/* Median pay by function - grouped, clickable */}
        <div className="chart-card">
          <h3>Median pay by function <Hint>click a bar to filter</Hint></h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={mfBar} margin={{ top: 6, right: 10, left: 0, bottom: 50 }}
              onClick={(e) => e && e.activeLabel && toggle('function', fnData.find(f => f.name.replace('Management','Mgmt') === e.activeLabel)?.name)}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" angle={-30} textAnchor="end" interval={0} height={60} tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={formatCompact} width={54} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => formatINR(v)} />
              <Legend />
              <Bar dataKey="Men" fill="#4c6ef5" radius={[3, 3, 0, 0]} cursor="pointer" />
              <Bar dataKey="Women" fill="#e64980" radius={[3, 3, 0, 0]} cursor="pointer" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Salary distribution histogram */}
        <div className="chart-card">
          <h3>Fixed-pay distribution <Hint>headcount per pay band</Hint></h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={hist} margin={{ top: 6, right: 10, left: 0, bottom: 50 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" angle={-30} textAnchor="end" interval={0} height={60} tick={{ fontSize: 10 }} />
              <YAxis width={30} tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Men" stackId="a" fill="#4c6ef5" />
              <Bar dataKey="Women" stackId="a" fill="#e64980" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Headcount by level & gender - stacked, clickable */}
        <div className="chart-card">
          <h3>Headcount by level <Hint>click to filter level</Hint></h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={hcData} margin={{ top: 6, right: 10, left: 0, bottom: 20 }}
              onClick={(e) => e && e.activeLabel && toggle('level', e.activeLabel)}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis width={30} tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Men" stackId="a" fill="#4c6ef5" cursor="pointer" />
              <Bar dataKey="Women" stackId="a" fill="#e64980" cursor="pointer" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Median pay by level - line-ish grouped */}
        <div className="chart-card">
          <h3>Median pay by level <Hint>career progression</Hint></h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={payLvl} margin={{ top: 6, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={formatCompact} width={54} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => formatINR(v)} />
              <Legend />
              <Bar dataKey="Men" fill="#4c6ef5" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Women" fill="#e64980" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gap by function - full width diverging, clickable */}
      <div className="chart-card">
        <h3>Like-for-like gap by function <Hint>green = fair, red = women underpaid · click to filter</Hint></h3>
        <ResponsiveContainer width="100%" height={Math.max(200, fnData.length * 40)}>
          <BarChart data={fnData.map(d => ({ name: d.name, gap: d.gapPct }))} layout="vertical"
            margin={{ top: 5, right: 60, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tickFormatter={(v) => v + '%'} tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => pct(v)} />
            <ReferenceLine x={0} stroke="#495057" strokeWidth={1.5} />
            <Bar dataKey="gap" radius={[3, 3, 3, 3]} cursor="pointer" onClick={(d) => toggle('function', d.name)}>
              {fnData.map((d, i) => (
                <Cell key={i} fill={gapColor(d.gapPct)}
                  opacity={filter.function && filter.function !== d.name ? 0.35 : 1} />
              ))}
              <LabelList dataKey="gap" position="right" formatter={(v) => pct(v)} style={{ fontSize: 11, fontWeight: 600 }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function Mini({ value, label, sub, color }) {
  return (
    <div className="mini">
      <div className="mini-value" style={color ? { color } : undefined}>{value}</div>
      <div className="mini-label">{label}</div>
      {sub && <div className="mini-sub">{sub}</div>}
    </div>
  );
}
const Hint = ({ children }) => <span className="chart-hint">{children}</span>;
