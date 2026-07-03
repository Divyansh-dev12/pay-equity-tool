import React from 'react';

const TONE = {
  critical: { icon: '🔴', cls: 'ins-critical' },
  warning: { icon: '🟠', cls: 'ins-warning' },
  good: { icon: '🟢', cls: 'ins-good' },
  info: { icon: '🔵', cls: 'ins-info' },
};

export default function Insights({ insights }) {
  if (!insights || !insights.length) return null;
  return (
    <div className="panel">
      <h2>🤖 AI insights</h2>
      <p className="panel-hint">Auto-generated read of your data, most important first.</p>
      <div className="insights-grid">
        {insights.map((it, i) => {
          const t = TONE[it.tone] || TONE.info;
          return (
            <div key={i} className={`insight ${t.cls}`}>
              <div className="insight-title">{t.icon} {it.title}</div>
              <p>{it.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
