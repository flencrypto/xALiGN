'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';

interface SignalEvent {
  id: number;
  company_intel_id?: number;
  company_name?: string;
  signal_type: string;
  strength: number;
  decay_factor: number;
  event_date: string;
  source_url?: string;
  description?: string;
  created_at: string;
}

interface RelationshipSuggestion {
  company_name?: string;
  total_score: number;
  recommendation: string;
  context_brief: string;
  conversation_angle: string;
  risk_flags: string[];
  top_signals: SignalEvent[];
}

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
const SIGNAL_TYPES = ['expansion', 'funding', 'hiring', 'contract_win', 'conference', 'earnings', 'partnership', 'risk'];

function SignalTypeBadge({ type }: { type: string }) {
  const map: Record<string, string> = {
    expansion: 'bg-green-500/20 text-green-400',
    funding: 'bg-blue-500/20 text-blue-400',
    hiring: 'bg-purple-500/20 text-purple-400',
    contract_win: 'bg-yellow-500/20 text-yellow-400',
    conference: 'bg-cyan-500/20 text-cyan-400',
    earnings: 'bg-orange-500/20 text-orange-400',
    partnership: 'bg-pink-500/20 text-pink-400',
    risk: 'bg-red-500/20 text-red-400',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${map[type] ?? 'bg-slate-700 text-slate-300'}`}>
      {type}
    </span>
  );
}

function ScoreMeter({ score }: { score: number }) {
  const pct = Math.min((score / 10) * 100, 100);
  const color = score >= 5 ? 'bg-green-500' : score >= 2 ? 'bg-yellow-500' : 'bg-slate-500';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">Timing Score</span>
        <span className="text-white font-bold">{score.toFixed(2)}</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<SignalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [suggestion, setSuggestion] = useState<RelationshipSuggestion | null>(null);
  const [suggestLoading, setSuggestLoading] = useState(false);
  const [suggestCompanyId, setSuggestCompanyId] = useState('');
  const [form, setForm] = useState({
    company_name: '', signal_type: 'expansion', strength: '3', decay_factor: '0.1',
    event_date: new Date().toISOString().slice(0, 16), description: '', source_url: '', company_intel_id: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API}/signals`).then((r) => r.json()).then(setSignals).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const payload: Record<string, unknown> = {
        company_name: form.company_name || undefined,
        signal_type: form.signal_type,
        strength: parseFloat(form.strength),
        decay_factor: parseFloat(form.decay_factor),
        event_date: new Date(form.event_date).toISOString(),
        description: form.description || undefined,
        source_url: form.source_url || undefined,
        company_intel_id: form.company_intel_id ? parseInt(form.company_intel_id) : undefined,
      };
      const res = await fetch(`${API}/signals`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error(await res.text());
      const created: SignalEvent = await res.json();
      setSignals((p) => [created, ...p]);
      setShowForm(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  async function handleSuggest(e: React.FormEvent) {
    e.preventDefault();
    if (!suggestCompanyId) return;
    setSuggestLoading(true); setSuggestion(null); setError('');
    try {
      const res = await fetch(`${API}/signals/relationship/suggest?company_intel_id=${suggestCompanyId}`, { method: 'POST' });
      if (!res.ok) throw new Error(await res.text());
      setSuggestion(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Suggest failed');
    } finally {
      setSuggestLoading(false);
    }
  }

  return (
    <>
      <Header title="Expansion Signals" />
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-slate-400 text-sm">Signal events with exponential-decay relationship timing scoring</p>
          <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-medium">
            + Add Signal
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleSubmit} className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
            <h3 className="text-white font-semibold">New Signal Event</h3>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Company Name</label>
                <input value={form.company_name} onChange={(e) => setForm((p) => ({ ...p, company_name: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Signal Type *</label>
                <select value={form.signal_type} onChange={(e) => setForm((p) => ({ ...p, signal_type: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm">
                  {SIGNAL_TYPES.map((t) => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Event Date *</label>
                <input type="datetime-local" required value={form.event_date} onChange={(e) => setForm((p) => ({ ...p, event_date: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Strength (0–10)</label>
                <input type="number" min="0" max="10" step="0.5" value={form.strength} onChange={(e) => setForm((p) => ({ ...p, strength: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Decay Factor λ (0–1)</label>
                <input type="number" min="0" max="1" step="0.01" value={form.decay_factor} onChange={(e) => setForm((p) => ({ ...p, decay_factor: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Company Intel ID</label>
                <input type="number" value={form.company_intel_id} onChange={(e) => setForm((p) => ({ ...p, company_intel_id: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-slate-400 text-xs mb-1">Description</label>
                <input value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Source URL</label>
                <input type="url" value={form.source_url} onChange={(e) => setForm((p) => ({ ...p, source_url: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg font-medium">{saving ? 'Saving…' : 'Save Signal'}</button>
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg">Cancel</button>
            </div>
          </form>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Signals list */}
          <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h2 className="text-white font-semibold">Signal Feed</h2>
            </div>
            {loading ? (
              <div className="p-5 space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-14 bg-slate-700 rounded animate-pulse" />)}</div>
            ) : signals.length === 0 ? (
              <p className="p-5 text-slate-400 text-sm">No signals yet. Add your first expansion signal above.</p>
            ) : (
              <div className="divide-y divide-slate-700">
                {signals.map((s) => (
                  <div key={s.id} className="px-5 py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 space-y-1">
                        <div className="flex items-center gap-2">
                          <SignalTypeBadge type={s.signal_type} />
                          {s.company_name && <span className="text-white text-sm font-medium">{s.company_name}</span>}
                        </div>
                        {s.description && <p className="text-slate-400 text-xs">{s.description}</p>}
                        <p className="text-slate-500 text-xs">{new Date(s.event_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                      </div>
                      <div className="text-right flex-shrink-0 space-y-1">
                        <p className="text-white text-sm font-bold">×{s.strength}</p>
                        <p className="text-slate-500 text-xs">λ={s.decay_factor}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Relationship timing panel */}
          <div className="space-y-4">
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
              <h3 className="text-white font-semibold">Relationship Timing Engine</h3>
              <p className="text-slate-400 text-xs">Enter a Company Intel ID to run the decay-based outreach recommendation.</p>
              {error && <p className="text-red-400 text-xs">{error}</p>}
              <form onSubmit={handleSuggest} className="flex gap-2">
                <input
                  type="number"
                  placeholder="Company Intel ID"
                  value={suggestCompanyId}
                  onChange={(e) => setSuggestCompanyId(e.target.value)}
                  className="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
                <button type="submit" disabled={suggestLoading} className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg">
                  {suggestLoading ? '…' : 'Score'}
                </button>
              </form>

              {suggestion && (
                <div className="space-y-3">
                  <ScoreMeter score={suggestion.total_score} />
                  <div className="bg-slate-900 rounded-lg p-3 space-y-2">
                    <p className="text-xs font-semibold text-blue-400 uppercase tracking-wide">Recommendation</p>
                    <p className="text-white text-sm">{suggestion.recommendation}</p>
                  </div>
                  <div className="bg-slate-900 rounded-lg p-3 space-y-2">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Conversation Angle</p>
                    <p className="text-slate-300 text-sm">{suggestion.conversation_angle}</p>
                  </div>
                  <div className="bg-slate-900 rounded-lg p-3">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Context Brief</p>
                    <p className="text-slate-300 text-xs">{suggestion.context_brief}</p>
                  </div>
                  {suggestion.risk_flags.length > 0 && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                      <p className="text-xs font-semibold text-red-400 uppercase tracking-wide mb-1">Risk Flags</p>
                      {suggestion.risk_flags.map((f, i) => <p key={i} className="text-red-300 text-xs">⚠ {f}</p>)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
