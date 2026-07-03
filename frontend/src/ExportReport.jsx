import React, { useState } from 'react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import PptxGenJS from 'pptxgenjs';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const RGB = {
  brand: [76, 110, 245], brandDark: [59, 91, 219],
  red: [224, 49, 49], green: [47, 158, 68], orange: [240, 140, 0],
  ink: [26, 31, 54], muted: [107, 114, 128],
  light: [248, 249, 255], border: [229, 231, 235], white: [255, 255, 255],
};
const HEX = {
  brand: '4C6EF5', brandDark: '3B5BDB',
  red: 'E03131', green: '2F9E44', orange: 'F08C00',
  ink: '1A1F36', muted: '6B7280',
  light: 'F8F9FF', border: 'E5E7EB', white: 'FFFFFF', bg: 'F4F6FB',
};

const toneHex = { critical: HEX.red, warning: HEX.orange, good: HEX.green, info: HEX.brand };
const toneBg  = { critical: 'FFF5F5', warning: 'FFF9DB', good: 'EBFBEE', info: 'F8F9FF' };
const toneRGB = { critical: RGB.red, warning: RGB.orange, good: RGB.green, info: RGB.brand };

const sevHex = { high: HEX.red, medium: HEX.orange, low: HEX.green };
const sevBg  = { high: 'FFF5F5', medium: 'FFF9DB', low: 'EBFBEE' };

function today() {
  return new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
}

// Capture each .analytics-card as a PNG data URL
async function captureCharts() {
  const panel = document.querySelector('.analytics-panel');
  if (!panel) return [];
  const cards = panel.querySelectorAll('.analytics-card');
  const out = [];
  for (const card of cards) {
    try {
      const canvas = await html2canvas(card, {
        scale: 2, backgroundColor: '#fafbff',
        useCORS: true, allowTaint: true, logging: false, imageTimeout: 0,
      });
      out.push(canvas.toDataURL('image/png'));
    } catch { /* skip failed captures silently */ }
  }
  return out;
}

// ─── PDF Builder ─────────────────────────────────────────────────────────────

async function buildPDF(rd, imgs) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const W = 210, M = 14;
  let y = 0;

  const sc = (rgb) => doc.setTextColor(...rgb);
  const sf = (rgb) => doc.setFillColor(...rgb);
  const sd = (rgb) => doc.setDrawColor(...rgb);
  const clamp = (v) => Math.min(255, Math.max(0, Math.round(v)));
  const lighten = ([r, g, b], f = 0.88) => [clamp(r + (255 - r) * f), clamp(g + (255 - g) * f), clamp(b + (255 - b) * f)];

  const newPage = () => { doc.addPage(); y = 18; };

  // ── Page 1: Header + KPIs ──────────────────────────────────────────────────
  sf(RGB.brand); doc.rect(0, 0, W, 40, 'F');
  sf(RGB.brandDark); doc.rect(0, 36, W, 4, 'F');

  doc.setFont('helvetica', 'bold'); doc.setFontSize(22); sc(RGB.white);
  doc.text('Pay Equity Studio', M, 16);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10);
  doc.text(rd.model === 'regression' ? 'Regression Model' : 'Linear (Median) Model', M, 26);
  doc.text(today(), W - M, 26, { align: 'right' });

  y = 50;
  if (rd.hasFilter) {
    sf([231, 245, 255]); sd([165, 216, 255]);
    doc.roundedRect(M, y - 5, W - M * 2, 10, 2, 2, 'FD');
    doc.setFontSize(9); sc([25, 113, 194]);
    doc.text(`Filter active: ${rd.filterLabel}`, M + 4, y + 1.5);
    y += 14;
  }

  doc.setFont('helvetica', 'bold'); doc.setFontSize(12); sc(RGB.ink);
  doc.text('Key Metrics', M, y); y += 8;

  const kpiW = (W - M * 2 - 6) / 2;
  rd.kpis.forEach((k, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * (kpiW + 6), ky = y + row * 21;
    sf(k.isNegative ? [255, 248, 248] : k.isPositive ? [240, 253, 244] : RGB.light);
    sd(k.isNegative ? [255, 201, 201] : k.isPositive ? [178, 242, 187] : RGB.border);
    doc.roundedRect(x, ky, kpiW, 17, 2, 2, 'FD');
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8); sc(RGB.muted);
    doc.text(k.label, x + 4, ky + 6);
    doc.setFont('helvetica', 'bold'); doc.setFontSize(13);
    sc(k.isNegative ? RGB.red : k.isPositive ? RGB.green : RGB.ink);
    doc.text(k.value, x + 4, ky + 13);
  });
  y += Math.ceil(rd.kpis.length / 2) * 21 + 8;

  // ── AI Insights ───────────────────────────────────────────────────────────
  if (y > 220) newPage(); else y += 4;
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12); sc(RGB.ink);
  doc.text('AI Insights', M, y); y += 7;

  for (const ins of (rd.insights || [])) {
    const rgb = toneRGB[ins.tone] || RGB.brand;
    const bodyLines = doc.splitTextToSize(ins.text, W - M * 2 - 12);
    const boxH = 7 + 5 + bodyLines.length * 4.5 + 4;
    if (y + boxH > 278) newPage();
    sf(lighten(rgb)); sd(rgb);
    doc.roundedRect(M, y, W - M * 2, boxH, 2, 2, 'FD');
    sf(rgb); doc.rect(M, y, 3, boxH, 'F');
    doc.setFont('helvetica', 'bold'); doc.setFontSize(9); sc(rgb);
    doc.text(ins.title, M + 7, y + 6);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8); sc(RGB.ink);
    doc.text(bodyLines, M + 7, y + 12);
    y += boxH + 4;
  }

  // ── Charts ─────────────────────────────────────────────────────────────────
  if (imgs.length) {
    newPage();
    doc.setFont('helvetica', 'bold'); doc.setFontSize(12); sc(RGB.ink);
    doc.text('Analytics Charts' + (rd.hasFilter ? ` — ${rd.filterLabel}` : ''), M, y); y += 8;
    const iW = (W - M * 2 - 6) / 2;
    const iH = iW * 0.72;
    imgs.forEach((src, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = M + col * (iW + 6), cy = y + row * (iH + 4);
      if (cy + iH > 284) { newPage(); }
      try { doc.addImage(src, 'PNG', x, cy, iW, iH); } catch { /* skip */ }
    });
  }

  // ── Recommendations ────────────────────────────────────────────────────────
  if (rd.recommendations) {
    newPage();
    doc.setFont('helvetica', 'bold'); doc.setFontSize(12); sc(RGB.ink);
    doc.text('Recommended Actions', M, y); y += 8;
    const sev = (rd.recommendations.severity || 'low').toLowerCase();
    const sevRGB = { high: RGB.red, medium: RGB.orange, low: RGB.green }[sev] || RGB.brand;
    sf(lighten(sevRGB)); sd(sevRGB);
    doc.roundedRect(M, y, W - M * 2, 18, 2, 2, 'FD');
    doc.setFont('helvetica', 'bold'); doc.setFontSize(9); sc(sevRGB);
    doc.text(`Severity: ${rd.recommendations.severity}  ·  ${rd.recommendations.pattern}`, M + 4, y + 7);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8); sc(RGB.ink);
    const msgLines = doc.splitTextToSize(rd.recommendations.message || '', W - M * 2 - 8);
    doc.text(msgLines, M + 4, y + 13);
    y += 22;

    (rd.recommendations.actions || []).forEach((action, i) => {
      const lines = doc.splitTextToSize(`${i + 1}.  ${action}`, W - M * 2 - 8);
      const bH = lines.length * 4.5 + 5;
      if (y + bH > 276) newPage();
      sf(i % 2 === 0 ? RGB.light : RGB.white); sd(RGB.border);
      doc.roundedRect(M, y, W - M * 2, bH, 1.5, 1.5, 'FD');
      doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); sc(RGB.ink);
      doc.text(lines, M + 5, y + 5);
      y += bH + 3;
    });
  }

  // Footer on every page
  const total = doc.getNumberOfPages();
  for (let p = 1; p <= total; p++) {
    doc.setPage(p);
    sf(RGB.brand); doc.rect(0, 290, W, 7, 'F');
    doc.setFont('helvetica', 'normal'); doc.setFontSize(7); sc(RGB.white);
    doc.text('Pay Equity Studio · Confidential', M, 295);
    doc.text(`Page ${p} of ${total}`, W - M, 295, { align: 'right' });
  }

  doc.save(`pay-equity-${rd.model}-${rd.hasFilter ? rd.filterLabel.replace(/[^\w]/g, '_').slice(0, 20) : 'all'}.pdf`);
}

// ─── PPT Builder ─────────────────────────────────────────────────────────────

async function buildPPT(rd, imgs) {
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_16x9';
  const W = 10, H = 7.5;
  const modelLabel = rd.model === 'regression' ? 'Regression Model' : 'Linear (Median) Model';

  const hdr = (slide, title, sub) => {
    slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: 0.62, fill: { color: HEX.brand } });
    slide.addText(title, { x: 0.3, y: 0.1, w: 8, h: 0.42, fontSize: 14, bold: true, color: HEX.white, fontFace: 'Calibri' });
    if (sub) slide.addText(sub, { x: 0.3, y: 0.1, w: 9.5, h: 0.42, fontSize: 10, color: 'C5CFF9', align: 'right', fontFace: 'Calibri' });
    slide.addShape(pptx.ShapeType.rect, { x: 0, y: H - 0.3, w: W, h: 0.3, fill: { color: HEX.brandDark } });
    slide.addText('Pay Equity Studio · Confidential', { x: 0, y: H - 0.28, w: W, h: 0.25, fontSize: 7, color: 'A5B4FC', align: 'center', fontFace: 'Calibri' });
  };

  // Slide 1 — Title
  const s1 = pptx.addSlide();
  s1.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: HEX.brand } });
  s1.addShape(pptx.ShapeType.rect, { x: 0, y: H * 0.68, w: W, h: H * 0.32, fill: { color: HEX.brandDark } });
  s1.addText('Pay Equity Studio', { x: 0.6, y: 1.2, w: 8.8, h: 1.4, fontSize: 44, bold: true, color: HEX.white, fontFace: 'Calibri' });
  s1.addText(modelLabel, { x: 0.6, y: 2.8, w: 8.8, h: 0.7, fontSize: 22, color: 'C5CFF9', fontFace: 'Calibri' });
  s1.addText(today(), { x: 0.6, y: 3.6, w: 8.8, h: 0.45, fontSize: 13, color: 'A5B4FC', fontFace: 'Calibri' });
  if (rd.hasFilter) {
    s1.addShape(pptx.ShapeType.rect, { x: 0.6, y: 4.5, w: 8.8, h: 0.55, fill: { color: '3B5BDB' }, line: { color: '818CF8', pt: 1 } });
    s1.addText(`Filter: ${rd.filterLabel}`, { x: 0.8, y: 4.55, w: 8.5, h: 0.45, fontSize: 12, color: HEX.white, fontFace: 'Calibri' });
  }

  // Slide 2 — KPIs
  const s2 = pptx.addSlide();
  hdr(s2, 'Key Metrics', rd.hasFilter ? `Filter: ${rd.filterLabel}` : null);
  const cols = 3, kW = 2.9, kH = 1.5, gX = 0.2, gY = 0.2;
  const startX = (W - cols * kW - (cols - 1) * gX) / 2, startY = 0.85;
  rd.kpis.forEach((k, i) => {
    const c = i % cols, r = Math.floor(i / cols);
    const x = startX + c * (kW + gX), ky = startY + r * (kH + gY);
    const bg = k.isNegative ? 'FFF8F8' : k.isPositive ? 'F0FDF4' : HEX.light;
    const ln = k.isNegative ? 'FFC9C9' : k.isPositive ? 'B2F2BB' : HEX.border;
    const vc = k.isNegative ? HEX.red : k.isPositive ? HEX.green : HEX.ink;
    s2.addShape(pptx.ShapeType.rect, { x, y: ky, w: kW, h: kH, fill: { color: bg }, line: { color: ln, pt: 1 } });
    s2.addText(k.label, { x: x + 0.12, y: ky + 0.15, w: kW - 0.24, h: 0.35, fontSize: 9.5, color: HEX.muted, fontFace: 'Calibri' });
    s2.addText(k.value, { x: x + 0.12, y: ky + 0.58, w: kW - 0.24, h: 0.75, fontSize: 26, bold: true, color: vc, fontFace: 'Calibri' });
  });

  // Slide 3 — AI Insights
  if (rd.insights?.length) {
    const s3 = pptx.addSlide();
    hdr(s3, 'AI Insights', rd.hasFilter ? `Filter: ${rd.filterLabel}` : null);
    const perSlide = Math.min(rd.insights.length, 5);
    const rowH = (H - 1.1) / perSlide - 0.1;
    rd.insights.slice(0, 5).forEach((ins, i) => {
      const iy = 0.75 + i * (rowH + 0.08);
      const th = toneHex[ins.tone] || HEX.brand;
      const tb = toneBg[ins.tone] || HEX.light;
      s3.addShape(pptx.ShapeType.rect, { x: 0.25, y: iy, w: 0.07, h: rowH, fill: { color: th } });
      s3.addShape(pptx.ShapeType.rect, { x: 0.32, y: iy, w: 9.4, h: rowH, fill: { color: tb }, line: { color: HEX.border, pt: 0.5 } });
      s3.addText(ins.title, { x: 0.5, y: iy + 0.06, w: 9.1, h: 0.3, fontSize: 10.5, bold: true, color: th, fontFace: 'Calibri' });
      s3.addText(ins.text, { x: 0.5, y: iy + 0.38, w: 9.1, h: rowH - 0.44, fontSize: 9, color: '374151', wrap: true, fontFace: 'Calibri' });
    });
  }

  // Slides 4+ — Charts (2 per slide)
  if (imgs.length) {
    for (let i = 0; i < imgs.length; i += 2) {
      const sc = pptx.addSlide();
      hdr(sc, 'Analytics Charts', rd.hasFilter ? `Filter: ${rd.filterLabel}` : null);
      const cW = 4.55, cH = 3.2;
      [0, 1].forEach(j => {
        const img = imgs[i + j];
        if (!img) return;
        const cx = j === 0 ? 0.18 : 5.07;
        sc.addShape(pptx.ShapeType.rect, { x: cx, y: 0.75, w: cW, h: cH, fill: { color: 'FAFBFF' }, line: { color: HEX.border, pt: 1 } });
        sc.addImage({ data: img, x: cx, y: 0.75, w: cW, h: cH });
      });
    }
  }

  // Slide — Recommendations
  if (rd.recommendations) {
    const sr = pptx.addSlide();
    hdr(sr, 'Recommended Actions', rd.hasFilter ? `Filter: ${rd.filterLabel}` : null);
    const sev = (rd.recommendations.severity || 'low').toLowerCase();
    const sh = sevHex[sev] || HEX.brand, sb = sevBg[sev] || HEX.light;
    sr.addShape(pptx.ShapeType.rect, { x: 0.25, y: 0.72, w: 9.5, h: 0.75, fill: { color: sb }, line: { color: sh, pt: 1 } });
    sr.addText(`Severity: ${rd.recommendations.severity}  ·  ${rd.recommendations.pattern}`, { x: 0.4, y: 0.76, w: 9.2, h: 0.32, fontSize: 11, bold: true, color: sh, fontFace: 'Calibri' });
    sr.addText(rd.recommendations.message || '', { x: 0.4, y: 1.06, w: 9.2, h: 0.35, fontSize: 9, color: '374151', fontFace: 'Calibri' });

    const actions = rd.recommendations.actions || [];
    const aH = Math.min((H - 1.7) / Math.max(actions.length, 1) - 0.06, 0.88);
    actions.forEach((a, i) => {
      const ay = 1.62 + i * (aH + 0.06);
      sr.addShape(pptx.ShapeType.rect, { x: 0.25, y: ay, w: 9.5, h: aH, fill: { color: i % 2 === 0 ? 'F8F9FB' : HEX.white }, line: { color: HEX.border, pt: 0.5 } });
      sr.addText(`${i + 1}.  ${a}`, { x: 0.4, y: ay + 0.06, w: 9.2, h: aH - 0.12, fontSize: 9.5, color: HEX.ink, wrap: true, fontFace: 'Calibri' });
    });
  }

  const fname = `pay-equity-${rd.model}-${rd.hasFilter ? rd.filterLabel.replace(/[^\w]/g, '_').slice(0, 20) : 'all'}.pptx`;
  await pptx.writeFile({ fileName: fname });
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function ExportReport({ reportData }) {
  const [state, setState] = useState('idle'); // idle | pdf | ppt

  async function run(type) {
    setState(type);
    try {
      const imgs = await captureCharts();
      if (type === 'pdf') await buildPDF(reportData, imgs);
      else await buildPPT(reportData, imgs);
    } catch (e) {
      console.error('Export error:', e);
      alert(`Export failed: ${e.message}`);
    } finally {
      setState('idle');
    }
  }

  const busy = state !== 'idle';
  const label = reportData.hasFilter ? `Exporting: ${reportData.filterLabel}` : 'Exporting all employees';

  return (
    <div className="export-bar">
      <span className="export-label">📥 Export current view</span>
      <span className="export-scope">{label}</span>
      <div className="export-btns">
        <button className="btn btn-export" onClick={() => run('pdf')} disabled={busy}>
          {state === 'pdf' ? '⏳ Generating PDF…' : '📄 Download PDF'}
        </button>
        <button className="btn btn-export-ppt" onClick={() => run('ppt')} disabled={busy}>
          {state === 'ppt' ? '⏳ Generating PPT…' : '📊 Download PPT'}
        </button>
      </div>
    </div>
  );
}
