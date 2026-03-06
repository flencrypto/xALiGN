'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { callsApi, CallIntelligence, KeyPoint, KeyPointSuggestResult } from '@/lib/api';
import IntegrationGate from '@/components/IntegrationGate';
import { useSetupStatus } from '@/lib/useSetupStatus';

export default function CallsPage() {
  const { isConfigured } = useSetupStatus();
  const grokConfigured = isConfigured('grok_ai');
  const [calls, setCalls] = useState<CallIntelligence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CallIntelligence | null>(null);
  const [filterCompany, setFilterCompany] = useState('');
  const [showAnalyseModal, setShowAnalyseModal] = useState(false);
  const [analysing, setAnalysing] = useState(false);

  // Per-key-point suggestions panel state
  const [suggestLoading, setSuggestLoading] = useState<number | null>(null);
  const [suggestions, setSuggestions] = useState<Record<number, KeyPointSuggestResult | null>>({});
  const [linking, setLinking] = useState<number | null>(null);

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

  useEffect(() => { fetchCalls(); }, []);

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

  /** Toggle the suggestions panel for a key point: fetch on first open, dismiss on second click. */
  const handleOpenSuggest = async (pointIndex: number) => {
    if (suggestions[pointIndex] !== undefined) {
      setSuggestions((prev) => { const next = { ...prev }; delete next[pointIndex]; return next; });
      return;
    }
    if (!selected) return;
    setSuggestLoading(pointIndex);
    try {
      const result = await callsApi.suggestKeyPointLinks(selected.id, pointIndex);
      setSuggestions((prev) => ({ ...prev, [pointIndex]: result }));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Suggest failed');
    } finally {
      setSuggestLoading(null);
    }
  };

  /** Link a key point to an existing opportunity or auto-create one. */
  const handleLink = async (pointIndex: number, opportunityId?: number) => {
    if (!selected) return;
    setLinking(pointIndex);
    try {
      const updated = await callsApi.linkKeyPoint(selected.id, pointIndex, opportunityId);
      setSelected(updated);
      setSuggestions((prev) => { const next = { ...prev }; delete next[pointIndex]; return next; });
      fetchCalls(filterCompany || undefined);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Link failed');
    } finally {
      setLinking(null);
    }
  };

  const sentimentLabel = (score?: number | null) => {
    if (score == null) return { text: '—', color: 'text-text-muted' };
    if (score >= 0.5) return { text: 'Positive', color: 'text-emerald-400' };
    if (score >= 0) return { text: 'Neutral', color: 'text-primary' };
    if (score >= -0.5) return { text: 'Cautious', color: 'text-amber-400' };
    return { text: 'Negative', color: 'text-danger' };
  };

  const keyPointTypeLabel = (type: KeyPoint['type']) => {
    switch (type) {
      case 'job_discussion': return { text: 'Job Discussion', color: 'bg-primary/20 text-primary' };
      case 'competitor_mention': return { text: 'Competitor', color: 'bg-red-600/20 text-danger' };
      case 'company_mention': return { text: 'Company', color: 'bg-amber-600/20 text-amber-300' };
      default: return { text: 'General', color: 'bg-surface/30 text-text-main' };
    }
  };

  const confidenceBadge = (pct: number) => {
    if (pct >= 70) return 'bg-emerald-600/25 text-emerald-300';
    if (pct >= 40) return 'bg-amber-600/25 text-amber-300';
    return 'bg-surface/30 text-text-muted';
  };

  const TagList = ({ items, color }: { items?: string[] | null; color: string }) => {
    if (!items || items.length === 0)
      return <span className="text-text-faint text-xs">None detected</span>;
    return (
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className={`text-xs px-2 py-1 rounded ${color}`}>{item}</span>
        ))}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-background text-text-main">
      <Header
        title="Call Intelligence"
        action={
          <IntegrationGate feature="grok_ai" isConfigured={grokConfigured}>
            <button
              onClick={() => setShowAnalyseModal(true)}
              className="bg-primary hover:bg-primary-dark text-text-main text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              + Analyse Call
            </button>
          </IntegrationGate>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel – call list */}
        <div className="w-72 border-r border-border-subtle flex flex-col">
          <div className="p-4 border-b border-border-subtle">
            <div className="flex gap-2">
              <input
                className="flex-1 bg-surface border border-border-subtle rounded px-3 py-2 text-sm placeholder-slate-500"
                placeholder="Filter by company…"
                value={filterCompany}
                onChange={(e) => setFilterCompany(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleFilter()}
              />
              <button onClick={handleFilter} className="bg-background hover:bg-surface px-3 py-2 rounded text-sm">
                Go
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <p className="p-4 text-text-muted text-sm">Loading…</p>
            ) : error ? (
              <p className="p-4 text-danger text-sm">{error}</p>
            ) : calls.length === 0 ? (
              <p className="p-4 text-text-faint text-sm">No call records yet.</p>
            ) : (
              calls.map((call) => {
                const sentiment = sentimentLabel(call.sentiment_score);
                return (
                  <button
                    key={call.id}
                    onClick={() => { setSelected(call); setSuggestions({}); }}
                    className={`w-full text-left px-4 py-3 border-b border-border-subtle/50 hover:bg-surface transition-colors ${selected?.id === call.id ? 'bg-primary/20 border-r-2 border-r-blue-500' : ''}`}
                  >
                    <p className="text-sm font-medium text-text-main truncate">{call.company_name ?? 'Unknown Company'}</p>
                    {call.executive_name && <p className="text-xs text-text-muted truncate">{call.executive_name}</p>}
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span className={`text-xs font-medium ${sentiment.color}`}>{sentiment.text}</span>
                      <span className="text-xs text-text-faint">
                        {call.created_at ? new Date(call.created_at).toLocaleDateString() : ''}
                      </span>
                      {call.key_points && call.key_points.length > 0 && (
                        <span className="text-xs bg-purple-600/30 text-purple-300 px-1.5 py-0.5 rounded">
                          {call.key_points.length} KP
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Panel – detail */}
        <div className="flex-1 overflow-y-auto p-6">
          {selected ? (
            <div className="space-y-5 max-w-2xl">

              {/* Call header */}
              <div className="bg-surface rounded-lg p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold">{selected.company_name ?? 'Unknown Company'}</h2>
                    {selected.executive_name && <p className="text-text-muted text-sm">{selected.executive_name}</p>}
                    <p className="text-xs text-text-faint mt-1">
                      {selected.created_at ? new Date(selected.created_at).toLocaleString() : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {selected.sentiment_score != null && (
                      <div className="text-center">
                        <div className={`text-lg font-bold ${sentimentLabel(selected.sentiment_score).color}`}>
                          {selected.sentiment_score > 0 ? '+' : ''}{selected.sentiment_score.toFixed(2)}
                        </div>
                        <div className="text-xs text-text-faint">Sentiment</div>
                      </div>
                    )}
                    <button onClick={() => handleDelete(selected.id)} className="text-danger hover:text-danger text-sm">
                      Delete
                    </button>
                  </div>
                </div>
              </div>

              {/* ── Key Points ─────────────────────────────────────── */}
              {selected.key_points && selected.key_points.length > 0 && (
                <div className="bg-surface rounded-lg p-4">
                  <p className="text-xs text-text-faint uppercase tracking-wide mb-3">
                    Key Points — Jobs, Companies &amp; Competitor Discussions
                  </p>
                  <div className="space-y-3">
                    {selected.key_points.map((kp, i) => {
                      const typeInfo = keyPointTypeLabel(kp.type);
                      const isLinked = !!kp.linked_opportunity_id;
                      const panelOpen = suggestions[i] !== undefined;

                      return (
                        <div key={i} className="border border-border-subtle rounded-lg overflow-hidden">
                          {/* Key point row */}
                          <div className="p-3 space-y-1.5">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`text-xs px-2 py-0.5 rounded ${typeInfo.color}`}>{typeInfo.text}</span>
                              {kp.mentioned_company && <span className="text-xs text-text-muted">🏢 {kp.mentioned_company}</span>}
                              {kp.mentioned_job_title && <span className="text-xs text-text-muted">💼 {kp.mentioned_job_title}</span>}
                            </div>
                            <p className="text-sm text-text-main">{kp.text}</p>
                            {kp.context && kp.context !== kp.text && (
                              <p className="text-xs text-text-muted italic">{kp.context}</p>
                            )}

                            {isLinked ? (
                              /* Audit trail */
                              <div className="mt-2 text-xs space-y-0.5">
                                <div className="flex items-center gap-2">
                                  <span className="text-emerald-400 font-medium">
                                    ✓ Linked to Opportunity #{kp.linked_opportunity_id}
                                  </span>
                                  {kp.action && (
                                    <span className="text-text-faint">
                                      ({kp.action === 'created_new' ? 'new record' : 'existing'})
                                    </span>
                                  )}
                                </div>
                                {kp.linked_by && (
                                  <p className="text-text-faint">
                                    Mentioned by {kp.linked_by}
                                    {kp.linked_at ? ` · ${new Date(kp.linked_at).toLocaleString()}` : ''}
                                  </p>
                                )}
                                {kp.what_was_said && (
                                  <p className="text-text-muted italic">&ldquo;{kp.what_was_said}&rdquo;</p>
                                )}
                              </div>
                            ) : (
                              /* Suggest button */
                              <button
                                onClick={() => handleOpenSuggest(i)}
                                disabled={suggestLoading === i}
                                aria-label={panelOpen ? 'Close suggestions panel' : 'Find or create linked record'}
                                className="mt-1 text-xs bg-purple-600/30 hover:bg-purple-600/50 text-purple-300 px-3 py-1 rounded disabled:opacity-50"
                              >
                                {suggestLoading === i ? 'Searching…' : panelOpen ? '▲ Close' : '🔗 Create / Link Record'}
                              </button>
                            )}
                          </div>

                          {/* ── Suggestions panel (inline) ── */}
                          {panelOpen && suggestions[i] && (
                            <div className="border-t border-border-subtle bg-background/60 p-3 space-y-3">

                              {/* Top-3 fuzzy matches */}
                              {suggestions[i]!.suggestions.length > 0 ? (
                                <>
                                  <p className="text-xs text-text-muted font-medium">Top matches — click to link</p>
                                  {suggestions[i]!.suggestions.map((s) => (
                                    <div key={s.id} className="flex items-center justify-between gap-3 bg-surface rounded px-3 py-2">
                                      <div className="min-w-0">
                                        <p className="text-sm text-text-main truncate">{s.title}</p>
                                        <p className="text-xs text-text-faint">
                                          {s.account_name ? `${s.account_name} · ` : ''}Stage: {s.stage} · {s.match_reason}
                                        </p>
                                      </div>
                                      <div className="flex items-center gap-2 shrink-0">
                                        <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${confidenceBadge(s.confidence)}`}>
                                          {s.confidence}%
                                        </span>
                                        <button
                                          onClick={() => handleLink(i, s.id)}
                                          disabled={linking === i}
                                          className="text-xs bg-primary hover:bg-blue-700 disabled:opacity-50 text-text-main px-3 py-1 rounded"
                                        >
                                          {linking === i ? '…' : 'Link'}
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </>
                              ) : (
                                <p className="text-xs text-text-faint">No close matches found in existing opportunities.</p>
                              )}

                              {/* Auto-create card */}
                              <div className="border border-border-subtle rounded px-3 py-2 space-y-1">
                                <p className="text-xs text-text-muted font-medium">Create new record</p>
                                <p className="text-xs text-text-main truncate">{suggestions[i]!.auto_create_payload.title}</p>
                                {suggestions[i]!.auto_create_payload.mentioned_company && (
                                  <p className="text-xs text-text-faint">🏢 {suggestions[i]!.auto_create_payload.mentioned_company}</p>
                                )}
                                <button
                                  onClick={() => handleLink(i)}
                                  disabled={linking === i}
                                  className="mt-1 text-xs bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-text-main px-3 py-1 rounded"
                                >
                                  {linking === i ? 'Creating…' : '+ Create New'}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Signals Grid */}
              <div className="grid grid-cols-1 gap-4">
                {[
                  { label: 'Budget Signals', items: selected.budget_signals, color: 'bg-emerald-600/20 text-emerald-300' },
                  { label: 'Competitor Mentions', items: selected.competitor_mentions, color: 'bg-red-600/20 text-danger' },
                  { label: 'Timeline Mentions', items: selected.timeline_mentions, color: 'bg-primary/20 text-primary' },
                  { label: 'Risk Language', items: selected.risk_language, color: 'bg-amber-600/20 text-amber-300' },
                  { label: 'Objection Categories', items: selected.objection_categories, color: 'bg-purple-600/20 text-purple-300' },
                ].map(({ label, items, color }) => (
                  <div key={label} className="bg-surface rounded-lg p-4">
                    <p className="text-xs text-text-faint uppercase tracking-wide mb-2">{label}</p>
                    <TagList items={items} color={color} />
                  </div>
                ))}
              </div>

              {/* Next Steps */}
              {selected.next_steps && (
                <div className="bg-surface rounded-lg p-4">
                  <p className="text-xs text-text-faint uppercase tracking-wide mb-2">Next Steps</p>
                  <p className="text-sm text-text-main">{selected.next_steps}</p>
                </div>
              )}

              {/* Transcript */}
              {selected.transcript && (
                <div className="bg-surface rounded-lg p-4">
                  <p className="text-xs text-text-faint uppercase tracking-wide mb-2">Transcript</p>
                  <pre className="text-xs text-text-muted whitespace-pre-wrap font-mono max-h-60 overflow-y-auto">
                    {selected.transcript}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-surface rounded-lg p-5 text-center text-text-faint text-sm max-w-md mx-auto mt-8">
              Select a call record to view intelligence, or click &ldquo;Analyse Call&rdquo; to submit a transcript.
            </div>
          )}
        </div>
      </div>

      {/* Analyse Modal */}
      {showAnalyseModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold mb-4">Analyse Call Transcript</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-text-muted block mb-1">Company Name</label>
                <input
                  className="w-full bg-background border border-border-subtle rounded px-3 py-2 text-sm"
                  value={form.company_name}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                  placeholder="e.g. Acme Data Centres"
                />
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">Executive Name</label>
                <input
                  className="w-full bg-background border border-border-subtle rounded px-3 py-2 text-sm"
                  value={form.executive_name}
                  onChange={(e) => setForm({ ...form, executive_name: e.target.value })}
                  placeholder="e.g. Jane Smith, CTO"
                />
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">
                  Transcript *{' '}
                  <span className="text-text-faint">(paste call transcript text)</span>
                </label>
                <textarea
                  rows={10}
                  className="w-full bg-background border border-border-subtle rounded px-3 py-2 text-sm font-mono"
                  value={form.transcript}
                  onChange={(e) => setForm({ ...form, transcript: e.target.value })}
                  placeholder="Paste transcript here…"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setShowAnalyseModal(false)}
                className="flex-1 bg-background hover:bg-surface py-2 rounded text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleAnalyse}
                disabled={analysing || !form.transcript}
                className="flex-1 bg-primary hover:bg-blue-700 disabled:opacity-50 py-2 rounded text-sm font-medium"
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
