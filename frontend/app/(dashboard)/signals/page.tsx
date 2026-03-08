'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { signalsApi, SignalEvent } from '@/lib/api';

const EVENT_TYPES = [
  'contract_win',
  'expansion',
  'funding_round',
  'new_role',
  'hiring_spike',
  'executive_post',
  'conference',
  'charity_event',
  'framework_award',
  'planning_notice',
  'general',
];

const STATUS_OPTIONS = ['active', 'archived'];

export default function SignalsPage() {
  const [signals, setSignals] = useState<SignalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SignalEvent | null>(null);
  const [filterCompany, setFilterCompany] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  const [form, setForm] = useState({
    company_name: '',
    event_type: 'general',
    title: '',
    description: '',
    source_url: '',
    relevance_score: '',
    event_date: '',
    status: 'active',
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchSignals = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await signalsApi.list({
        company_name: filterCompany || undefined,
        event_type: filterType || undefined,
      });
      setSignals(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load signal events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilter = () => fetchSignals();

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this signal event?')) return;
    try {
      await signalsApi.delete(id);
      if (selected?.id === id) setSelected(null);
      fetchSignals();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Delete failed');
    }
  };

  const handleArchive = async (id: number) => {
    try {
      await signalsApi.update(id, { status: 'archived' });
      fetchSignals();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Update failed');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await signalsApi.create({
        company_name: form.company_name,
        event_type: form.event_type,
        title: form.title,
        description: form.description || undefined,
        source_url: form.source_url || undefined,
        relevance_score: form.relevance_score ? parseFloat(form.relevance_score) : undefined,
        event_date: form.event_date || undefined,
        status: form.status,
      });
      setShowAddModal(false);
      setForm({
        company_name: '',
        event_type: 'general',
        title: '',
        description: '',
        source_url: '',
        relevance_score: '',
        event_date: '',
        status: 'active',
      });
      fetchSignals();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to create signal event');
    } finally {
      setSubmitting(false);
    }
  };

  const badgeColor = (type: string) => {
    const map: Record<string, string> = {
      contract_win: 'bg-green-500/20 text-green-300',
      expansion: 'bg-blue-500/20 text-blue-300',
      funding_round: 'bg-purple-500/20 text-purple-300',
      new_role: 'bg-yellow-500/20 text-yellow-300',
      hiring_spike: 'bg-orange-500/20 text-orange-300',
      executive_post: 'bg-cyan-500/20 text-cyan-300',
      conference: 'bg-indigo-500/20 text-indigo-300',
      charity_event: 'bg-pink-500/20 text-pink-300',
      framework_award: 'bg-teal-500/20 text-teal-300',
      planning_notice: 'bg-lime-500/20 text-lime-300',
    };
    return map[type] ?? 'bg-color-primary/10 text-color-primary';
  };

  return (
    <div className="flex flex-col min-h-full">
      <Header title="Signals 📡" subtitle="Commercial and relationship signal events" />

      <div className="flex-1 p-6 space-y-6">
        {/* Filters + Add */}
        <div className="glass-card p-4 flex flex-wrap gap-3 items-center">
          <input
            className="input flex-1 min-w-[180px]"
            placeholder="Filter by company…"
            value={filterCompany}
            onChange={(e) => setFilterCompany(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleFilter()}
          />
          <select
            className="input w-44"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All types</option>
            {EVENT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
          <button className="btn-secondary" onClick={handleFilter}>
            Search
          </button>
          <button className="btn-primary ml-auto" onClick={() => setShowAddModal(true)}>
            + Add Signal
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="glass-card p-4 border border-red-500/30 text-red-400">{error}</div>
        )}

        {/* Table */}
        <div className="glass-card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-color-text-muted font-mono animate-pulse">
              Loading signal events…
            </div>
          ) : signals.length === 0 ? (
            <div className="p-8 text-center text-color-text-muted">
              No signal events found. Add one to get started.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-color-border-subtle/40 text-color-text-faint uppercase text-[10px] tracking-widest font-mono">
                  <th className="text-left px-4 py-3">Company</th>
                  <th className="text-left px-4 py-3">Type</th>
                  <th className="text-left px-4 py-3">Title</th>
                  <th className="text-left px-4 py-3">Relevance</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Detected</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {signals.map((s) => (
                  <tr
                    key={s.id}
                    className="border-b border-color-border-subtle/20 hover:bg-color-primary/5 cursor-pointer transition-colors"
                    onClick={() => setSelected(s)}
                  >
                    <td className="px-4 py-3 font-medium text-color-text-main">{s.company_name}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[11px] font-mono ${badgeColor(s.event_type)}`}>
                        {s.event_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-color-text-muted max-w-[260px] truncate">{s.title}</td>
                    <td className="px-4 py-3 text-color-text-muted font-mono">
                      {s.relevance_score !== undefined && s.relevance_score !== null
                        ? (s.relevance_score * 100).toFixed(0) + '%'
                        : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[11px] font-mono ${
                          s.status === 'active'
                            ? 'bg-color-success/20 text-color-success'
                            : 'bg-color-border-subtle/30 text-color-text-faint'
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-color-text-faint font-mono text-[11px]">
                      {new Date(s.detected_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                      {s.status === 'active' && (
                        <button
                          className="text-xs text-color-text-muted hover:text-color-primary"
                          onClick={() => handleArchive(s.id)}
                        >
                          Archive
                        </button>
                      )}
                      <button
                        className="text-xs text-red-400 hover:text-red-300"
                        onClick={() => handleDelete(s.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Detail Panel */}
        {selected && (
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-color-text-main">{selected.title}</h2>
                <p className="text-sm text-color-text-muted mt-0.5">{selected.company_name}</p>
              </div>
              <button
                className="text-color-text-faint hover:text-color-text-muted text-xl leading-none"
                onClick={() => setSelected(null)}
              >
                ×
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-color-text-faint text-[10px] uppercase tracking-wider font-mono mb-1">Type</p>
                <p className="font-mono">{selected.event_type.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <p className="text-color-text-faint text-[10px] uppercase tracking-wider font-mono mb-1">Relevance</p>
                <p className="font-mono">
                  {selected.relevance_score !== undefined && selected.relevance_score !== null
                    ? (selected.relevance_score * 100).toFixed(0) + '%'
                    : '—'}
                </p>
              </div>
              <div>
                <p className="text-color-text-faint text-[10px] uppercase tracking-wider font-mono mb-1">Status</p>
                <p className="font-mono">{selected.status}</p>
              </div>
              <div>
                <p className="text-color-text-faint text-[10px] uppercase tracking-wider font-mono mb-1">Event Date</p>
                <p className="font-mono">
                  {selected.event_date ? new Date(selected.event_date).toLocaleDateString() : '—'}
                </p>
              </div>
            </div>
            {selected.description && (
              <div>
                <p className="text-color-text-faint text-[10px] uppercase tracking-wider font-mono mb-1">Description</p>
                <p className="text-sm text-color-text-muted whitespace-pre-wrap">{selected.description}</p>
              </div>
            )}
            {selected.source_url && (
              <div>
                <p className="text-color-text-faint text-[10px] uppercase tracking-wider font-mono mb-1">Source</p>
                <a
                  href={selected.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-color-primary text-sm hover:underline break-all"
                >
                  {selected.source_url}
                </a>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={(e) => e.target === e.currentTarget && setShowAddModal(false)}
        >
          <div className="glass-card w-full max-w-lg p-6 space-y-4">
            <h2 className="text-lg font-semibold text-color-text-main">Add Signal Event</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="label">Company *</label>
                <input
                  className="input w-full"
                  required
                  value={form.company_name}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                />
              </div>
              <div>
                <label className="label">Title *</label>
                <input
                  className="input w-full"
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Event Type</label>
                  <select
                    className="input w-full"
                    value={form.event_type}
                    onChange={(e) => setForm({ ...form, event_type: e.target.value })}
                  >
                    {EVENT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Status</label>
                  <select
                    className="input w-full"
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Relevance Score (0–1)</label>
                  <input
                    className="input w-full"
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={form.relevance_score}
                    onChange={(e) => setForm({ ...form, relevance_score: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Event Date</label>
                  <input
                    className="input w-full"
                    type="date"
                    value={form.event_date}
                    onChange={(e) => setForm({ ...form, event_date: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="label">Description</label>
                <textarea
                  className="input w-full h-20 resize-none"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>
              <div>
                <label className="label">Source URL</label>
                <input
                  className="input w-full"
                  type="url"
                  value={form.source_url}
                  onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1" disabled={submitting}>
                  {submitting ? 'Saving…' : 'Save Signal'}
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
