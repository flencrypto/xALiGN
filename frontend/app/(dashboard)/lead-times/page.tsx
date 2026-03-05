'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { leadTimeApi, LeadTimeItem } from '@/lib/api';

const CATEGORIES = [
  'switchgear', 'ups', 'chiller', 'generator', 'pdu',
  'crac', 'transformer', 'busbar', 'battery', 'other',
];

const CAT_ICONS: Record<string, string> = {
  switchgear: '⚡', ups: '🔋', chiller: '❄️', generator: '🛢️',
  pdu: '🔌', crac: '💨', transformer: '🔧', busbar: '📊',
  battery: '🔋', other: '📦',
};

const WEEK_COLORS = (min: number) => {
  if (min <= 12) return 'text-success bg-success/10';
  if (min <= 24) return 'text-warning bg-warning/10';
  return 'text-danger bg-danger/10';
};

interface NewItemForm {
  category: string;
  manufacturer: string;
  model_ref: string;
  description: string;
  lead_weeks_min: string;
  lead_weeks_max: string;
  region: string;
  notes: string;
  source: string;
}

const EMPTY_FORM: NewItemForm = {
  category: 'switchgear', manufacturer: '', model_ref: '', description: '',
  lead_weeks_min: '', lead_weeks_max: '', region: 'UK', notes: '', source: '',
};

export default function LeadTimesPage() {
  const [items, setItems] = useState<LeadTimeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [filterCat, setFilterCat] = useState('');
  const [filterRegion, setFilterRegion] = useState('');
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<NewItemForm>(EMPTY_FORM);

  async function load() {
    setLoading(true);
    try {
      const data = await leadTimeApi.list(filterCat || undefined, filterRegion || undefined);
      setItems(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterCat, filterRegion]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSeed() {
    setSeeding(true);
    try {
      const created = await leadTimeApi.seed();
      if (created.length === 0) {
        alert('All default items already loaded.');
      }
      await load();
    } catch {
      alert('Seed failed – check backend connection.');
    } finally {
      setSeeding(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await leadTimeApi.create({
        category: form.category,
        manufacturer: form.manufacturer || undefined,
        model_ref: form.model_ref || undefined,
        description: form.description,
        lead_weeks_min: parseInt(form.lead_weeks_min, 10),
        lead_weeks_max: parseInt(form.lead_weeks_max, 10),
        region: form.region || undefined,
        notes: form.notes || undefined,
        source: form.source || undefined,
      });
      setForm(EMPTY_FORM);
      setShowNew(false);
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this lead-time entry?')) return;
    await leadTimeApi.delete(id);
    setItems((prev) => prev.filter((i) => i.id !== id));
  }

  const grouped: Record<string, LeadTimeItem[]> = {};
  for (const item of items) {
    (grouped[item.category] ??= []).push(item);
  }

  const action = (
    <div className="flex gap-2">
      <button
        onClick={handleSeed}
        disabled={seeding}
        className="bg-surface border border-border-subtle text-text-muted hover:text-text-main px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50"
      >
        {seeding ? 'Seeding…' : '⚡ Seed Defaults'}
      </button>
      <button
        onClick={() => setShowNew(true)}
        className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 px-3 py-1.5 rounded-lg text-xs font-medium"
      >
        + Add Item
      </button>
    </div>
  );

  return (
    <>
      <Header title="Lead-Time Intelligence" action={action} />

      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <select
            value={filterCat}
            onChange={(e) => setFilterCat(e.target.value)}
            className="bg-surface border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{CAT_ICONS[c]} {c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
          <input
            placeholder="Filter by region…"
            value={filterRegion}
            onChange={(e) => setFilterRegion(e.target.value)}
            className="bg-surface border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary w-48"
          />
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-4xl mb-3">⏱</p>
            <p className="text-text-muted text-sm mb-4">No lead-time data yet.</p>
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 px-5 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {seeding ? 'Seeding…' : '⚡ Load Default Dataset (switchgear, UPS, chillers, generators…)'}
            </button>
          </div>
        ) : (
          Object.entries(grouped).map(([cat, catItems]) => (
            <div key={cat} className="bg-surface border border-border-subtle rounded-xl overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border-subtle bg-background/40">
                <span className="text-lg">{CAT_ICONS[cat] ?? '📦'}</span>
                <h3 className="text-text-main font-semibold capitalize">{cat}</h3>
                <span className="text-text-muted text-xs ml-auto">{catItems.length} item{catItems.length !== 1 ? 's' : ''}</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-subtle">
                      <th className="text-left px-4 py-2.5 text-text-muted font-medium">Manufacturer / Model</th>
                      <th className="text-left px-4 py-2.5 text-text-muted font-medium">Description</th>
                      <th className="text-left px-4 py-2.5 text-text-muted font-medium">Lead Time (weeks)</th>
                      <th className="text-left px-4 py-2.5 text-text-muted font-medium">Region</th>
                      <th className="text-left px-4 py-2.5 text-text-muted font-medium hidden lg:table-cell">Source</th>
                      <th className="px-4 py-2.5" />
                    </tr>
                  </thead>
                  <tbody>
                    {catItems.map((item) => (
                      <tr key={item.id} className="border-b border-border-subtle/40 hover:bg-white/2">
                        <td className="px-4 py-3">
                          <p className="text-text-main font-medium">{item.manufacturer ?? '—'}</p>
                          {item.model_ref && <p className="text-text-muted text-xs">{item.model_ref}</p>}
                        </td>
                        <td className="px-4 py-3 text-text-muted max-w-xs">
                          <p className="line-clamp-2">{item.description}</p>
                          {item.notes && <p className="text-xs text-warning/80 mt-1">{item.notes}</p>}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded-md text-xs font-mono font-semibold ${WEEK_COLORS(item.lead_weeks_min)}`}>
                            {item.lead_weeks_min}–{item.lead_weeks_max}w
                          </span>
                          {item.lead_weeks_typical && (
                            <p className="text-text-faint text-xs mt-1">typical: {item.lead_weeks_typical}w</p>
                          )}
                        </td>
                        <td className="px-4 py-3 text-text-muted text-xs">{item.region ?? '—'}</td>
                        <td className="px-4 py-3 text-text-faint text-xs hidden lg:table-cell">{item.source ?? '—'}</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="text-text-faint hover:text-danger text-xs transition-colors"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))
        )}
      </div>

      {/* New Item Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-text-main font-semibold text-lg mb-4">Add Lead-Time Item</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <select
                  required
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="col-span-2 bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{CAT_ICONS[c]} {c}</option>
                  ))}
                </select>
                <input
                  placeholder="Manufacturer"
                  value={form.manufacturer}
                  onChange={(e) => setForm({ ...form, manufacturer: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
                <input
                  placeholder="Model Ref"
                  value={form.model_ref}
                  onChange={(e) => setForm({ ...form, model_ref: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
              </div>
              <input
                required
                placeholder="Description *"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
              <div className="grid grid-cols-3 gap-3">
                <input
                  required
                  type="number"
                  min="1"
                  placeholder="Min weeks *"
                  value={form.lead_weeks_min}
                  onChange={(e) => setForm({ ...form, lead_weeks_min: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
                <input
                  required
                  type="number"
                  min="1"
                  placeholder="Max weeks *"
                  value={form.lead_weeks_max}
                  onChange={(e) => setForm({ ...form, lead_weeks_max: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
                <input
                  placeholder="Region"
                  value={form.region}
                  onChange={(e) => setForm({ ...form, region: e.target.value })}
                  className="bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
              </div>
              <input
                placeholder="Source / reference"
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
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
                  onClick={() => { setShowNew(false); setForm(EMPTY_FORM); }}
                  className="px-4 py-2 text-text-muted hover:text-text-main text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {saving ? 'Saving…' : 'Add Item'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
