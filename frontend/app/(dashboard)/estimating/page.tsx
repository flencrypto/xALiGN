'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { estimatingApi, bidsApi, EstimatingProject, ScopeGap, ChecklistItem, Bid } from '@/lib/api';

const SCOPE_CATEGORIES = [
  'Power Distribution',
  'Cooling Infrastructure',
  'Structural Works',
  'Network Cabling',
  'Security & Access',
  'Fire Suppression',
  'Monitoring & DCIM',
  'Commissioning',
];

function trafficLight(status: string) {
  if (status === 'Clear' || status === 'Complete') return 'bg-success';
  if (status === 'Amber' || status === 'Partial') return 'bg-warning';
  return 'bg-danger';
}

function scoreColor(score?: number) {
  if (!score) return 'text-text-muted';
  if (score <= 3) return 'text-success';
  if (score <= 6) return 'text-warning';
  return 'text-danger';
}

function scoreBg(score?: number) {
  if (!score) return 'bg-surface';
  if (score <= 3) return 'bg-success/10 border-success/30';
  if (score <= 6) return 'bg-warning/10 border-warning/30';
  return 'bg-danger/10 border-danger/30';
}

interface NewProjectForm { title: string; bid_id: string; project_type: string; tier: string; budget: string; notes: string; }

export default function EstimatingPage() {
  const [projects, setProjects] = useState<EstimatingProject[]>([]);
  const [bids, setBids] = useState<Bid[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<EstimatingProject | null>(null);
  const [scopeGaps, setScopeGaps] = useState<ScopeGap[]>([]);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [gapScore, setGapScore] = useState<number | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<NewProjectForm>({ title: '', bid_id: '', project_type: 'Refurb', tier: 'Tier III', budget: '', notes: '' });

  useEffect(() => {
    Promise.all([estimatingApi.list().catch(() => []), bidsApi.list().catch(() => [])])
      .then(([p, b]) => { setProjects(p); setBids(b); })
      .finally(() => setLoading(false));
  }, []);

  async function selectProject(proj: EstimatingProject) {
    setSelected(proj);
    const [gaps, checks, report] = await Promise.all([
      estimatingApi.listScopeGaps(proj.id).catch(() => []),
      estimatingApi.listChecklist(proj.id).catch(() => []),
      estimatingApi.getScopeGapReport(proj.id).catch(() => null),
    ]);
    setScopeGaps(gaps);
    setChecklist(checks);
    setGapScore(report?.score ?? proj.scope_gap_score ?? null);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const proj = await estimatingApi.create({ ...form, bid_id: form.bid_id ? Number(form.bid_id) : undefined, budget: form.budget ? Number(form.budget) : undefined });
      setProjects((prev) => [...prev, proj]);
      setShowNew(false);
      setForm({ title: '', bid_id: '', project_type: 'Refurb', tier: 'Tier III', budget: '', notes: '' });
    } finally {
      setSaving(false);
    }
  }

  function bidTitle(id?: number) { return id ? bids.find((b) => b.id === id)?.title ?? '—' : '—'; }

  function gapsByCategory(cat: string) { return scopeGaps.filter((g) => g.category === cat); }

  function categoryStatus(cat: string) {
    const gaps = gapsByCategory(cat);
    if (gaps.length === 0) return 'Clear';
    if (gaps.some((g) => g.risk_level === 'High')) return 'Red';
    if (gaps.some((g) => g.risk_level === 'Medium')) return 'Amber';
    return 'Clear';
  }

  return (
    <>
      <Header
        title="Estimating & Scope Gap"
        action={
          <button onClick={() => setShowNew(true)} className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            + New Project
          </button>
        }
      />
      <div className="flex flex-1 overflow-hidden">
        {/* List */}
        <div className={`${selected ? 'hidden lg:flex' : 'flex'} flex-col w-full lg:w-72 xl:w-80 flex-shrink-0 border-r border-border-subtle overflow-auto p-4`}>
          {loading ? (
            <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-surface rounded-xl animate-pulse" />)}</div>
          ) : projects.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-4xl mb-3">📐</p>
              <p className="text-text-muted text-sm">No estimating projects yet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {projects.map((proj) => (
                <div
                  key={proj.id}
                  onClick={() => selectProject(proj)}
                  className={`bg-surface border rounded-xl p-4 cursor-pointer hover:border-blue-500/50 transition-colors ${selected?.id === proj.id ? 'border-blue-500' : 'border-border-subtle'}`}
                >
                  <p className="text-text-main text-sm font-medium mb-1">{proj.title}</p>
                  <div className="flex items-center justify-between">
                    <p className="text-text-muted text-xs">{proj.project_type} · {proj.tier}</p>
                    {proj.scope_gap_score != null && (
                      <span className={`text-xs font-bold ${scoreColor(proj.scope_gap_score)}`}>Risk: {proj.scope_gap_score}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail */}
        {selected && (
          <div className="flex-1 overflow-auto p-5">
            <div className="flex items-center gap-3 mb-6">
              <button onClick={() => setSelected(null)} className="text-text-muted hover:text-text-main lg:hidden">← Back</button>
              <h2 className="text-text-main font-semibold text-xl">{selected.title}</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">
              {/* Project info */}
              <div className="bg-surface border border-border-subtle rounded-xl p-4 space-y-2 text-sm">
                <p className="text-text-muted text-xs font-semibold uppercase tracking-wide mb-3">Project Info</p>
                <p className="text-text-muted">Type: <span className="text-text-main">{selected.project_type ?? '—'}</span></p>
                <p className="text-text-muted">Tier: <span className="text-text-main">{selected.tier ?? '—'}</span></p>
                <p className="text-text-muted">Budget: <span className="text-success font-medium">{selected.budget ? `£${selected.budget.toLocaleString()}` : '—'}</span></p>
                <p className="text-text-muted">Bid: <span className="text-text-main">{bidTitle(selected.bid_id)}</span></p>
              </div>

              {/* Scope gap score */}
              <div className={`border rounded-xl p-4 flex flex-col items-center justify-center ${scoreBg(gapScore ?? undefined)}`}>
                <p className="text-text-muted text-xs font-semibold uppercase tracking-wide mb-2">Scope Gap Risk Score</p>
                <p className={`text-6xl font-black ${scoreColor(gapScore ?? undefined)}`}>{gapScore ?? '—'}</p>
                <p className="text-text-faint text-xs mt-2">
                  {gapScore == null ? 'Not calculated'
                    : gapScore <= 3 ? 'Low Risk'
                    : gapScore <= 6 ? 'Medium Risk'
                    : 'High Risk'}
                </p>
              </div>

              {/* Checklist summary */}
              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <p className="text-text-muted text-xs font-semibold uppercase tracking-wide mb-3">Checklist</p>
                {checklist.length === 0 ? (
                  <p className="text-text-faint text-sm">No items.</p>
                ) : (
                  <div className="space-y-2">
                    {checklist.slice(0, 6).map((item) => (
                      <div key={item.id} className="flex items-center gap-2 text-xs">
                        <span className={`w-4 h-4 rounded flex-shrink-0 flex items-center justify-center ${item.checked ? 'bg-success/20 text-success' : 'bg-background text-text-faint'}`}>
                          {item.checked ? '✓' : '○'}
                        </span>
                        <span className={item.checked ? 'text-text-main line-through' : 'text-text-main'}>{item.item}</span>
                      </div>
                    ))}
                    {checklist.length > 6 && <p className="text-text-faint text-xs">+{checklist.length - 6} more</p>}
                  </div>
                )}
              </div>
            </div>

            {/* Scope gap categories */}
            <div className="bg-surface border border-border-subtle rounded-xl overflow-hidden mb-5">
              <div className="px-4 py-3 border-b border-border-subtle">
                <h3 className="text-text-main font-semibold text-sm">Scope Gap Analysis</h3>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-subtle">
                    <th className="text-left px-4 py-2 text-text-muted font-medium">Category</th>
                    <th className="text-left px-4 py-2 text-text-muted font-medium">Status</th>
                    <th className="text-left px-4 py-2 text-text-muted font-medium hidden md:table-cell">Gaps</th>
                  </tr>
                </thead>
                <tbody>
                  {SCOPE_CATEGORIES.map((cat) => {
                    const status = categoryStatus(cat);
                    const gaps = gapsByCategory(cat);
                    return (
                      <tr key={cat} className="border-b border-border-subtle/50">
                        <td className="px-4 py-3 text-text-main">{cat}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className={`w-3 h-3 rounded-full ${trafficLight(status)}`} />
                            <span className="text-text-main text-xs">{status}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-text-muted text-xs hidden md:table-cell">
                          {gaps.length > 0 ? gaps.map((g) => g.item).join(', ') : 'None identified'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Full scope gaps */}
            {scopeGaps.length > 0 && (
              <div className="bg-surface border border-border-subtle rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-border-subtle">
                  <h3 className="text-text-main font-semibold text-sm">Identified Scope Gaps ({scopeGaps.length})</h3>
                </div>
                <div className="divide-y divide-slate-700/50">
                  {scopeGaps.map((gap) => (
                    <div key={gap.id} className="px-4 py-3 flex items-start gap-3">
                      <span className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${trafficLight(gap.risk_level ?? '')}`} />
                      <div>
                        <p className="text-text-main text-sm">{gap.item}</p>
                        <p className="text-text-muted text-xs">{gap.category} · Risk: {gap.risk_level ?? 'Unknown'}</p>
                        {gap.notes && <p className="text-text-faint text-xs mt-1">{gap.notes}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!selected && !loading && projects.length > 0 && (
          <div className="hidden lg:flex flex-1 items-center justify-center text-text-faint text-sm">
            Select a project to view details
          </div>
        )}
      </div>

      {/* New Project Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-md p-6">
            <h2 className="text-text-main font-semibold text-lg mb-4">New Estimating Project</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input required placeholder="Project title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <select value={form.bid_id} onChange={(e) => setForm({ ...form, bid_id: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option value="">Link to bid (optional)…</option>
                {bids.map((b) => <option key={b.id} value={b.id}>{b.title}</option>)}
              </select>
              <select value={form.project_type} onChange={(e) => setForm({ ...form, project_type: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {['Refurb', 'New Build', 'Extension', 'Fit-Out'].map((t) => <option key={t}>{t}</option>)}
              </select>
              <select value={form.tier} onChange={(e) => setForm({ ...form, tier: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {['Tier I', 'Tier II', 'Tier III', 'Tier IV'].map((t) => <option key={t}>{t}</option>)}
              </select>
              <input placeholder="Budget (£)" type="number" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <textarea placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
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
