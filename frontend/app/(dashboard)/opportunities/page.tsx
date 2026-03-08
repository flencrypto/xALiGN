'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { opportunitiesApi, accountsApi, Opportunity, Account, Qualification, QualificationInput } from '@/lib/api';

// Backend enum values (lowercase)
const STAGES = ['target', 'lead', 'qualified', 'bid', 'won', 'lost'];
// Display labels for each stage
const STAGE_LABELS: Record<string, string> = {
  target: 'Target', lead: 'Lead', qualified: 'Qualified',
  bid: 'Bid', won: 'Won', lost: 'Lost',
};

const STAGE_COLORS: Record<string, string> = {
  target: 'bg-surface text-text-main border-border-subtle',
  lead: 'bg-primary/20 text-primary border-primary/30',
  qualified: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  bid: 'bg-warning/20 text-warning border-warning/30',
  won: 'bg-success/20 text-success border-success/30',
  lost: 'bg-danger/20 text-danger border-danger/30',
};

const GO_NO_GO_COLORS: Record<string, string> = {
  go: 'text-success',
  conditional: 'text-warning',
  no_go: 'text-danger',
};

function scoreColor(score?: number) {
  if (score == null) return 'bg-surface text-text-muted';
  if (score >= 7) return 'bg-success/20 text-success';
  if (score >= 5) return 'bg-warning/20 text-warning';
  return 'bg-danger/20 text-danger';
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-text-muted">{label}</span>
        <span className="text-text-main">{value}/10</span>
      </div>
      <div className="h-2 bg-background rounded-full overflow-hidden">
        <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${Math.min(100, value * 10)}%` }} />
      </div>
    </div>
  );
}

interface NewOppForm {
  title: string;
  account_id: string;
  stage: string;
  estimated_value: string;
  description: string;
}

interface QualForm {
  budget_confidence: string;
  route_to_market_clarity: string;
  incumbent_lock_in_risk: string;
  procurement_timeline_realism: string;
  technical_fit: string;
  rationale: string;
}
const DEFAULT_QUAL: QualForm = {
  budget_confidence: '5', route_to_market_clarity: '5', incumbent_lock_in_risk: '5',
  procurement_timeline_realism: '5', technical_fit: '5', rationale: '',
};

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Opportunity | null>(null);
  const [qualification, setQualification] = useState<Qualification | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [showQualForm, setShowQualForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [qualifying, setQualifying] = useState(false);
  const [form, setForm] = useState<NewOppForm>({ title: '', account_id: '', stage: 'target', estimated_value: '', description: '' });
  const [qualForm, setQualForm] = useState<QualForm>(DEFAULT_QUAL);

  useEffect(() => {
    Promise.all([
      opportunitiesApi.list().catch(() => []),
      accountsApi.list().catch(() => []),
    ]).then(([o, a]) => { setOpportunities(o); setAccounts(a); }).finally(() => setLoading(false));
  }, []);

  async function selectOpp(opp: Opportunity) {
    setSelected(opp);
    setQualification(null);
    setShowQualForm(false);
    const q = await opportunitiesApi.getQualification(opp.id).catch(() => null);
    setQualification(q);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const opp = await opportunitiesApi.create({
        title: form.title,
        account_id: Number(form.account_id),
        stage: form.stage,
        estimated_value: form.estimated_value ? Number(form.estimated_value) : undefined,
        description: form.description || undefined,
      });
      setOpportunities((prev) => [...prev, opp]);
      setShowNew(false);
      setForm({ title: '', account_id: '', stage: 'target', estimated_value: '', description: '' });
    } finally {
      setSaving(false);
    }
  }

  async function runQualification(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setQualifying(true);
    try {
      const payload: QualificationInput = {
        budget_confidence: Number(qualForm.budget_confidence),
        route_to_market_clarity: Number(qualForm.route_to_market_clarity),
        incumbent_lock_in_risk: Number(qualForm.incumbent_lock_in_risk),
        procurement_timeline_realism: Number(qualForm.procurement_timeline_realism),
        technical_fit: Number(qualForm.technical_fit),
        rationale: qualForm.rationale || undefined,
      };
      const q = await opportunitiesApi.qualify(selected.id, payload);
      setQualification(q);
      setShowQualForm(false);
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
          <button onClick={() => setShowNew(true)} className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            + New Opportunity
          </button>
        }
      />
      <div className="flex flex-1 overflow-hidden">
        {/* Kanban */}
        <div className="flex-1 p-4 overflow-auto">
          {loading ? (
            <div className="flex gap-4">{STAGES.map((s) => <div key={s} className="w-52 h-40 bg-surface rounded-xl animate-pulse" />)}</div>
          ) : (
            <div className="flex gap-4 min-w-max pb-4">
              {STAGES.map((stage) => (
                <div key={stage} className="w-56 flex-shrink-0">
                  <div className="flex items-center justify-between mb-3 px-1">
                    <span className={`px-2 py-1 rounded text-xs font-semibold border ${STAGE_COLORS[stage]}`}>{STAGE_LABELS[stage] ?? stage}</span>
                    <span className="text-text-faint text-xs">{byStage(stage).length}</span>
                  </div>
                  <div className="space-y-2">
                    {byStage(stage).map((opp) => (
                      <div
                        key={opp.id}
                        onClick={() => selectOpp(opp)}
                        className={`bg-surface border rounded-xl p-3 cursor-pointer hover:border-blue-500/50 transition-colors ${selected?.id === opp.id ? 'border-blue-500' : 'border-border-subtle'}`}
                      >
                        <p className="text-text-main text-sm font-medium leading-snug mb-1">{opp.title}</p>
                        <p className="text-text-muted text-xs mb-2">{accountName(opp.account_id)}</p>
                        <div className="flex items-center justify-between">
                          {opp.estimated_value && (
                            <span className="text-success text-xs font-medium">£{opp.estimated_value.toLocaleString()}</span>
                          )}
                        </div>
                      </div>
                    ))}
                    {byStage(stage).length === 0 && (
                      <div className="border border-dashed border-border-subtle rounded-xl p-4 text-center text-text-faint text-xs">Empty</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="w-80 xl:w-96 border-l border-border-subtle bg-surface overflow-auto p-5 flex-shrink-0">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-text-main font-semibold truncate">{selected.title}</h2>
              <button onClick={() => setSelected(null)} className="text-text-muted hover:text-text-main ml-2">✕</button>
            </div>
            <div className="space-y-2 text-sm mb-5">
              <p className="text-text-muted">Account: <span className="text-text-main">{accountName(selected.account_id)}</span></p>
              <p className="text-text-muted">Stage: <span className={`px-2 py-0.5 rounded text-xs border ${STAGE_COLORS[selected.stage]}`}>{STAGE_LABELS[selected.stage] ?? selected.stage}</span></p>
              {selected.estimated_value && <p className="text-text-muted">Value: <span className="text-success font-medium">£{selected.estimated_value.toLocaleString()}</span></p>}
              {selected.description && <p className="text-text-muted text-xs">{selected.description}</p>}
            </div>

            {/* Go/No-Go panel */}
            <div className="bg-surface/50 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-text-main text-sm font-semibold">Go / No-Go Qualification</h3>
              </div>
              {qualification ? (
                <>
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`text-3xl font-bold ${scoreColor(qualification.overall_score)}`}>{qualification.overall_score}</div>
                    <div>
                      <p className="text-xs text-text-muted">Score /10</p>
                      <p className={`text-sm font-semibold ${GO_NO_GO_COLORS[qualification.go_no_go] ?? 'text-text-main'}`}>{qualification.go_no_go.replace('_', ' ').toUpperCase()}</p>
                    </div>
                  </div>
                  <ScoreBar label="Budget Confidence" value={qualification.budget_confidence} />
                  <ScoreBar label="Route to Market" value={qualification.route_to_market_clarity} />
                  <ScoreBar label="Procurement Timeline" value={qualification.procurement_timeline_realism} />
                  <ScoreBar label="Technical Fit" value={qualification.technical_fit} />
                  <ScoreBar label="Incumbent Lock-in (risk)" value={qualification.incumbent_lock_in_risk} />
                  {qualification.rationale && <p className="text-text-muted text-xs mt-2">{qualification.rationale}</p>}
                </>
              ) : (
                <p className="text-text-muted text-xs mb-3">No qualification data yet. Score this opportunity to get a Go/No-Go decision.</p>
              )}
              <button onClick={() => setShowQualForm((v) => !v)} className="w-full mt-2 bg-primary hover:bg-primary-dark text-text-main py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors">
                {qualification ? '↺ Re-score' : '▶ Run Qualification'}
              </button>
              {showQualForm && (
                <form onSubmit={runQualification} className="mt-3 space-y-2">
                  {([
                    ['budget_confidence', 'Budget Confidence (0-10)'],
                    ['route_to_market_clarity', 'Route to Market Clarity (0-10)'],
                    ['incumbent_lock_in_risk', 'Incumbent Lock-in Risk (0-10)'],
                    ['procurement_timeline_realism', 'Procurement Timeline Realism (0-10)'],
                    ['technical_fit', 'Technical Fit (0-10)'],
                  ] as [keyof QualForm, string][]).map(([key, label]) => (
                    <div key={key}>
                      <label className="text-text-muted text-xs">{label}</label>
                      <input type="number" min="0" max="10" step="0.5" required value={qualForm[key]} onChange={(e) => setQualForm({ ...qualForm, [key]: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500" />
                    </div>
                  ))}
                  <textarea placeholder="Rationale (optional)" value={qualForm.rationale} onChange={(e) => setQualForm({ ...qualForm, rationale: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-16 resize-none" />
                  <button type="submit" disabled={qualifying} className="w-full bg-success hover:bg-success/80 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors">
                    {qualifying ? 'Scoring…' : '✓ Submit Scores'}
                  </button>
                </form>
              )}
            </div>
          </div>
        )}
      </div>

      {/* New Opportunity Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-md p-6">
            <h2 className="text-text-main font-semibold text-lg mb-4">New Opportunity</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input required placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <select required value={form.account_id} onChange={(e) => setForm({ ...form, account_id: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option value="">Select account…</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
              <select value={form.stage} onChange={(e) => setForm({ ...form, stage: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {STAGES.map((s) => <option key={s} value={s}>{STAGE_LABELS[s]}</option>)}
              </select>
              <input placeholder="Estimated value (£)" type="number" value={form.estimated_value} onChange={(e) => setForm({ ...form, estimated_value: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <textarea placeholder="Description (optional)" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNew(false)} className="px-4 py-2 text-text-main hover:text-text-main text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
