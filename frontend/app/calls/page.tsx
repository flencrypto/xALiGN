'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';

interface CallRecord {
  id: number;
  company_intel_id?: number;
  title: string;
  audio_filename?: string;
  transcript?: string;
  sentiment_score?: number;
  competitor_mentions?: string;
  budget_signals?: string;
  risk_phrases?: string;
  next_steps?: string;
  crm_summary?: string;
  created_at: string;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

function SentimentBar({ score }: { score: number }) {
  const pct = Math.min((score / 10) * 100, 100);
  const color = score >= 7 ? 'bg-green-500' : score >= 4 ? 'bg-yellow-500' : 'bg-red-500';
  const label = score >= 7 ? 'Positive' : score >= 4 ? 'Neutral' : 'Negative';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">Sentiment</span>
        <span className={`font-medium ${score >= 7 ? 'text-green-400' : score >= 4 ? 'text-yellow-400' : 'text-red-400'}`}>{label} ({score.toFixed(1)})</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function parseJsonField(v?: string): string[] {
  if (!v) return [];
  try { return JSON.parse(v); } catch { return [v]; }
}

export default function CallsPage() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<CallRecord | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', company_intel_id: '' });
  const [transcript, setTranscript] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API}/calls`).then((r) => r.json()).then(setCalls).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const payload: Record<string, unknown> = { title: form.title };
      if (form.company_intel_id) payload.company_intel_id = parseInt(form.company_intel_id);
      const res = await fetch(`${API}/calls`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error(await res.text());
      const created: CallRecord = await res.json();
      setCalls((p) => [created, ...p]);
      setShowForm(false);
      setSelected(created);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleAnalyze() {
    if (!selected || !transcript.trim()) return;
    setAnalyzing(true); setError('');
    try {
      const res = await fetch(`${API}/calls/${selected.id}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript }),
      });
      if (!res.ok) {
        const body = await res.text();
        if (res.status === 503) throw new Error('Grok AI not configured. Set XAI_API_KEY on the backend.');
        throw new Error(body);
      }
      const updated: CallRecord = await res.json();
      setCalls((p) => p.map((c) => (c.id === updated.id ? updated : c)));
      setSelected(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <>
      <Header title="Call Intelligence" />
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-slate-400 text-sm">Upload transcripts and extract competitor mentions, budget signals, risk phrases and next steps</p>
          <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-medium">
            + New Call
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
            <h3 className="text-white font-semibold">New Call Record</h3>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Title *</label>
                <input required value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" placeholder="e.g. Discovery call with Acme CEO" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Company Intel ID</label>
                <input type="number" value={form.company_intel_id} onChange={(e) => setForm((p) => ({ ...p, company_intel_id: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg font-medium">{saving ? 'Creating…' : 'Create'}</button>
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg">Cancel</button>
            </div>
          </form>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Call list */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h2 className="text-white font-semibold">Calls</h2>
            </div>
            {loading ? (
              <div className="p-5 space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-12 bg-slate-700 rounded animate-pulse" />)}</div>
            ) : calls.length === 0 ? (
              <p className="p-5 text-slate-400 text-sm">No calls yet.</p>
            ) : (
              <div className="divide-y divide-slate-700">
                {calls.map((c) => (
                  <button key={c.id} onClick={() => { setSelected(c); setTranscript(c.transcript ?? ''); }} className={`w-full text-left px-5 py-4 hover:bg-slate-700/50 transition-colors ${selected?.id === c.id ? 'bg-blue-600/10 border-l-2 border-blue-500' : ''}`}>
                    <p className="text-white text-sm font-medium truncate">{c.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {c.crm_summary ? <span className="text-green-400 text-xs">✓ Analysed</span> : <span className="text-slate-500 text-xs">Pending analysis</span>}
                      {c.sentiment_score != null && <span className="text-xs text-slate-400">S:{c.sentiment_score.toFixed(1)}</span>}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Analysis panel */}
          <div className="lg:col-span-2 space-y-4">
            {!selected ? (
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
                <p className="text-slate-400 text-sm">Select a call or create a new one to analyse its transcript.</p>
              </div>
            ) : (
              <>
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
                  <h3 className="text-white font-semibold">{selected.title}</h3>
                  <div>
                    <label className="block text-slate-400 text-xs mb-1 uppercase tracking-wide">Transcript</label>
                    <textarea
                      rows={6}
                      value={transcript}
                      onChange={(e) => setTranscript(e.target.value)}
                      placeholder="Paste the call transcript here…"
                      className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono resize-y"
                    />
                  </div>
                  {error && <p className="text-red-400 text-sm">{error}</p>}
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing || !transcript.trim()}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm rounded-lg font-medium flex items-center gap-2"
                  >
                    {analyzing ? <><span className="animate-spin">◌</span> Analysing with Grok…</> : '✦ Analyse with AI'}
                  </button>
                </div>

                {selected.crm_summary && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selected.sentiment_score != null && (
                      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                        <SentimentBar score={selected.sentiment_score} />
                      </div>
                    )}
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-2">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">CRM Summary</p>
                      <p className="text-slate-300 text-sm">{selected.crm_summary}</p>
                    </div>
                    {parseJsonField(selected.competitor_mentions).length > 0 && (
                      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-2">
                        <p className="text-xs font-semibold text-red-400 uppercase tracking-wide">Competitor Mentions</p>
                        {parseJsonField(selected.competitor_mentions).map((m, i) => (
                          <p key={i} className="text-slate-300 text-sm flex gap-2"><span className="text-red-400">◈</span>{m}</p>
                        ))}
                      </div>
                    )}
                    {parseJsonField(selected.budget_signals).length > 0 && (
                      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-2">
                        <p className="text-xs font-semibold text-green-400 uppercase tracking-wide">Budget Signals</p>
                        {parseJsonField(selected.budget_signals).map((b, i) => (
                          <p key={i} className="text-slate-300 text-sm flex gap-2"><span className="text-green-400">$</span>{b}</p>
                        ))}
                      </div>
                    )}
                    {parseJsonField(selected.risk_phrases).length > 0 && (
                      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-2">
                        <p className="text-xs font-semibold text-yellow-400 uppercase tracking-wide">Risk Phrases</p>
                        {parseJsonField(selected.risk_phrases).map((r, i) => (
                          <p key={i} className="text-slate-300 text-sm flex gap-2"><span className="text-yellow-400">⚠</span>{r}</p>
                        ))}
                      </div>
                    )}
                    {selected.next_steps && (
                      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-2 md:col-span-2">
                        <p className="text-xs font-semibold text-blue-400 uppercase tracking-wide">Next Steps</p>
                        <p className="text-slate-300 text-sm">{selected.next_steps}</p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
