'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import {
  bidsApi, opportunitiesApi, debriefApi, exportApi,
  Bid, BidDocument, ComplianceItem, RFI, Opportunity, BidDebrief,
} from '@/lib/api';


const STATUS_COLORS: Record<string, string> = {
  draft:     'bg-surface text-text-main border-border-subtle',
  review:    'bg-warning/20 text-warning border-warning/30',
  submitted: 'bg-primary/20 text-primary border-primary/30',
  won:       'bg-success/20 text-success border-success/30',
  lost:      'bg-danger/20 text-danger border-danger/30',
};

const COMPLIANCE_STATUS_COLORS: Record<string, string> = {
  yes:     'bg-success/20 text-success',
  partial: 'bg-warning/20 text-warning',
  no:      'bg-danger/20 text-danger',
  tbc:     'bg-surface text-text-muted',
};

const RFI_PRIORITY_COLORS: Record<string, string> = {
  high:   'bg-danger/20 text-danger border-danger/30',
  medium: 'bg-warning/20 text-warning border-warning/30',
  low:    'bg-surface text-text-muted border-border-subtle',
};

const OUTCOME_COLORS: Record<string, string> = {
  won:       'bg-success/20 text-success border-success/30',
  lost:      'bg-danger/20 text-danger border-danger/30',
  withdrawn: 'bg-warning/20 text-warning border-warning/30',
  no_award:  'bg-surface text-text-muted border-border-subtle',
};

type Tab = 'overview' | 'documents' | 'compliance' | 'rfis' | 'debrief';

interface NewBidForm {
  title: string; opportunity_id: string; status: string;
  win_themes: string; notes: string;
}

interface DebriefForm {
  outcome: string; our_score: string; winner_score: string;
  our_price: string; winner_price: string; client_feedback: string;
  strengths: string; weaknesses: string; winning_company: string;
  lessons_learned: string; process_improvements: string; bid_manager: string;
}
const EMPTY_DEBRIEF: DebriefForm = {
  outcome: 'lost', our_score: '', winner_score: '', our_price: '', winner_price: '',
  client_feedback: '', strengths: '', weaknesses: '', winning_company: '',
  lessons_learned: '', process_improvements: '', bid_manager: '',
};

export default function BidsPage() {
  const [bids, setBids] = useState<Bid[]>([]);
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Bid | null>(null);
  const [tab, setTab] = useState<Tab>('overview');
  const [documents, setDocuments] = useState<BidDocument[]>([]);
  const [compliance, setCompliance] = useState<ComplianceItem[]>([]);
  const [rfis, setRfis] = useState<RFI[]>([]);
  const [debrief, setDebrief] = useState<BidDebrief | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingDebrief, setSavingDebrief] = useState(false);
  const [generating, setGenerating] = useState('');
  const [debriefForm, setDebriefForm] = useState<DebriefForm>(EMPTY_DEBRIEF);
  const [form, setForm] = useState<NewBidForm>({
    title: '', opportunity_id: '', status: 'draft', win_themes: '', notes: '',
  });

  useEffect(() => {
    Promise.all([bidsApi.list().catch(() => []), opportunitiesApi.list().catch(() => [])])
      .then(([b, o]) => { setBids(b); setOpps(o); })
      .finally(() => setLoading(false));
  }, []);

  async function selectBid(bid: Bid) {
    setSelected(bid);
    setTab('overview');
    const [docs, comp, r, deb] = await Promise.all([
      bidsApi.listDocuments(bid.id).catch(() => []),
      bidsApi.listComplianceItems(bid.id).catch(() => []),
      bidsApi.listRFIs(bid.id).catch(() => []),
      debriefApi.get(bid.id).catch(() => null),
    ]);
    setDocuments(docs);
    setCompliance(comp);
    setRfis(r);
    setDebrief(deb);
    if (deb) {
      setDebriefForm({
        outcome: deb.outcome,
        our_score: deb.our_score?.toString() ?? '',
        winner_score: deb.winner_score?.toString() ?? '',
        our_price: deb.our_price?.toString() ?? '',
        winner_price: deb.winner_price?.toString() ?? '',
        client_feedback: deb.client_feedback ?? '',
        strengths: deb.strengths ?? '',
        weaknesses: deb.weaknesses ?? '',
        winning_company: deb.winning_company ?? '',
        lessons_learned: deb.lessons_learned ?? '',
        process_improvements: deb.process_improvements ?? '',
        bid_manager: deb.bid_manager ?? '',
      });
    } else {
      setDebriefForm(EMPTY_DEBRIEF);
    }
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
    } catch { /* ignore */ }
    finally { setGenerating(''); }
  }

  async function generateRFIs() {
    if (!selected) return;
    setGenerating('rfis');
    try {
      const items = await bidsApi.generateRFIs(selected.id);
      setRfis(items);
      setTab('rfis');
    } catch { /* ignore */ }
    finally { setGenerating(''); }
  }

  async function saveDebrief(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setSavingDebrief(true);
    try {
      const payload = {
        bid_id: selected.id,
        outcome: debriefForm.outcome as BidDebrief['outcome'],
        our_score:    debriefForm.our_score    ? parseFloat(debriefForm.our_score)    : undefined,
        winner_score: debriefForm.winner_score ? parseFloat(debriefForm.winner_score) : undefined,
        our_price:    debriefForm.our_price    ? parseFloat(debriefForm.our_price)    : undefined,
        winner_price: debriefForm.winner_price ? parseFloat(debriefForm.winner_price) : undefined,
        client_feedback:     debriefForm.client_feedback     || undefined,
        strengths:           debriefForm.strengths           || undefined,
        weaknesses:          debriefForm.weaknesses          || undefined,
        winning_company:     debriefForm.winning_company     || undefined,
        lessons_learned:     debriefForm.lessons_learned     || undefined,
        process_improvements:debriefForm.process_improvements|| undefined,
        bid_manager:         debriefForm.bid_manager         || undefined,
      };
      const result = debrief
        ? await debriefApi.update(selected.id, payload)
        : await debriefApi.create(selected.id, payload);
      setDebrief(result);
    } finally {
      setSavingDebrief(false);
    }
  }

  function oppTitle(id: number) { return opps.find((o) => o.id === id)?.title ?? '—'; }

  const TABS: Tab[] = ['overview', 'documents', 'compliance', 'rfis', 'debrief'];

  return (
    <>
      <Header
        title="Bid Pack Builder"
        action={
          <button
            onClick={() => setShowNew(true)}
            className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            + New Bid
          </button>
        }
      />
      <div className="flex flex-1 overflow-hidden">
        {/* List */}
        <div className={`${selected ? 'hidden lg:flex' : 'flex'} flex-col w-full lg:w-72 xl:w-80 flex-shrink-0 border-r border-border-subtle overflow-auto`}>
          <div className="p-4 flex-1">
            {loading ? (
              <div className="space-y-2">{[...Array(4)].map((_, i) => (
                <div key={i} className="h-16 bg-surface rounded-xl animate-pulse" />
              ))}</div>
            ) : bids.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-4xl mb-3">📋</p>
                <p className="text-text-muted text-sm">No bids yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {bids.map((bid) => (
                  <div
                    key={bid.id}
                    onClick={() => selectBid(bid)}
                    className={`bg-surface border rounded-xl p-4 cursor-pointer hover:border-blue-500/50 transition-colors ${selected?.id === bid.id ? 'border-blue-500' : 'border-border-subtle'}`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-text-main text-sm font-medium leading-snug">{bid.title}</p>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0 ${STATUS_COLORS[bid.status] ?? STATUS_COLORS.draft}`}>
                        {bid.status}
                      </span>
                    </div>
                    <p className="text-text-muted text-xs">{oppTitle(bid.opportunity_id)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Detail */}
        {selected && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Tabs + action bar */}
            <div className="flex flex-col border-b border-border-subtle bg-background">
              <div className="flex items-center gap-1 px-4 pt-3">
                <button onClick={() => setSelected(null)} className="text-text-muted hover:text-text-main mr-3 lg:hidden">← Back</button>
                {TABS.map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${tab === t ? 'border-primary text-primary' : 'border-transparent text-text-muted hover:text-text-main'}`}
                  >
                    {t === 'debrief' ? '📝 Debrief' : t}
                  </button>
                ))}
              </div>
              {/* Action row */}
              <div className="flex flex-wrap items-center gap-2 px-4 pb-2 pt-1">
                <button onClick={generateCompliance} disabled={!!generating}
                  className="bg-background hover:bg-surface text-text-main px-3 py-1 rounded text-xs font-medium border border-border-subtle disabled:opacity-50">
                  {generating === 'compliance' ? '⏳…' : '⚡ Gen Compliance'}
                </button>
                <button onClick={generateRFIs} disabled={!!generating}
                  className="bg-background hover:bg-surface text-text-main px-3 py-1 rounded text-xs font-medium border border-border-subtle disabled:opacity-50">
                  {generating === 'rfis' ? '⏳…' : '⚡ Gen RFIs'}
                </button>
                <span className="text-border-subtle">|</span>
                {/* Export downloads */}
                <a
                  href={exportApi.pursuitPackPdfUrl(selected.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 px-3 py-1 rounded text-xs font-medium transition-colors"
                >
                  ⬇ PDF
                </a>
                <a
                  href={exportApi.tenderResponseDocxUrl(selected.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-secondary/10 border border-secondary/30 text-secondary hover:bg-secondary/20 px-3 py-1 rounded text-xs font-medium transition-colors"
                >
                  ⬇ Word
                </a>
                <a
                  href={exportApi.complianceMatrixXlsxUrl(selected.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-success/10 border border-success/30 text-success hover:bg-success/20 px-3 py-1 rounded text-xs font-medium transition-colors"
                >
                  ⬇ Excel
                </a>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-5">
              {/* Overview */}
              {tab === 'overview' && (
                <div className="space-y-4 max-w-2xl">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-surface border border-border-subtle rounded-xl p-4">
                      <p className="text-text-muted text-xs mb-1">Status</p>
                      <span className={`px-2 py-1 rounded text-xs font-semibold border ${STATUS_COLORS[selected.status] ?? STATUS_COLORS.draft}`}>{selected.status}</span>
                    </div>
                    <div className="bg-surface border border-border-subtle rounded-xl p-4">
                      <p className="text-text-muted text-xs mb-1">Opportunity</p>
                      <p className="text-text-main text-sm">{oppTitle(selected.opportunity_id)}</p>
                    </div>
                  </div>
                  {selected.win_themes && (
                    <div className="bg-surface border border-border-subtle rounded-xl p-4">
                      <p className="text-text-muted text-xs mb-2">Win Themes</p>
                      <p className="text-text-main text-sm whitespace-pre-wrap">{selected.win_themes}</p>
                    </div>
                  )}
                  {selected.notes && (
                    <div className="bg-surface border border-border-subtle rounded-xl p-4">
                      <p className="text-text-muted text-xs mb-2">Notes</p>
                      <p className="text-text-main text-sm whitespace-pre-wrap">{selected.notes}</p>
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
                      <p className="text-text-muted text-sm">No documents uploaded.</p>
                    </div>
                  ) : (
                    <div className="bg-surface border border-border-subtle rounded-xl overflow-hidden">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-border-subtle">
                            <th className="text-left px-4 py-3 text-text-muted font-medium">Name</th>
                            <th className="text-left px-4 py-3 text-text-muted font-medium">Type</th>
                            <th className="text-left px-4 py-3 text-text-muted font-medium">Uploaded</th>
                          </tr>
                        </thead>
                        <tbody>
                          {documents.map((d) => (
                            <tr key={d.id} className="border-b border-border-subtle/50">
                              <td className="px-4 py-3 text-text-main">{d.filename}</td>
                              <td className="px-4 py-3 text-text-muted">{d.doc_type ?? '—'}</td>
                              <td className="px-4 py-3 text-text-muted">
                                {d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : '—'}
                              </td>
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
                      <p className="text-text-muted text-sm">No compliance items. Use ⚡ Gen Compliance to generate.</p>
                    </div>
                  ) : (
                    <div className="bg-surface border border-border-subtle rounded-xl overflow-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-border-subtle">
                            <th className="text-left px-4 py-3 text-text-muted font-medium">Requirement</th>
                            <th className="text-left px-4 py-3 text-text-muted font-medium">Status</th>
                            <th className="text-left px-4 py-3 text-text-muted font-medium hidden md:table-cell">Evidence</th>
                            <th className="text-left px-4 py-3 text-text-muted font-medium hidden lg:table-cell">Owner</th>
                          </tr>
                        </thead>
                        <tbody>
                          {compliance.map((c) => (
                            <tr key={c.id} className="border-b border-border-subtle/50">
                              <td className="px-4 py-3 text-text-main">{c.requirement}</td>
                              <td className="px-4 py-3">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${COMPLIANCE_STATUS_COLORS[c.compliance_status] ?? COMPLIANCE_STATUS_COLORS.tbc}`}>
                                  {c.compliance_status}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-text-muted hidden md:table-cell">{c.evidence ?? '—'}</td>
                              <td className="px-4 py-3 text-text-muted hidden lg:table-cell">{c.owner ?? '—'}</td>
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
                      <p className="text-text-muted text-sm">No RFIs. Use ⚡ Gen RFIs to generate.</p>
                    </div>
                  ) : (
                    rfis.map((r) => (
                      <div key={r.id} className="bg-surface border border-border-subtle rounded-xl p-4">
                        <div className="flex items-start gap-3 mb-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0 ${RFI_PRIORITY_COLORS[r.priority] ?? RFI_PRIORITY_COLORS.low}`}>
                            {r.priority}
                          </span>
                          <span className="text-text-muted text-xs">{r.status}</span>
                        </div>
                        <p className="text-text-main text-sm">{r.question}</p>
                        {r.answer && <p className="text-text-muted text-xs mt-2 italic">{r.answer}</p>}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Debrief */}
              {tab === 'debrief' && (
                <div className="max-w-2xl">
                  {debrief && (
                    <div className="mb-5 flex items-center gap-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold border ${OUTCOME_COLORS[debrief.outcome] ?? OUTCOME_COLORS.no_award}`}>
                        {debrief.outcome.replace('_', ' ').toUpperCase()}
                      </span>
                      {debrief.our_score != null && (
                        <span className="text-text-muted text-xs">
                          Our score: <span className="text-text-main font-mono">{debrief.our_score}</span>
                          {debrief.winner_score != null && (
                            <> · Winner: <span className="text-text-main font-mono">{debrief.winner_score}</span></>
                          )}
                        </span>
                      )}
                      {debrief.our_price != null && debrief.winner_price != null && (
                        <span className="text-text-muted text-xs font-mono">
                          Price gap: {((debrief.our_price - debrief.winner_price) / debrief.winner_price * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  )}

                  <form onSubmit={saveDebrief} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-text-muted block mb-1">Outcome *</label>
                        <select
                          value={debriefForm.outcome}
                          onChange={(e) => setDebriefForm({ ...debriefForm, outcome: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                        >
                          {['won', 'lost', 'withdrawn', 'no_award'].map((o) => (
                            <option key={o} value={o}>{o.replace('_', ' ')}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-text-muted block mb-1">Winning company</label>
                        <input
                          placeholder="Competitor name"
                          value={debriefForm.winning_company}
                          onChange={(e) => setDebriefForm({ ...debriefForm, winning_company: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-text-muted block mb-1">Our score (0–10)</label>
                        <input
                          type="number" min="0" max="10" step="0.1"
                          placeholder="e.g. 7.5"
                          value={debriefForm.our_score}
                          onChange={(e) => setDebriefForm({ ...debriefForm, our_score: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-text-muted block mb-1">Winner score (0–10)</label>
                        <input
                          type="number" min="0" max="10" step="0.1"
                          placeholder="e.g. 8.2"
                          value={debriefForm.winner_score}
                          onChange={(e) => setDebriefForm({ ...debriefForm, winner_score: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-text-muted block mb-1">Our price (£)</label>
                        <input
                          type="number" min="0"
                          placeholder="e.g. 1500000"
                          value={debriefForm.our_price}
                          onChange={(e) => setDebriefForm({ ...debriefForm, our_price: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-text-muted block mb-1">Winner price (£)</label>
                        <input
                          type="number" min="0"
                          placeholder="e.g. 1200000"
                          value={debriefForm.winner_price}
                          onChange={(e) => setDebriefForm({ ...debriefForm, winner_price: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-text-muted block mb-1">Client feedback</label>
                      <textarea
                        rows={3}
                        value={debriefForm.client_feedback}
                        onChange={(e) => setDebriefForm({ ...debriefForm, client_feedback: e.target.value })}
                        className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary resize-none"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-success block mb-1">Strengths</label>
                        <textarea
                          rows={3}
                          value={debriefForm.strengths}
                          onChange={(e) => setDebriefForm({ ...debriefForm, strengths: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary resize-none"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-danger block mb-1">Weaknesses</label>
                        <textarea
                          rows={3}
                          value={debriefForm.weaknesses}
                          onChange={(e) => setDebriefForm({ ...debriefForm, weaknesses: e.target.value })}
                          className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary resize-none"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-text-muted block mb-1">Lessons learned</label>
                      <textarea
                        rows={3}
                        value={debriefForm.lessons_learned}
                        onChange={(e) => setDebriefForm({ ...debriefForm, lessons_learned: e.target.value })}
                        className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary resize-none"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-text-muted block mb-1">Process improvements</label>
                      <textarea
                        rows={2}
                        value={debriefForm.process_improvements}
                        onChange={(e) => setDebriefForm({ ...debriefForm, process_improvements: e.target.value })}
                        className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary resize-none"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-text-muted block mb-1">Bid manager</label>
                      <input
                        value={debriefForm.bid_manager}
                        onChange={(e) => setDebriefForm({ ...debriefForm, bid_manager: e.target.value })}
                        className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
                      />
                    </div>
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={savingDebrief}
                        className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
                      >
                        {savingDebrief ? 'Saving…' : debrief ? 'Update Debrief' : 'Save Debrief'}
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
        )}

        {!selected && !loading && bids.length > 0 && (
          <div className="hidden lg:flex flex-1 items-center justify-center text-text-faint text-sm">
            Select a bid to view details
          </div>
        )}
      </div>

      {/* New Bid Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-md p-6">
            <h2 className="text-text-main font-semibold text-lg mb-4">New Bid</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input
                required placeholder="Bid title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
              <select
                required
                value={form.opportunity_id}
                onChange={(e) => setForm({ ...form, opportunity_id: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
              >
                <option value="">Link to opportunity…</option>
                {opps.map((o) => <option key={o.id} value={o.id}>{o.title}</option>)}
              </select>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
              >
                {['draft', 'review', 'submitted', 'won', 'lost'].map((s) => <option key={s}>{s}</option>)}
              </select>
              <textarea
                placeholder="Win themes"
                value={form.win_themes}
                onChange={(e) => setForm({ ...form, win_themes: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary h-20 resize-none"
              />
              <textarea
                placeholder="Notes"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary h-20 resize-none"
              />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNew(false)} className="px-4 py-2 text-text-muted hover:text-text-main text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">
                  {saving ? 'Saving…' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}


