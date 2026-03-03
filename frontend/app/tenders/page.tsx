'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';

interface TenderAward {
  id: number;
  authority_name: string;
  winning_company: string;
  contract_value?: number;
  currency: string;
  cpv_codes?: string;
  duration_months?: number;
  award_date?: string;
  scope_summary?: string;
  source_url?: string;
  capacity_mw?: number;
  price_per_mw?: number;
  created_at: string;
}

interface PricingModel {
  tender_id: number;
  winning_company: string;
  price_per_mw: number;
  cpi_z_score: number;
  pricing_label: string;
  market_mean_ppmw: number;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

async function fetchTenders(): Promise<TenderAward[]> {
  const res = await fetch(`${API}/tenders`);
  if (!res.ok) return [];
  return res.json();
}

async function createTender(data: Partial<TenderAward>): Promise<TenderAward> {
  const res = await fetch(`${API}/tenders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function fetchPricingModel(id: number): Promise<PricingModel> {
  const res = await fetch(`${API}/tenders/${id}/pricing-model`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function fmtCurrency(v?: number, currency = 'GBP') {
  if (!v) return '—';
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency, maximumFractionDigits: 0 }).format(v);
}

function CPIBadge({ label }: { label: string }) {
  const map: Record<string, string> = {
    premium: 'bg-red-500/20 text-red-400',
    aggressive: 'bg-green-500/20 text-green-400',
    'market-rate': 'bg-blue-500/20 text-blue-400',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${map[label] ?? 'bg-slate-700 text-slate-300'}`}>
      {label}
    </span>
  );
}

export default function TendersPage() {
  const [tenders, setTenders] = useState<TenderAward[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<TenderAward | null>(null);
  const [pricing, setPricing] = useState<PricingModel | null>(null);
  const [pricingLoading, setPricingLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ authority_name: '', winning_company: '', contract_value: '', currency: 'GBP', scope_summary: '', source_url: '', capacity_mw: '', duration_months: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTenders().then(setTenders).finally(() => setLoading(false));
  }, []);

  async function handleSelect(t: TenderAward) {
    setSelected(t);
    setPricing(null);
    if (t.price_per_mw) {
      setPricingLoading(true);
      fetchPricingModel(t.id).then(setPricing).catch(() => {}).finally(() => setPricingLoading(false));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload: Partial<TenderAward> = {
        authority_name: form.authority_name,
        winning_company: form.winning_company,
        currency: form.currency,
        scope_summary: form.scope_summary || undefined,
        source_url: form.source_url || undefined,
      };
      if (form.contract_value) payload.contract_value = parseFloat(form.contract_value);
      if (form.capacity_mw) payload.capacity_mw = parseFloat(form.capacity_mw);
      if (form.duration_months) payload.duration_months = parseInt(form.duration_months);
      const created = await createTender(payload);
      setTenders((p) => [created, ...p]);
      setShowForm(false);
      setForm({ authority_name: '', winning_company: '', contract_value: '', currency: 'GBP', scope_summary: '', source_url: '', capacity_mw: '', duration_months: '' });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Header title="Tender Intelligence" />
      <div className="p-6 space-y-6">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-slate-400 text-sm">Public procurement awards & competitive pricing index</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-medium"
          >
            + Add Award
          </button>
        </div>

        {/* Add form */}
        {showForm && (
          <form onSubmit={handleSubmit} className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
            <h3 className="text-white font-semibold">Add Tender Award</h3>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Authority Name *</label>
                <input required value={form.authority_name} onChange={(e) => setForm((p) => ({ ...p, authority_name: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Winning Company *</label>
                <input required value={form.winning_company} onChange={(e) => setForm((p) => ({ ...p, winning_company: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Contract Value</label>
                <input type="number" value={form.contract_value} onChange={(e) => setForm((p) => ({ ...p, contract_value: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Currency</label>
                <select value={form.currency} onChange={(e) => setForm((p) => ({ ...p, currency: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm">
                  {['GBP','EUR','USD'].map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Capacity (MW) — for CPI</label>
                <input type="number" value={form.capacity_mw} onChange={(e) => setForm((p) => ({ ...p, capacity_mw: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Duration (months)</label>
                <input type="number" value={form.duration_months} onChange={(e) => setForm((p) => ({ ...p, duration_months: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-slate-400 text-xs mb-1">Scope Summary</label>
                <textarea rows={2} value={form.scope_summary} onChange={(e) => setForm((p) => ({ ...p, scope_summary: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-slate-400 text-xs mb-1">Source URL</label>
                <input type="url" value={form.source_url} onChange={(e) => setForm((p) => ({ ...p, source_url: e.target.value }))} className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm" />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg font-medium">
                {saving ? 'Saving…' : 'Save Award'}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg">Cancel</button>
            </div>
          </form>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Award list */}
          <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h2 className="text-white font-semibold">Contract Awards</h2>
            </div>
            {loading ? (
              <div className="p-5 space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-12 bg-slate-700 rounded animate-pulse" />)}</div>
            ) : tenders.length === 0 ? (
              <p className="p-5 text-slate-400 text-sm">No tender awards yet. Add your first award above.</p>
            ) : (
              <div className="divide-y divide-slate-700">
                {tenders.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => handleSelect(t)}
                    className={`w-full text-left px-5 py-4 hover:bg-slate-700/50 transition-colors ${selected?.id === t.id ? 'bg-blue-600/10 border-l-2 border-blue-500' : ''}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className="text-white font-medium text-sm truncate">{t.winning_company}</p>
                        <p className="text-slate-400 text-xs mt-0.5 truncate">{t.authority_name}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-green-400 text-sm font-medium">{fmtCurrency(t.contract_value, t.currency)}</p>
                        {t.price_per_mw && <p className="text-slate-500 text-xs">{fmtCurrency(t.price_per_mw, t.currency)}/MW</p>}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Detail panel */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
            {!selected ? (
              <p className="text-slate-400 text-sm">Select an award to view details and pricing model.</p>
            ) : (
              <>
                <h3 className="text-white font-semibold">{selected.winning_company}</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Authority</span>
                    <span className="text-slate-200 text-right max-w-[60%] truncate">{selected.authority_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Value</span>
                    <span className="text-green-400 font-medium">{fmtCurrency(selected.contract_value, selected.currency)}</span>
                  </div>
                  {selected.capacity_mw != null && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Capacity</span>
                      <span className="text-slate-200">{selected.capacity_mw} MW</span>
                    </div>
                  )}
                  {selected.price_per_mw != null && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Price/MW</span>
                      <span className="text-yellow-400 font-medium">{fmtCurrency(selected.price_per_mw, selected.currency)}</span>
                    </div>
                  )}
                  {selected.duration_months != null && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Duration</span>
                      <span className="text-slate-200">{selected.duration_months} months</span>
                    </div>
                  )}
                </div>

                {selected.scope_summary && (
                  <div>
                    <p className="text-slate-400 text-xs uppercase tracking-wide mb-1">Scope</p>
                    <p className="text-slate-300 text-sm">{selected.scope_summary}</p>
                  </div>
                )}

                {/* CPI Model */}
                {pricingLoading ? (
                  <div className="h-16 bg-slate-700 rounded animate-pulse" />
                ) : pricing ? (
                  <div className="bg-slate-900 rounded-lg p-4 space-y-2">
                    <p className="text-white text-xs font-semibold uppercase tracking-wide">Competitive Pricing Index</p>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-white">{pricing.cpi_z_score.toFixed(2)}</span>
                      <CPIBadge label={pricing.pricing_label} />
                    </div>
                    <p className="text-slate-500 text-xs">z-score vs market mean of {fmtCurrency(pricing.market_mean_ppmw)}/MW</p>
                  </div>
                ) : (
                  <p className="text-slate-500 text-xs">Add capacity_mw to compute the CPI pricing model.</p>
                )}

                {selected.source_url && (
                  <a href={selected.source_url} target="_blank" rel="noopener noreferrer" className="inline-block text-blue-400 hover:text-blue-300 text-xs">
                    View source ↗
                  </a>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
