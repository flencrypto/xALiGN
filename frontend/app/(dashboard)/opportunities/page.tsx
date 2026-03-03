'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { opportunitiesApi, accountsApi, Opportunity, Account, Qualification } from '@/lib/api';

const STAGES = ['Target', 'Lead', 'Qualified', 'Bid', 'Won', 'Lost'];

const STAGE_COLORS: Record<string, string> = {
  Target: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  Lead: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  Qualified: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  Bid: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  Won: 'bg-green-500/20 text-green-300 border-green-500/30',
  Lost: 'bg-red-500/20 text-red-300 border-red-500/30',
};

function scoreColor(score?: number) {
  if (!score) return 'bg-slate-500/20 text-slate-400';
  if (score >= 70) return 'bg-green-500/20 text-green-400';
  if (score >= 40) return 'bg-yellow-500/20 text-yellow-400';
  return 'bg-red-500/20 text-red-400';
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300">{value}</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  );
}

interface NewOppForm {
  title: string;
  account_id: string;
  stage: string;
  estimated_value: string;
  probability: string;
  notes: string;
}

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Opportunity | null>(null);
  const [qualification, setQualification] = useState<Qualification | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [qualifying, setQualifying] = useState(false);
  const [form, setForm] = useState<NewOppForm>({ title: '', account_id: '', stage: 'Target', estimated_value: '', probability: '', notes: '' });

  useEffect(() => {
    Promise.all([
      opportunitiesApi.list().catch(() => []),
      accountsApi.list().catch(() => []),
    ]).then(([o, a]) => { setOpportunities(o); setAccounts(a); }).finally(() => setLoading(false));
  }, []);

  async function selectOpp(opp: Opportunity) {
    setSelected(opp);
    setQualification(null);
    const q = await opportunitiesApi.getQualification(opp.id).catch(() => null);
    setQualification(q);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const opp = await opportunitiesApi.create({
        ...form,
        account_id: Number(form.account_id),
        estimated_value: form.estimated_value ? Number(form.estimated_value) : undefined,
        probability: form.probability ? Number(form.probability) : undefined,
      });
      setOpportunities((prev) => [...prev, opp]);
      setShowNew(false);
      setForm({ title: '', account_id: '', stage: 'Target', estimated_value: '', probability: '', notes: '' });
    } finally {
      setSaving(false);
    }
  }

  async function runQualification() {
    if (!selected) return;
    setQualifying(true);
    try {
      const q = await opportunitiesApi.qualify(selected.id, {});
      setQualification(q);
    } finally {
      setQualifying(false);
    }
  }

  function accountName(id: number) {
    return accounts.find((a) => a.id === id)?.name ?? '—';
  }

  const byStage = (stage: string) => opportunities.filter((o) => o.stage === stage);

  return (
    <>
      <Header
        title="Opportunity Pipeline"
        action={
          <button onClick={() => setShowNew(true)} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            + New Opportunity
          </button>
        }
      />
      <div className="flex flex-1 overflow-hidden">
        {/* Kanban */}
        <div className="flex-1 p-4 overflow-auto">
          {loading ? (
            <div className="flex gap-4">{STAGES.map((s) => <div key={s} className="w-52 h-40 bg-slate-800 rounded-xl animate-pulse" />)}</div>
          ) : (
            <div className="flex gap-4 min-w-max pb-4">
              {STAGES.map((stage) => (
                <div key={stage} className="w-56 flex-shrink-0">
                  <div className="flex items-center justify-between mb-3 px-1">
                    <span className={`px-2 py-1 rounded text-xs font-semibold border ${STAGE_COLORS[stage]}`}>{stage}</span>
                    <span className="text-slate-500 text-xs">{byStage(stage).length}</span>
                  </div>
                  <div className="space-y-2">
                    {byStage(stage).map((opp) => (
                      <div
                        key={opp.id}
                        onClick={() => selectOpp(opp)}
                        className={`bg-slate-800 border rounded-xl p-3 cursor-pointer hover:border-blue-500/50 transition-colors ${selected?.id === opp.id ? 'border-blue-500' : 'border-slate-700'}`}
                      >
                        <p className="text-white text-sm font-medium leading-snug mb-1">{opp.title}</p>
                        <p className="text-slate-400 text-xs mb-2">{accountName(opp.account_id)}</p>
                        <div className="flex items-center justify-between">
                          {opp.estimated_value && (
                            <span className="text-green-400 text-xs font-medium">£{opp.estimated_value.toLocaleString()}</span>
                          )}
                          {opp.qualification_score != null && (
                            <span className={`ml-auto px-2 py-0.5 rounded text-xs font-bold ${scoreColor(opp.qualification_score)}`}>
                              {opp.qualification_score}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                    {byStage(stage).length === 0 && (
                      <div className="border border-dashed border-slate-700 rounded-xl p-4 text-center text-slate-600 text-xs">Empty</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="w-80 xl:w-96 border-l border-slate-700 bg-slate-800 overflow-auto p-5 flex-shrink-0">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-semibold truncate">{selected.title}</h2>
              <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-white ml-2">✕</button>
            </div>
            <div className="space-y-2 text-sm mb-5">
              <p className="text-slate-400">Account: <span className="text-slate-200">{accountName(selected.account_id)}</span></p>
              <p className="text-slate-400">Stage: <span className={`px-2 py-0.5 rounded text-xs border ${STAGE_COLORS[selected.stage]}`}>{selected.stage}</span></p>
              {selected.estimated_value && <p className="text-slate-400">Value: <span className="text-green-400 font-medium">£{selected.estimated_value.toLocaleString()}</span></p>}
              {selected.probability != null && <p className="text-slate-400">Probability: <span className="text-slate-200">{selected.probability}%</span></p>}
            </div>

            {/* Go/No-Go panel */}
            <div className="bg-slate-700/50 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white text-sm font-semibold">Go / No-Go Qualification</h3>
              </div>
              {qualification ? (
                <>
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`text-3xl font-bold ${scoreColor(qualification.score)}`}>{qualification.score}</div>
                    <div>
                      <p className="text-xs text-slate-400">Score</p>
                      {qualification.recommendation && <p className={`text-sm font-semibold ${qualification.score >= 60 ? 'text-green-400' : 'text-red-400'}`}>{qualification.recommendation}</p>}
                    </div>
                  </div>
                  {qualification.criteria && Object.entries(qualification.criteria).map(([k, v]) => (
                    <ScoreBar key={k} label={k} value={Number(v)} />
                  ))}
                </>
              ) : (
                <p className="text-slate-400 text-xs mb-3">No qualification data yet. Run the qualification to get a Go/No-Go score.</p>
              )}
              <button onClick={runQualification} disabled={qualifying} className="w-full mt-2 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors">
                {qualifying ? 'Running…' : '▶ Run Qualification'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* New Opportunity Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-md p-6">
            <h2 className="text-white font-semibold text-lg mb-4">New Opportunity</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input required placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <select required value={form.account_id} onChange={(e) => setForm({ ...form, account_id: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option value="">Select account…</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
              <select value={form.stage} onChange={(e) => setForm({ ...form, stage: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {STAGES.map((s) => <option key={s}>{s}</option>)}
              </select>
              <input placeholder="Estimated value (£)" type="number" value={form.estimated_value} onChange={(e) => setForm({ ...form, estimated_value: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Probability (%)" type="number" min="0" max="100" value={form.probability} onChange={(e) => setForm({ ...form, probability: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
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
