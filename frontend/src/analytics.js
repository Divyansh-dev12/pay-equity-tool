// Client-side analytics so charts can recompute instantly when cross-filters change.
// Works on any array of rows that have: base_salary, job_function, job_level, gender.

export const isF = (g) => ['female', 'f'].includes(String(g || '').toLowerCase());
export const isM = (g) => ['male', 'm'].includes(String(g || '').toLowerCase());

export function median(arr) {
  if (!arr.length) return 0;
  const s = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}
export const mean = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);

export function applyFilters(rows, f) {
  return rows.filter(r =>
    (!f.function || r.job_function === f.function) &&
    (!f.level || r.job_level === f.level) &&
    (!f.gender || (f.gender === 'Female' ? isF(r.gender) : isM(r.gender)))
  );
}

export function kpis(rows) {
  const fem = rows.filter(r => isF(r.gender)).map(r => r.base_salary);
  const male = rows.filter(r => isM(r.gender)).map(r => r.base_salary);
  const medF = median(fem), medM = median(male);
  return {
    total: rows.length,
    femaleCount: fem.length,
    maleCount: male.length,
    femalePct: rows.length ? Math.round(fem.length / rows.length * 100) : 0,
    femaleMedian: Math.round(medF),
    maleMedian: Math.round(medM),
    rawGapPct: medM ? +(((medF - medM) / medM) * 100).toFixed(1) : 0,
  };
}

// Level-adjusted (mean-based) gap for a subset — strips level composition.
function levelAdjustedGap(rows) {
  const byLvl = {};
  rows.forEach(r => { (byLvl[r.job_level] ||= []).push(r); });
  let num = 0, den = 0;
  Object.values(byLvl).forEach(cell => {
    const f = cell.filter(r => isF(r.gender)).map(r => r.base_salary);
    const m = cell.filter(r => isM(r.gender)).map(r => r.base_salary);
    if (f.length && m.length && mean(m) > 0) {
      num += ((mean(f) - mean(m)) / mean(m)) * cell.length;
      den += cell.length;
    }
  });
  return den ? +((num / den) * 100).toFixed(1) : 0;
}

export function byFunction(rows) {
  const groups = {};
  rows.forEach(r => { (groups[r.job_function] ||= []).push(r); });
  return Object.entries(groups).map(([name, rs]) => {
    const f = rs.filter(r => isF(r.gender)).map(r => r.base_salary);
    const m = rs.filter(r => isM(r.gender)).map(r => r.base_salary);
    return {
      name,
      headcount: rs.length,
      femaleMedian: Math.round(median(f)),
      maleMedian: Math.round(median(m)),
      gapPct: levelAdjustedGap(rs),
    };
  }).sort((a, b) => a.gapPct - b.gapPct);
}

export function headcountByLevel(rows) {
  const groups = {};
  rows.forEach(r => { (groups[r.job_level] ||= { Women: 0, Men: 0 }); if (isF(r.gender)) groups[r.job_level].Women++; else if (isM(r.gender)) groups[r.job_level].Men++; });
  return Object.entries(groups)
    .map(([name, v]) => ({ name, ...v }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function payByLevel(rows) {
  const groups = {};
  rows.forEach(r => { (groups[r.job_level] ||= []).push(r); });
  return Object.entries(groups).map(([name, rs]) => ({
    name,
    Women: Math.round(median(rs.filter(r => isF(r.gender)).map(r => r.base_salary))),
    Men: Math.round(median(rs.filter(r => isM(r.gender)).map(r => r.base_salary))),
  })).sort((a, b) => a.name.localeCompare(b.name));
}

// Recompute KPIs from filtered regression predictions (for filter-aware stat cards).
export function filteredRegressionStats(rows) {
  const fem = rows.filter(r => isF(r.gender));
  const mal = rows.filter(r => isM(r.gender));
  const medF = median(fem.map(r => r.base_salary));
  const medM = median(mal.map(r => r.base_salary));
  const underpaid = rows.filter(r => r.is_underpaid_outlier);
  return {
    total: rows.length,
    femaleCount: fem.length,
    maleCount: mal.length,
    femaleMedian: Math.round(medF),
    maleMedian: Math.round(medM),
    rawGapPct: medM ? +((medF - medM) / medM * 100).toFixed(1) : 0,
    underpaidCount: underpaid.length,
    remediationCost: underpaid.reduce((s, r) => s + Math.abs(r.gap_dollars || 0), 0),
  };
}

// Recompute KPIs from filtered median employees (for filter-aware stat cards).
export function filteredMedianStats(rows) {
  const fem = rows.filter(r => isF(r.gender));
  const mal = rows.filter(r => isM(r.gender));
  const femPos = mean(fem.map(r => r.gap_pct || 0));
  const malPos = mean(mal.map(r => r.gap_pct || 0));
  const femBelow = fem.filter(r => r.below_median).length;
  const malBelow = mal.filter(r => r.below_median).length;
  return {
    total: rows.length,
    femaleCount: fem.length,
    maleCount: mal.length,
    genderGapVsMedianPct: +((femPos - malPos).toFixed(1)),
    femaleBelowPct: fem.length ? +(femBelow / fem.length * 100).toFixed(0) : 0,
    maleBelowPct: mal.length ? +(malBelow / mal.length * 100).toFixed(0) : 0,
  };
}

// Salary distribution histogram with gender split.
export function histogram(rows, binCount = 8) {
  const vals = rows.map(r => r.base_salary).filter(v => v > 0);
  if (!vals.length) return [];
  const min = Math.min(...vals), max = Math.max(...vals);
  const width = (max - min) / binCount || 1;
  const bins = Array.from({ length: binCount }, (_, i) => ({
    lo: min + i * width, hi: min + (i + 1) * width, Women: 0, Men: 0,
  }));
  rows.forEach(r => {
    let idx = Math.floor((r.base_salary - min) / width);
    if (idx >= binCount) idx = binCount - 1;
    if (idx < 0) idx = 0;
    if (isF(r.gender)) bins[idx].Women++; else if (isM(r.gender)) bins[idx].Men++;
  });
  return bins.map(b => ({
    name: `${(b.lo / 1_00_000).toFixed(0)}-${(b.hi / 1_00_000).toFixed(0)}L`,
    Women: b.Women, Men: b.Men,
  }));
}
