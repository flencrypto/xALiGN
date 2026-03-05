'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { frameworksApi, ProcurementFramework } from '@/lib/api';

const STATUS_STYLES: Record<string, string> = {
  active:        'bg-success/10 text-success border-success/30',
  expiring_soon: 'bg-warning/10 text-warning border-warning/30',
  expired:       'bg-danger/10 text-danger border-danger/30',
  pending:       'bg-secondary/10 text-secondary border-secondary/30',
  not_listed:    'bg-surface text-text-muted border-border-subtle',
};

const STATUS_LABELS: Record<string, string> = {
  active: 'Active', expiring_soon: 'Expiring Soon', expired: 'Expired',
  pending: 'Pending', not_listed: 'Not Listed',
};

function daysUntil(dateStr?: string): number | null {
  if (!dateStr) return null;
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.ceil(diff / 86400000);
}

function fmtDate(d?: string) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

interface NewFwForm {
  name: string; authority: string; reference: string; region: string;
  status: string; start_date: string; expiry_date: string;
  url: string; notes: string; we_are_listed: boolean;
}
const EMPTY: NewFwForm = {
  name: '', authority: '', reference: '', region: 'UK',
  status: 'active', start_date: '', expiry_date: '',
  url: '', notes: '', we_are_listed: false,
};

export default function FrameworksPage() {
  const [frameworks, setFrameworks] = useState<ProcurementFramework[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterListed, setFilterListed] = useState<'' | 'true' | 'false'>('');
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<NewFwForm>(EMPTY);
  const [editing, setEditing] = useState<ProcurementFramework | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await frameworksApi.list(
        filterStatus || undefined,
        undefined,
        filterListed !== '' ? filterListed === 'true' : undefined,
      );
      setFrameworks(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus, filterListed]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        authority: form.authority,
        reference: form.reference || undefined,
        region: form.region || undefined,
        status: form.status as ProcurementFramework['status'],
        start_date: form.start_date || undefined,
        expiry_date: form.expiry_date || undefined,
        url: form.url || undefined,
        notes: form.notes || undefined,
        we_are_listed: form.we_are_listed,
      };
      if (editing) {
        await frameworksApi.update(editing.id, payload);
      } else {
        await frameworksApi.create(payload);
      }
      setForm(EMPTY);
      setShowNew(false);
      setEditing(null);
      await load();
    } finally {
      setSaving(false);
    }
  }

  function startEdit(fw: ProcurementFramework) {
    setForm({
      name: fw.name, authority: fw.authority, reference: fw.reference ?? '',
      region: fw.region ?? 'UK', status: fw.status,
      start_date: fw.start_date ?? '', expiry_date: fw.expiry_date ?? '',
      url: fw.url ?? '', notes: fw.notes ?? '', we_are_listed: fw.we_are_listed,
    });
    setEditing(fw);
    setShowNew(true);
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this framework?')) return;
    await frameworksApi.delete(id);
    setFrameworks((prev) => prev.filter((f) => f.id !== id));
  }

  // Counts for KPI bar
  const activeCount  = frameworks.filter((f) => f.status === 'active').length;
  const listedCount  = frameworks.filter((f) => f.we_are_listed).length;
  const expiringCount= frameworks.filter((f) => f.status === 'expiring_soon').length;
  const expiredCount = frameworks.filter((f) => f.status === 'expired').length;

  const action = (
    <button
      onClick={() => { setForm(EMPTY); setEditing(null); setShowNew(true); }}
      className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 px-3 py-1.5 rounded-lg text-xs font-medium"
    >
      + Add Framework
    </button>
  );

  return (
    <>
      <Header title="Procurement Frameworks" action={action} />

      <div className="p-6 space-y-5">
        {/* KPI row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Active', value: activeCount,   color: 'text-success', bg: 'bg-success/10' },
            { label: 'We Are Listed', value: listedCount,  color: 'text-primary', bg: 'bg-primary/10' },
            { label: 'Expiring Soon', value: expiringCount, color: 'text-warning', bg: 'bg-warning/10' },
            { label: 'Expired',       value: expiredCount,  color: 'text-danger',  bg: 'bg-danger/10'  },
          ].map(({ label, value, color, bg }) => (
            <div key={label} className={`${bg} border border-border-subtle rounded-xl p-4`}>
              <p className={`text-2xl font-bold font-mono ${color}`}>{value}</p>
              <p className="text-text-muted text-xs mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-surface border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
          >
            <option value="">All Statuses</option>
            {Object.entries(STATUS_LABELS).map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
          <select
            value={filterListed}
            onChange={(e) => setFilterListed(e.target.value as '' | 'true' | 'false')}
            className="bg-surface border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
          >
            <option value="">All (listed + not listed)</option>
            <option value="true">We are listed only</option>
            <option value="false">Not listed</option>
          </select>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : frameworks.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-4xl mb-3">🏛</p>
            <p className="text-text-muted text-sm mb-4">No frameworks yet. Add the first one above.</p>
          </div>
        ) : (
          <div className="bg-surface border border-border-subtle rounded-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left px-4 py-3 text-text-muted font-medium">Framework</th>
                  <th className="text-left px-4 py-3 text-text-muted font-medium">Authority</th>
                  <th className="text-left px-4 py-3 text-text-muted font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-text-muted font-medium">Listed?</th>
                  <th className="text-left px-4 py-3 text-text-muted font-medium hidden md:table-cell">Expiry</th>
                  <th className="text-left px-4 py-3 text-text-muted font-medium hidden lg:table-cell">Region</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {frameworks.map((fw) => {
                  const days = daysUntil(fw.expiry_date);
                  return (
                    <tr key={fw.id} className="border-b border-border-subtle/40 hover:bg-white/2">
                      <td className="px-4 py-3">
                        <p className="text-text-main font-medium">{fw.name}</p>
                        {fw.reference && <p className="text-text-faint text-xs">{fw.reference}</p>}
                        {fw.url && (
                          <a
                            href={fw.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary text-xs hover:underline"
                          >
                            View →
                          </a>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text-muted">{fw.authority}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${STATUS_STYLES[fw.status] ?? STATUS_STYLES.not_listed}`}>
                          {STATUS_LABELS[fw.status] ?? fw.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {fw.we_are_listed ? (
                          <span className="text-success text-xs font-medium">✅ Listed</span>
                        ) : (
                          <span className="text-text-faint text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text-muted hidden md:table-cell">
                        <p>{fmtDate(fw.expiry_date)}</p>
                        {days !== null && days > 0 && days <= 180 && (
                          <p className={`text-xs mt-0.5 ${days <= 90 ? 'text-warning' : 'text-text-faint'}`}>
                            {days}d remaining
                          </p>
                        )}
                        {days !== null && days <= 0 && (
                          <p className="text-xs mt-0.5 text-danger">Expired</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text-muted hidden lg:table-cell">{fw.region ?? '—'}</td>
                      <td className="px-4 py-3 text-right flex gap-2 justify-end">
                        <button
                          onClick={() => startEdit(fw)}
                          className="text-text-faint hover:text-primary text-xs transition-colors"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDelete(fw.id)}
                          className="text-text-faint hover:text-danger text-xs transition-colors"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New / Edit Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-text-main font-semibold text-lg mb-4">
              {editing ? 'Edit Framework' : 'Add Framework'}
            </h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input
                required
                placeholder="Framework name *"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
              <input
                required
                placeholder="Contracting authority *"
                value={form.authority}
                onChange={(e) => setForm({ ...form, authority: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  placeholder="Reference / lot"
                  value={form.reference}
                  onChange={(e) => setForm({ ...form, reference: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
                <input
                  placeholder="Region"
                  value={form.region}
                  onChange={(e) => setForm({ ...form, region: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                >
                  {Object.entries(STATUS_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
                <label className="flex items-center gap-2 text-sm text-text-muted px-3 py-2 bg-background border border-border-subtle rounded-lg cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.we_are_listed}
                    onChange={(e) => setForm({ ...form, we_are_listed: e.target.checked })}
                    className="accent-primary"
                  />
                  We are listed
                </label>
                <div>
                  <label className="text-xs text-text-muted block mb-1">Start date</label>
                  <input
                    type="date"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted block mb-1">Expiry date</label>
                  <input
                    type="date"
                    value={form.expiry_date}
                    onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
                    className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                  />
                </div>
              </div>
              <input
                placeholder="URL"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
              <textarea
                placeholder="Notes"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary h-20 resize-none"
              />
              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => { setShowNew(false); setForm(EMPTY); setEditing(null); }}
                  className="px-4 py-2 text-text-muted hover:text-text-main text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {saving ? 'Saving…' : editing ? 'Save Changes' : 'Add Framework'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
