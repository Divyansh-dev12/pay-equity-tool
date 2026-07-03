import React, { useState, useRef, useEffect } from 'react';
import { API_URL } from './format';

/**
 * Floating pay-equity assistant.
 * `buildContext()` returns the compact analysis facts + employee rows the
 * backend answers from, so the bot always reflects the CURRENT model + filters.
 *
 * "Learning": every bot reply has a Teach button. Correcting it POSTs to
 * /api/chat/teach, which persists the question→answer pair server-side
 * (taught_answers.json). Next time a similar question is asked — by anyone,
 * in any session — the taught answer wins over the generic one.
 */
export default function ChatBot({ buildContext, model }) {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState([
    { role: 'bot', text: `Hi! I'm your pay-equity assistant for the ${model} model. I can answer questions about specific employees too — e.g. "who earns the lowest in Sales?". If I get something wrong, teach me the right answer and I'll remember it.` },
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [teaching, setTeaching] = useState(null); // index of message being corrected
  const [teachText, setTeachText] = useState('');
  const [learnedCount, setLearnedCount] = useState(0);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs, open, teaching]);

  const suggestions = [
    'Who earns the lowest?',
    'Which function has the biggest gap?',
    'How much would remediation cost?',
    'What should we do next?',
  ];

  async function send(q) {
    const question = (q ?? input).trim();
    if (!question || busy) return;
    setMsgs(m => [...m, { role: 'user', text: question }]);
    setInput('');
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          context: buildContext(),
          history: msgs.slice(-10),  // send last 10 turns for follow-up resolution
        }),
      });
      const data = await res.json();
      setMsgs(m => [...m, { role: 'bot', text: data.answer, question, engine: data.engine }]);
    } catch (e) {
      setMsgs(m => [...m, { role: 'bot', text: 'Sorry — I could not reach the analysis service.' }]);
    } finally { setBusy(false); }
  }

  async function submitTeach(idx) {
    const msg = msgs[idx];
    if (!teachText.trim()) return;
    await fetch(`${API_URL}/api/chat/teach`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: msg.question, answer: teachText.trim() }),
    });
    setLearnedCount(c => c + 1);
    setMsgs(m => [...m, { role: 'bot', text: `Got it — I'll remember that next time someone asks "${msg.question}". 🧠`, engine: 'learned' }]);
    setTeaching(null); setTeachText('');
  }

  return (
    <>
      <button className={`chat-fab ${open ? 'open' : ''}`} onClick={() => setOpen(o => !o)}
        title="Ask the pay-equity assistant">
        {open ? '×' : '💬'}
      </button>

      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span>🤖 Pay-Equity Assistant {learnedCount > 0 && <span className="chat-learned-badge">+{learnedCount} taught</span>}</span>
            <button onClick={() => setOpen(false)}>×</button>
          </div>
          <div className="chat-body">
            {msgs.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>
                {m.text.split('\n').map((line, j) => <div key={j}>{renderInline(line)}</div>)}
                {m.role === 'bot' && m.question && teaching !== i && (
                  <button className="teach-btn" onClick={() => { setTeaching(i); setTeachText(''); }}>
                    ✏️ Not quite right? Teach me
                  </button>
                )}
                {m.role === 'bot' && m.engine === 'learned' && (
                  <span className="engine-tag">🧠 learned from you</span>
                )}
                {teaching === i && (
                  <div className="teach-box">
                    <textarea value={teachText} onChange={e => setTeachText(e.target.value)}
                      placeholder={`What should I say when asked "${m.question}"?`} rows={2} />
                    <div className="teach-actions">
                      <button className="teach-cancel" onClick={() => setTeaching(null)}>Cancel</button>
                      <button className="teach-save" onClick={() => submitTeach(i)}>Save answer</button>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {busy && <div className="chat-msg bot typing">…thinking</div>}
            <div ref={endRef} />
          </div>
          <div className="chat-suggest">
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => send(s)} disabled={busy}>{s}</button>
            ))}
          </div>
          <div className="chat-input">
            <input value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              placeholder="Ask a question…" disabled={busy} />
            <button onClick={() => send()} disabled={busy}>Send</button>
          </div>
        </div>
      )}
    </>
  );
}

// Minimal **bold** rendering
function renderInline(line) {
  const parts = line.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) =>
    p.startsWith('**') && p.endsWith('**')
      ? <strong key={i}>{p.slice(2, -2)}</strong>
      : <React.Fragment key={i}>{p}</React.Fragment>);
}
