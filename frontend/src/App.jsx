import React, { useState } from 'react';
import './App.css';
import RegressionDashboard from './RegressionDashboard';
import MedianDashboard from './MedianDashboard';

function loadCached(key) {
  try { return JSON.parse(sessionStorage.getItem(key)); } catch { return null; }
}
function saveCache(key, data) {
  try {
    if (data) sessionStorage.setItem(key, JSON.stringify(data));
    else sessionStorage.removeItem(key);
  } catch {}
}

export default function App() {
  const [view, setView] = useState('landing');
  const [regressionData, setRegressionData] = useState(() => loadCached('pex-regression'));
  const [medianData, setMedianData] = useState(() => loadCached('pex-median'));

  function setRegData(data) { setRegressionData(data); saveCache('pex-regression', data); }
  function setMedData(data) { setMedianData(data); saveCache('pex-median', data); }

  if (view === 'regression') return (
    <RegressionDashboard onHome={() => setView('landing')} savedData={regressionData} onDataChange={setRegData} />
  );
  if (view === 'median') return (
    <MedianDashboard onHome={() => setView('landing')} savedData={medianData} onDataChange={setMedData} />
  );

  return (
    <div className="app">
      <header className="hero">
        <h1>⚖️ Pay Equity Studio</h1>
        <p>Two complementary lenses on gender pay equity for your workforce</p>
      </header>

      <div className="tiles">
        <button className="tile" onClick={() => setView('regression')}>
          <div className="tile-icon">📈</div>
          <h2>Regression Model</h2>
          <p className="tile-tag">Explains pay with statistics</p>
          <p className="tile-desc">
            Fits a multiple-regression model on level, tenure, performance, function
            and location, then isolates the <strong>unexplained gender gap</strong> that
            remains after those factors are held equal.
          </p>
          <ul className="tile-points">
            <li>Controlled vs uncontrolled gap</li>
            <li>Statistical significance (p-values)</li>
            <li>Flags individuals paid below model</li>
          </ul>
          {regressionData && <span className="tile-resume">▶ Resume last session</span>}
          <span className="tile-cta">Open Regression Model →</span>
        </button>

        <button className="tile" onClick={() => setView('median')}>
          <div className="tile-icon">📊</div>
          <h2>Linear (Median) Model</h2>
          <p className="tile-tag">Compares pay to a median line</p>
          <p className="tile-desc">
            Compares every employee to the <strong>median fixed pay</strong> of their
            cohort (function + level). Upload your own market medians, or let the tool
            compute them from your data.
          </p>
          <ul className="tile-points">
            <li>Upload a median benchmark table</li>
            <li>How far each gender sits from median</li>
            <li>Simple, transparent, no model needed</li>
          </ul>
          {medianData && <span className="tile-resume">▶ Resume last session</span>}
          <span className="tile-cta">Open Median Model →</span>
        </button>
      </div>

      <footer className="footer">
        Methodology: Multiple Linear Regression (OLS) &amp; median benchmarking · Fixed pay in INR
      </footer>
    </div>
  );
}
