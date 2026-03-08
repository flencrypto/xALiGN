'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { estimatingApi, bidsApi, EstimatingProject, ScopeGap, ChecklistItem, Bid } from '@/lib/api';

// Values must match backend ScopeGapCategory enum exactly
const SCOPE_CATEGORIES: { value: string; label: string }[] = [
  { value: 'enabling_works',  label: 'Enabling Works' },
  { value: 'temp_power',      label: 'Temporary Power' },
  { value: 'temp_cooling',    label: 'Temporary Cooling' },
  { value: 'weekend_working', label: 'Weekend Working' },
  { value: 'commissioning',   label: 'Commissioning' },
  { value: 'client_kit',      label: 'Client Kit' },
  { value: 'logistics',       label: 'Logistics' },
  { value: 'permits',         label: 'Permits' },
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

interface NewProjectForm { bid_id: string; project_type: string; tier_level: string; total_budget: string; }

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
  const [form, setForm] = useState<NewProjectForm>({ bid_id: '', project_type: 'live_refurb', tier_level: 'Tier III', total_budget: '' });

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
    setGapScore(report?.risk_score ?? null);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.bid_id) return;
    setSaving(true);
    try {
      const proj = await estimatingApi.create({
        bid_id: Number(form.bid_id),
        project_type: form.project_type,
        tier_level: form.tier_level || undefined,
        total_budget: form.total_budget ? Number(form.total_budget) : undefined,
      });
      setProjects((prev) => [...prev, proj]);
      setShowNew(false);
      setForm({ bid_id: '', project_type: 'live_refurb', tier_level: 'Tier III', total_budget: '' });
    } finally {
      setSaving(false);
    }
  }

  function bidTitle(id?: number) { return id ? bids.find((b) => b.id === id)?.title ?? '—' : '—'; }

  function gapsByCategory(catValue: string) { return scopeGaps.filter((g) => g.category === catValue); }

  function categoryStatus(catValue: string) {
    const gaps = gapsByCategory(catValue);
    if (gaps.length === 0) return 'Clear';
    if (gaps.some((g) => !g.identified)) return 'Red';
    if (gaps.some((g) => !g.owner_agreed || !g.included_in_price)) return 'Amber';
    return 'Complete';
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
                  <p className="text-text-main text-sm font-medium mb-1">{proj.project_type}</p>
                  <div className="flex items-center justify-between">
                    <p className="text-text-muted text-xs">{proj.project_type} · {proj.tier_level ?? '—'}</p>
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
              <h2 className="text-text-main font-semibold text-xl">{selected.project_type}</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">
              {/* Project info */}
              <div className="bg-surface border border-border-subtle rounded-xl p-4 space-y-2 text-sm">
                <p className="text-text-muted text-xs font-semibold uppercase tracking-wide mb-3">Project Info</p>
                <p className="text-text-muted">Type: <span className="text-text-main">{selected.project_type ?? '—'}</span></p>
                <p className="text-text-muted">Tier: <span className="text-text-main">{selected.tier_level ?? '—'}</span></p>
                <p className="text-text-muted">Budget: <span className="text-success font-medium">{selected.total_budget ? `£${selected.total_budget.toLocaleString()}` : '—'}</span></p>
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
                        <span className={`w-4 h-4 rounded flex-shrink-0 flex items-center justify-center ${item.completed ? 'bg-success/20 text-success' : 'bg-background text-text-faint'}`}>
                          {item.completed ? '✓' : '○'}
                        </span>
                        <span className={item.completed ? 'text-text-main line-through' : 'text-text-main'}>{item.item}</span>
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
                  {SCOPE_CATEGORIES.map(({ value, label }) => {
                    const status = categoryStatus(value);
                    const gaps = gapsByCategory(value);
                    return (
                      <tr key={value} className="border-b border-border-subtle/50">
                        <td className="px-4 py-3 text-text-main">{label}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className={`w-3 h-3 rounded-full ${trafficLight(status)}`} />
                            <span className="text-text-main text-xs">{status}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-text-muted text-xs hidden md:table-cell">
                          {gaps.length > 0 ? gaps.map((g) => g.description).join(', ') : 'None identified'}
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
                      <span className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${trafficLight(gap.identified ? (gap.owner_agreed ? 'Complete' : 'Partial') : 'Red')}`} />
                      <div>
                        <p className="text-text-main text-sm">{gap.description}</p>
                        <p className="text-text-muted text-xs">{gap.category} · Identified: {gap.identified ? 'Yes' : 'No'} · In price: {gap.included_in_price ? 'Yes' : 'No'}</p>
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
              <select required value={form.bid_id} onChange={(e) => setForm({ ...form, bid_id: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option value="">Select bid to link…</option>
                {bids.map((b) => <option key={b.id} value={b.id}>{b.title}</option>)}
              </select>
              <select value={form.project_type} onChange={(e) => setForm({ ...form, project_type: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {([['live_refurb', 'Live Refurb'], ['brownfield', 'Brownfield'], ['new_build', 'New Build']] as const).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
              <select value={form.tier_level} onChange={(e) => setForm({ ...form, tier_level: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {['Tier I', 'Tier II', 'Tier III', 'Tier IV'].map((t) => <option key={t}>{t}</option>)}
              </select>
              <input placeholder="Total Budget (£)" type="number" value={form.total_budget} onChange={(e) => setForm({ ...form, total_budget: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
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
