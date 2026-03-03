'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { bidsApi, opportunitiesApi, Bid, BidDocument, ComplianceItem, RFI, Opportunity } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  review: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  submitted: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  won: 'bg-green-500/20 text-green-300 border-green-500/30',
  lost: 'bg-red-500/20 text-red-300 border-red-500/30',
};

const COMPLIANCE_STATUS_COLORS: Record<string, string> = {
  yes: 'bg-green-500/20 text-green-400',
  partial: 'bg-yellow-500/20 text-yellow-400',
  no: 'bg-red-500/20 text-red-400',
  tbc: 'bg-slate-500/20 text-slate-400',
};

const RFI_PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-500/20 text-red-400 border-red-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

type Tab = 'overview' | 'documents' | 'compliance' | 'rfis';

interface NewBidForm { title: string; opportunity_id: string; status: string; win_themes: string; notes: string; }

export default function BidsPage() {
  const [bids, setBids] = useState<Bid[]>([]);
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Bid | null>(null);
  const [tab, setTab] = useState<Tab>('overview');
  const [documents, setDocuments] = useState<BidDocument[]>([]);
  const [compliance, setCompliance] = useState<ComplianceItem[]>([]);
  const [rfis, setRfis] = useState<RFI[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState('');
  const [form, setForm] = useState<NewBidForm>({ title: '', opportunity_id: '', status: 'draft', win_themes: '', notes: '' });

  useEffect(() => {
    Promise.all([bidsApi.list().catch(() => []), opportunitiesApi.list().catch(() => [])])
      .then(([b, o]) => { setBids(b); setOpps(o); })
      .finally(() => setLoading(false));
  }, []);

  async function selectBid(bid: Bid) {
    setSelected(bid);
    setTab('overview');
    const [docs, comp, r] = await Promise.all([
      bidsApi.listDocuments(bid.id).catch(() => []),
      bidsApi.listComplianceItems(bid.id).catch(() => []),
      bidsApi.listRFIs(bid.id).catch(() => []),
    ]);
    setDocuments(docs);
    setCompliance(comp);
    setRfis(r);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const bid = await bidsApi.create({ ...form, opportunity_id: Number(form.opportunity_id) });
      setBids((prev) => [...prev, bid]);
      setShowNew(false);
      setForm({ title: '', opportunity_id: '', status: 'draft', win_themes: '', notes: '' });
    } finally {
      setSaving(false);
    }
  }

  async function generateCompliance() {
    if (!selected) return;
    setGenerating('compliance');
    try {
      const items = await bidsApi.generateComplianceMatrix(selected.id);
      setCompliance(items);
      setTab('compliance');
    } catch {
      /* ignore */
    } finally {
      setGenerating('');
    }
  }

  async function generateRFIs() {
    if (!selected) return;
    setGenerating('rfis');
    try {
      const items = await bidsApi.generateRFIs(selected.id);
      setRfis(items);
      setTab('rfis');
    } catch {
      /* ignore */
    } finally {
      setGenerating('');
    }
  }

  function oppTitle(id: number) { return opps.find((o) => o.id === id)?.title ?? '—'; }

  return (
    <>
      <Header
        title="Bid Pack Builder"
        action={
          <button onClick={() => setShowNew(true)} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            + New Bid
          </button>
        }
      />
      <div className="flex flex-1 overflow-hidden">
        {/* List */}
        <div className={`${selected ? 'hidden lg:flex' : 'flex'} flex-col w-full lg:w-72 xl:w-80 flex-shrink-0 border-r border-slate-700 overflow-auto`}>
          <div className="p-4 flex-1">
            {loading ? (
              <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-slate-800 rounded-xl animate-pulse" />)}</div>
            ) : bids.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-4xl mb-3">📋</p>
                <p className="text-slate-400 text-sm">No bids yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {bids.map((bid) => (
                  <div
                    key={bid.id}
                    onClick={() => selectBid(bid)}
                    className={`bg-slate-800 border rounded-xl p-4 cursor-pointer hover:border-blue-500/50 transition-colors ${selected?.id === bid.id ? 'border-blue-500' : 'border-slate-700'}`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-white text-sm font-medium leading-snug">{bid.title}</p>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0 ${STATUS_COLORS[bid.status] ?? STATUS_COLORS.draft}`}>{bid.status}</span>
                    </div>
                    <p className="text-slate-400 text-xs">{oppTitle(bid.opportunity_id)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Detail */}
        {selected && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Tabs */}
            <div className="flex items-center gap-1 px-4 pt-4 border-b border-slate-700 bg-slate-900">
              <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-white mr-3 lg:hidden">← Back</button>
              {(['overview', 'documents', 'compliance', 'rfis'] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${tab === t ? 'border-blue-500 text-blue-400' : 'border-transparent text-slate-400 hover:text-white'}`}
                >
                  {t}
                </button>
              ))}
              <div className="ml-auto flex gap-2 pb-2">
                <button onClick={generateCompliance} disabled={!!generating} className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1 rounded text-xs font-medium disabled:opacity-50">
                  {generating === 'compliance' ? '⏳ Generating…' : '⚡ Gen Compliance'}
                </button>
                <button onClick={generateRFIs} disabled={!!generating} className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1 rounded text-xs font-medium disabled:opacity-50">
                  {generating === 'rfis' ? '⏳ Generating…' : '⚡ Gen RFIs'}
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-5">
              {/* Overview */}
              {tab === 'overview' && (
                <div className="space-y-4 max-w-2xl">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                      <p className="text-slate-400 text-xs mb-1">Status</p>
                      <span className={`px-2 py-1 rounded text-xs font-semibold border ${STATUS_COLORS[selected.status] ?? STATUS_COLORS.draft}`}>{selected.status}</span>
                    </div>
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                      <p className="text-slate-400 text-xs mb-1">Opportunity</p>
                      <p className="text-white text-sm">{oppTitle(selected.opportunity_id)}</p>
                    </div>
                  </div>
                  {selected.win_themes && (
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                      <p className="text-slate-400 text-xs mb-2">Win Themes</p>
                      <p className="text-slate-200 text-sm whitespace-pre-wrap">{selected.win_themes}</p>
                    </div>
                  )}
                  {selected.notes && (
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                      <p className="text-slate-400 text-xs mb-2">Notes</p>
                      <p className="text-slate-200 text-sm whitespace-pre-wrap">{selected.notes}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Documents */}
              {tab === 'documents' && (
                <div className="max-w-2xl">
                  {documents.length === 0 ? (
                    <div className="text-center py-16">
                      <p className="text-3xl mb-2">📄</p>
                      <p className="text-slate-400 text-sm">No documents uploaded.</p>
                    </div>
                  ) : (
                    <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-700">
                            <th className="text-left px-4 py-3 text-slate-400 font-medium">Name</th>
                            <th className="text-left px-4 py-3 text-slate-400 font-medium">Type</th>
                            <th className="text-left px-4 py-3 text-slate-400 font-medium">Uploaded</th>
                          </tr>
                        </thead>
                        <tbody>
                          {documents.map((d) => (
                            <tr key={d.id} className="border-b border-slate-700/50">
                              <td className="px-4 py-3 text-white">{d.filename}</td>
                              <td className="px-4 py-3 text-slate-400">{d.doc_type ?? '—'}</td>
                              <td className="px-4 py-3 text-slate-400">{d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Compliance */}
              {tab === 'compliance' && (
                <div>
                  {compliance.length === 0 ? (
                    <div className="text-center py-16">
                      <p className="text-3xl mb-2">✅</p>
                      <p className="text-slate-400 text-sm">No compliance items. Use ⚡ Gen Compliance to generate.</p>
                    </div>
                  ) : (
                    <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-700">
                            <th className="text-left px-4 py-3 text-slate-400 font-medium">Requirement</th>
                            <th className="text-left px-4 py-3 text-slate-400 font-medium">Status</th>
                            <th className="text-left px-4 py-3 text-slate-400 font-medium hidden md:table-cell">Evidence</th>
                            <th className="text-left px-4 py-3 text-slate-400 font-medium hidden lg:table-cell">Owner</th>
                          </tr>
                        </thead>
                        <tbody>
                          {compliance.map((c) => (
                            <tr key={c.id} className="border-b border-slate-700/50">
                              <td className="px-4 py-3 text-white">{c.requirement}</td>
                              <td className="px-4 py-3">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${COMPLIANCE_STATUS_COLORS[c.compliance_status] ?? COMPLIANCE_STATUS_COLORS.tbc}`}>{c.compliance_status}</span>
                              </td>
                              <td className="px-4 py-3 text-slate-400 hidden md:table-cell">{c.evidence ?? '—'}</td>
                              <td className="px-4 py-3 text-slate-400 hidden lg:table-cell">{c.owner ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* RFIs */}
              {tab === 'rfis' && (
                <div className="max-w-2xl space-y-3">
                  {rfis.length === 0 ? (
                    <div className="text-center py-16">
                      <p className="text-3xl mb-2">❓</p>
                      <p className="text-slate-400 text-sm">No RFIs. Use ⚡ Gen RFIs to generate.</p>
                    </div>
                  ) : (
                    rfis.map((r) => (
                      <div key={r.id} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                        <div className="flex items-start gap-3 mb-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0 ${RFI_PRIORITY_COLORS[r.priority] ?? RFI_PRIORITY_COLORS.low}`}>{r.priority}</span>
                          <span className="text-slate-400 text-xs">{r.status}</span>
                        </div>
                        <p className="text-white text-sm">{r.question}</p>
                        {r.answer && <p className="text-slate-400 text-xs mt-2 italic">{r.answer}</p>}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {!selected && !loading && bids.length > 0 && (
          <div className="hidden lg:flex flex-1 items-center justify-center text-slate-500 text-sm">
            Select a bid to view details
          </div>
        )}
      </div>

      {/* New Bid Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-md p-6">
            <h2 className="text-white font-semibold text-lg mb-4">New Bid</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input required placeholder="Bid title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <select required value={form.opportunity_id} onChange={(e) => setForm({ ...form, opportunity_id: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option value="">Link to opportunity…</option>
                {opps.map((o) => <option key={o.id} value={o.id}>{o.title}</option>)}
              </select>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {['draft', 'review', 'submitted', 'won', 'lost'].map((s) => <option key={s}>{s}</option>)}
              </select>
              <textarea placeholder="Win themes" value={form.win_themes} onChange={(e) => setForm({ ...form, win_themes: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
              <textarea placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNew(false)} className="px-4 py-2 text-slate-300 hover:text-white text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
