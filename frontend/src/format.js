// Indian number + currency formatting helpers. All money is whole rupees (no decimals).

export const API_URL = 'http://localhost:8000';

// ₹25,00,000  (Indian digit grouping)
export function formatINR(n) {
  if (n === null || n === undefined || isNaN(n)) return '—';
  const rounded = Math.round(Number(n));
  return '₹' + rounded.toLocaleString('en-IN');
}

// Compact: ₹25.0 L / ₹1.20 Cr — good for big headline numbers
export function formatCompact(n) {
  if (n === null || n === undefined || isNaN(n)) return '—';
  const v = Math.round(Number(n));
  const abs = Math.abs(v);
  if (abs >= 1_00_00_000) return '₹' + (v / 1_00_00_000).toFixed(2) + ' Cr';
  if (abs >= 1_00_000) return '₹' + (v / 1_00_000).toFixed(1) + ' L';
  return '₹' + v.toLocaleString('en-IN');
}

// Signed percentage, 1 dp
export function pct(n) {
  if (n === null || n === undefined || isNaN(n)) return '—';
  const v = Number(n);
  return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
}

// Color for a like-for-like GAP value (near-zero is good; large either way is bad)
export function gapColor(n) {
  const v = Number(n);
  if (v <= -5) return '#e03131';   // red
  if (v <= -2) return '#f08c00';   // amber
  if (v < 2) return '#2f9e44';     // green (equitable)
  if (v < 5) return '#f08c00';     // amber (women higher — watch)
  return '#e03131';
}

// Simple sign color: positive = green, negative = red (used for median position/gap).
export function posNegColor(n) {
  return Number(n) >= 0 ? '#2f9e44' : '#e03131';
}
