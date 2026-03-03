'use client';

import { useEffect, useState } from 'react';
import { tenderApi, TenderAward, CPIResult, RelationshipSuggestResult } from '@/lib/api';

const SIGNAL_EVENTS = [
  'contract_win',
  'expansion',
  'new_role',
  'funding_round',
  'conference',
  'charity_event',
  'executive_post',
];

export default function TendersPage() {
  const [awards, setAwards] = useState<TenderAward[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<TenderAward | null>(null);
  const [filterCompany, setFilterCompany] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // CPI scorer state
  const [cpiCompany, setCpiCompany] = useState('');
  const [cpiResult, setCpiResult] = useState<CPIResult | null>(null);
  const [cpiLoading, setCpiLoading] = useState(false);

  // Relationship state
  const [relCompany, setRelCompany] = useState('');
  const [relEvents, setRelEvents] = useState<{ event: string; days: number }[]>([
    { event: 'contract_win', days: 30 },
  ]);
  const [relResult, setRelResult] = useState<RelationshipSuggestResult | null>(null);
  const [relLoading, setRelLoading] = useState(false);

  // New award form
  const [form, setForm] = useState({
    authority_name: '',
    winning_company: '',
    contract_value: '',
    contract_currency: 'GBP',
    scope_summary: '',
    award_date: '',
    duration_months: '',
    source_url: '',
    region: '',
    mw_capacity: '',
    framework: false,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchAwards = async (company?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await tenderApi.list(company || undefined);
      setAwards(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load tender awards');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAwards();
  }, []);

  const handleFilter = () => fetchAwards(filterCompany || undefined);

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this tender award?')) return;
    try {
      await tenderApi.delete(id);
      if (selected?.id === id) setSelected(null);
      fetchAwards(filterCompany || undefined);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Delete failed');
    }
  };

  const handleAddSubmit = async () => {
    if (!form.authority_name || !form.winning_company) return;
    setSubmitting(true);
    try {
      await tenderApi.create({
        authority_name: form.authority_name,
        winning_company: form.winning_company,
        contract_value: form.contract_value ? parseFloat(form.contract_value) : undefined,
        contract_currency: form.contract_currency || 'GBP',
        scope_summary: form.scope_summary || undefined,
        award_date: form.award_date || undefined,
        duration_months: form.duration_months ? parseInt(form.duration_months) : undefined,
        source_url: form.source_url || undefined,
        region: form.region || undefined,
        mw_capacity: form.mw_capacity ? parseFloat(form.mw_capacity) : undefined,
        framework: form.framework,
      });
      setShowAddModal(false);
      setForm({
        authority_name: '',
        winning_company: '',
        contract_value: '',
        contract_currency: 'GBP',
        scope_summary: '',
        award_date: '',
        duration_months: '',
        source_url: '',
        region: '',
        mw_capacity: '',
        framework: false,
      });
      fetchAwards(filterCompany || undefined);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to add tender award');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCPI = async () => {
    if (!cpiCompany) return;
    setCpiLoading(true);
    setCpiResult(null);
    try {
      const result = await tenderApi.getCPI(cpiCompany);
      setCpiResult(result);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'CPI computation failed');
    } finally {
      setCpiLoading(false);
    }
  };

  const handleRelationship = async () => {
    if (!relCompany) return;
    setRelLoading(true);
    setRelResult(null);
    try {
      const result = await tenderApi.suggestRelationship({
        company_name: relCompany,
        recent_events: relEvents.map((e) => e.event),
        days_since_events: relEvents.map((e) => e.days),
      });
      setRelResult(result);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Relationship analysis failed');
    } finally {
      setRelLoading(false);
    }
  };

  const formatValue = (value?: number, currency?: string) => {
    if (value == null) return '—';
    return `${currency ?? ''}${value.toLocaleString()}`;
  };

  const cpiColor = (cpi?: number | null) => {
    if (cpi == null) return 'text-slate-400';
    if (cpi < -0.5) return 'text-emerald-400';
    if (cpi > 0.5) return 'text-amber-400';
    return 'text-blue-400';
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 text-white">
      {/* Header */}
      <div className="border-b border-slate-700 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Tender Award Intelligence</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Track public contract awards, model competitor pricing, and optimise outreach timing.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded"
        >
          + Add Award
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel */}
        <div className="w-80 border-r border-slate-700 flex flex-col">
          {/* Filter */}
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

          {/* Award List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <p className="p-4 text-slate-400 text-sm">Loading…</p>
            ) : error ? (
              <p className="p-4 text-red-400 text-sm">{error}</p>
            ) : awards.length === 0 ? (
              <p className="p-4 text-slate-500 text-sm">No tender awards found.</p>
            ) : (
              awards.map((award) => (
                <button
                  key={award.id}
                  onClick={() => setSelected(award)}
                  className={`w-full text-left px-4 py-3 border-b border-slate-700/50 hover:bg-slate-800 transition-colors ${
                    selected?.id === award.id ? 'bg-blue-600/20 border-r-2 border-r-blue-500' : ''
                  }`}
                >
                  <p className="text-sm font-medium text-white truncate">{award.winning_company}</p>
                  <p className="text-xs text-slate-400 truncate">{award.authority_name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-emerald-400 font-medium">
                      {formatValue(award.contract_value, award.contract_currency)}
                    </span>
                    {award.framework && (
                      <span className="text-xs bg-purple-600/30 text-purple-300 px-1.5 py-0.5 rounded">
                        Framework
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Selected Award Detail */}
          {selected ? (
            <div className="bg-slate-800 rounded-lg p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-lg font-bold">{selected.winning_company}</h2>
                  <p className="text-slate-400 text-sm">{selected.authority_name}</p>
                </div>
                <button
                  onClick={() => handleDelete(selected.id)}
                  className="text-red-400 hover:text-red-300 text-sm"
                >
                  Delete
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide">Contract Value</p>
                  <p className="font-medium">{formatValue(selected.contract_value, selected.contract_currency)}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide">Award Date</p>
                  <p className="font-medium">{selected.award_date ?? '—'}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide">Duration</p>
                  <p className="font-medium">{selected.duration_months ? `${selected.duration_months} months` : '—'}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide">Region</p>
                  <p className="font-medium">{selected.region ?? '—'}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide">MW Capacity</p>
                  <p className="font-medium">{selected.mw_capacity != null ? `${selected.mw_capacity} MW` : '—'}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide">Framework</p>
                  <p className="font-medium">{selected.framework ? 'Yes' : 'No'}</p>
                </div>
              </div>
              {selected.scope_summary && (
                <div className="mt-4">
                  <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">Scope Summary</p>
                  <p className="text-sm text-slate-300">{selected.scope_summary}</p>
                </div>
              )}
              {selected.competitors && selected.competitors.length > 0 && (
                <div className="mt-4">
                  <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">Competitors</p>
                  <div className="flex flex-wrap gap-2">
                    {selected.competitors.map((c) => (
                      <span key={c} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {selected.source_url && (
                <a
                  href={selected.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 inline-block text-xs text-blue-400 hover:underline"
                >
                  View Source →
                </a>
              )}
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-5 text-center text-slate-500 text-sm">
              Select a tender award to view details.
            </div>
          )}

          {/* CPI Scorer */}
          <div className="bg-slate-800 rounded-lg p-5">
            <h3 className="font-semibold mb-3">Competitive Pricing Index (CPI)</h3>
            <p className="text-xs text-slate-400 mb-3">
              CPI &lt; 0 = aggressive pricing · CPI &gt; 0 = premium pricing
            </p>
            <div className="flex gap-2 mb-4">
              <input
                className="flex-1 bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm placeholder-slate-500"
                placeholder="Company name…"
                value={cpiCompany}
                onChange={(e) => setCpiCompany(e.target.value)}
              />
              <button
                onClick={handleCPI}
                disabled={cpiLoading || !cpiCompany}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-4 py-2 rounded text-sm font-medium"
              >
                {cpiLoading ? 'Computing…' : 'Compute CPI'}
              </button>
            </div>
            {cpiResult && (
              <div className="bg-slate-700/50 rounded p-4 text-sm space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Company</span>
                  <span className="font-medium">{cpiResult.company}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Awards Analysed</span>
                  <span>{cpiResult.award_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Value</span>
                  <span>{cpiResult.total_value.toLocaleString()}</span>
                </div>
                {cpiResult.avg_price_per_mw != null && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Avg Price/MW</span>
                    <span>{cpiResult.avg_price_per_mw.toLocaleString()}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-slate-400">CPI</span>
                  <span className={`font-bold ${cpiColor(cpiResult.cpi)}`}>
                    {cpiResult.cpi != null ? cpiResult.cpi.toFixed(3) : '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Interpretation</span>
                  <span className="text-right max-w-[180px]">{cpiResult.interpretation}</span>
                </div>
              </div>
            )}
          </div>

          {/* Relationship Timing */}
          <div className="bg-slate-800 rounded-lg p-5">
            <h3 className="font-semibold mb-3">Relationship Timing Engine</h3>
            <p className="text-xs text-slate-400 mb-3">
              Compute optimal outreach timing using signal decay and AI brief generation.
            </p>
            <input
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm placeholder-slate-500 mb-3"
              placeholder="Target company name…"
              value={relCompany}
              onChange={(e) => setRelCompany(e.target.value)}
            />
            <div className="space-y-2 mb-3">
              {relEvents.map((ev, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <select
                    value={ev.event}
                    onChange={(e) => {
                      const updated = [...relEvents];
                      updated[i] = { ...updated[i], event: e.target.value };
                      setRelEvents(updated);
                    }}
                    className="bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm flex-1"
                  >
                    {SIGNAL_EVENTS.map((s) => (
                      <option key={s} value={s}>
                        {s.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    value={ev.days}
                    onChange={(e) => {
                      const updated = [...relEvents];
                      updated[i] = { ...updated[i], days: parseInt(e.target.value) || 0 };
                      setRelEvents(updated);
                    }}
                    className="bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm w-20"
                    placeholder="Days"
                    min={0}
                  />
                  <span className="text-xs text-slate-500">days ago</span>
                  {relEvents.length > 1 && (
                    <button
                      onClick={() => setRelEvents(relEvents.filter((_, j) => j !== i))}
                      className="text-red-400 hover:text-red-300 text-sm"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setRelEvents([...relEvents, { event: 'contract_win', days: 14 }])}
                className="text-sm text-slate-400 hover:text-white"
              >
                + Add Signal
              </button>
              <button
                onClick={handleRelationship}
                disabled={relLoading || !relCompany}
                className="ml-auto bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-4 py-2 rounded text-sm font-medium"
              >
                {relLoading ? 'Analysing…' : 'Generate Brief'}
              </button>
            </div>
            {relResult && (
              <div className="mt-4 bg-slate-700/50 rounded p-4 text-sm space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Timing Score</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-slate-600 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${relResult.timing_score * 100}%` }}
                      />
                    </div>
                    <span className="font-bold">{(relResult.timing_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Recommend Contact</span>
                  <span className={relResult.recommend_contact ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                    {relResult.recommend_contact ? '✓ Yes' : '○ Not Yet'}
                  </span>
                </div>
                <hr className="border-slate-600" />
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">Suggested Angle</p>
                  <p className="text-slate-200">{relResult.suggested_angle}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">Why Now</p>
                  <p className="text-slate-200">{relResult.why_now}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">What to Mention</p>
                  <p className="text-slate-200">{relResult.what_to_mention}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">What to Avoid</p>
                  <p className="text-slate-300">{relResult.what_to_avoid}</p>
                </div>
                {relResult.risk_flags && (
                  <div>
                    <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">Risk Flags</p>
                    <p className="text-amber-300">{relResult.risk_flags}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Award Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold mb-4">Add Tender Award</h2>
            <div className="space-y-3">
              {[
                { label: 'Contracting Authority *', key: 'authority_name', type: 'text' },
                { label: 'Winning Company *', key: 'winning_company', type: 'text' },
                { label: 'Contract Value', key: 'contract_value', type: 'number' },
                { label: 'Currency', key: 'contract_currency', type: 'text' },
                { label: 'Award Date (YYYY-MM-DD)', key: 'award_date', type: 'text' },
                { label: 'Duration (months)', key: 'duration_months', type: 'number' },
                { label: 'MW Capacity', key: 'mw_capacity', type: 'number' },
                { label: 'Region', key: 'region', type: 'text' },
                { label: 'Source URL', key: 'source_url', type: 'text' },
              ].map(({ label, key, type }) => (
                <div key={key}>
                  <label className="text-xs text-slate-400 block mb-1">{label}</label>
                  <input
                    type={type}
                    className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
                    value={String((form as Record<string, string | boolean>)[key])}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  />
                </div>
              ))}
              <div>
                <label className="text-xs text-slate-400 block mb-1">Scope Summary</label>
                <textarea
                  rows={3}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
                  value={form.scope_summary}
                  onChange={(e) => setForm({ ...form, scope_summary: e.target.value })}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="framework"
                  checked={form.framework}
                  onChange={(e) => setForm({ ...form, framework: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="framework" className="text-sm text-slate-300">
                  Framework Contract
                </label>
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleAddSubmit}
                disabled={submitting || !form.authority_name || !form.winning_company}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 py-2 rounded text-sm font-medium"
              >
                {submitting ? 'Saving…' : 'Add Award'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
