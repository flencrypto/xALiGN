'use client';

import { useEffect, useState } from 'react';
import { callsApi, CallIntelligence } from '@/lib/api';

export default function CallsPage() {
  const [calls, setCalls] = useState<CallIntelligence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CallIntelligence | null>(null);
  const [filterCompany, setFilterCompany] = useState('');
  const [showAnalyseModal, setShowAnalyseModal] = useState(false);
  const [analysing, setAnalysing] = useState(false);

  const [form, setForm] = useState({
    company_name: '',
    executive_name: '',
    transcript: '',
  });

  const fetchCalls = async (company?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await callsApi.list(company || undefined);
      setCalls(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load calls');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, []);

  const handleFilter = () => fetchCalls(filterCompany || undefined);

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this call record?')) return;
    try {
      await callsApi.delete(id);
      if (selected?.id === id) setSelected(null);
      fetchCalls(filterCompany || undefined);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Delete failed');
    }
  };

  const handleAnalyse = async () => {
    if (!form.transcript) return;
    setAnalysing(true);
    try {
      const result = await callsApi.analyse({
        company_name: form.company_name || undefined,
        executive_name: form.executive_name || undefined,
        transcript: form.transcript,
      });
      setSelected(result);
      setShowAnalyseModal(false);
      setForm({ company_name: '', executive_name: '', transcript: '' });
      fetchCalls(filterCompany || undefined);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Analysis failed');
    } finally {
      setAnalysing(false);
    }
  };

  const sentimentLabel = (score?: number | null) => {
    if (score == null) return { text: '—', color: 'text-slate-400' };
    if (score >= 0.5) return { text: 'Positive', color: 'text-emerald-400' };
    if (score >= 0) return { text: 'Neutral', color: 'text-blue-400' };
    if (score >= -0.5) return { text: 'Cautious', color: 'text-amber-400' };
    return { text: 'Negative', color: 'text-red-400' };
  };

  const TagList = ({ items, color }: { items?: string[] | null; color: string }) => {
    if (!items || items.length === 0) return <span className="text-slate-500 text-xs">None detected</span>;
    return (
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className={`text-xs px-2 py-1 rounded ${color}`}>
            {item}
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 text-white">
      {/* Header */}
      <div className="border-b border-slate-700 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Call Intelligence</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Transcribe and analyse calls to extract budget signals, competitor mentions, and next steps.
          </p>
        </div>
        <button
          onClick={() => setShowAnalyseModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded"
        >
          + Analyse Call
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel */}
        <div className="w-72 border-r border-slate-700 flex flex-col">
          <div className="p-4 border-b border-slate-700">
            <div className="flex gap-2">
              <input
                className="flex-1 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm placeholder-slate-500"
                placeholder="Filter by company…"
                value={filterCompany}
                onChange={(e) => setFilterCompany(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleFilter()}
              />
              <button
                onClick={handleFilter}
                className="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded text-sm"
              >
                Go
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <p className="p-4 text-slate-400 text-sm">Loading…</p>
            ) : error ? (
              <p className="p-4 text-red-400 text-sm">{error}</p>
            ) : calls.length === 0 ? (
              <p className="p-4 text-slate-500 text-sm">No call records yet.</p>
            ) : (
              calls.map((call) => {
                const sentiment = sentimentLabel(call.sentiment_score);
                return (
                  <button
                    key={call.id}
                    onClick={() => setSelected(call)}
                    className={`w-full text-left px-4 py-3 border-b border-slate-700/50 hover:bg-slate-800 transition-colors ${
                      selected?.id === call.id ? 'bg-blue-600/20 border-r-2 border-r-blue-500' : ''
                    }`}
                  >
                    <p className="text-sm font-medium text-white truncate">
                      {call.company_name ?? 'Unknown Company'}
                    </p>
                    {call.executive_name && (
                      <p className="text-xs text-slate-400 truncate">{call.executive_name}</p>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs font-medium ${sentiment.color}`}>{sentiment.text}</span>
                      <span className="text-xs text-slate-500">
                        {call.created_at ? new Date(call.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="flex-1 overflow-y-auto p-6">
          {selected ? (
            <div className="space-y-5 max-w-2xl">
              {/* Header */}
              <div className="bg-slate-800 rounded-lg p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold">{selected.company_name ?? 'Unknown Company'}</h2>
                    {selected.executive_name && (
                      <p className="text-slate-400 text-sm">{selected.executive_name}</p>
                    )}
                    <p className="text-xs text-slate-500 mt-1">
                      {selected.created_at ? new Date(selected.created_at).toLocaleString() : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {selected.sentiment_score != null && (
                      <div className="text-center">
                        <div
                          className={`text-lg font-bold ${sentimentLabel(selected.sentiment_score).color}`}
                        >
                          {selected.sentiment_score > 0 ? '+' : ''}
                          {selected.sentiment_score.toFixed(2)}
                        </div>
                        <div className="text-xs text-slate-500">Sentiment</div>
                      </div>
                    )}
                    <button
                      onClick={() => handleDelete(selected.id)}
                      className="text-red-400 hover:text-red-300 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>

              {/* Signals Grid */}
              <div className="grid grid-cols-1 gap-4">
                {[
                  {
                    label: 'Budget Signals',
                    items: selected.budget_signals,
                    color: 'bg-emerald-600/20 text-emerald-300',
                  },
                  {
                    label: 'Competitor Mentions',
                    items: selected.competitor_mentions,
                    color: 'bg-red-600/20 text-red-300',
                  },
                  {
                    label: 'Timeline Mentions',
                    items: selected.timeline_mentions,
                    color: 'bg-blue-600/20 text-blue-300',
                  },
                  {
                    label: 'Risk Language',
                    items: selected.risk_language,
                    color: 'bg-amber-600/20 text-amber-300',
                  },
                  {
                    label: 'Objection Categories',
                    items: selected.objection_categories,
                    color: 'bg-purple-600/20 text-purple-300',
                  },
                ].map(({ label, items, color }) => (
                  <div key={label} className="bg-slate-800 rounded-lg p-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">{label}</p>
                    <TagList items={items} color={color} />
                  </div>
                ))}
              </div>

              {/* Next Steps */}
              {selected.next_steps && (
                <div className="bg-slate-800 rounded-lg p-4">
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Next Steps</p>
                  <p className="text-sm text-slate-200">{selected.next_steps}</p>
                </div>
              )}

              {/* Transcript */}
              {selected.transcript && (
                <div className="bg-slate-800 rounded-lg p-4">
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Transcript</p>
                  <pre className="text-xs text-slate-400 whitespace-pre-wrap font-mono max-h-60 overflow-y-auto">
                    {selected.transcript}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-5 text-center text-slate-500 text-sm max-w-md mx-auto mt-8">
              Select a call record to view intelligence, or click &ldquo;Analyse Call&rdquo; to submit a
              transcript.
            </div>
          )}
        </div>
      </div>

      {/* Analyse Modal */}
      {showAnalyseModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold mb-4">Analyse Call Transcript</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Company Name</label>
                <input
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
                  value={form.company_name}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                  placeholder="e.g. Acme Data Centres"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Executive Name</label>
                <input
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
                  value={form.executive_name}
                  onChange={(e) => setForm({ ...form, executive_name: e.target.value })}
                  placeholder="e.g. Jane Smith, CTO"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">
                  Transcript *{' '}
                  <span className="text-slate-500">(paste call transcript text)</span>
                </label>
                <textarea
                  rows={10}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm font-mono"
                  value={form.transcript}
                  onChange={(e) => setForm({ ...form, transcript: e.target.value })}
                  placeholder="Paste transcript here…"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setShowAnalyseModal(false)}
                className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleAnalyse}
                disabled={analysing || !form.transcript}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 py-2 rounded text-sm font-medium"
              >
                {analysing ? 'Analysing…' : 'Analyse & Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
