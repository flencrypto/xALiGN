'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { projectsApi, type InfrastructureProject } from '@/lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

export default function CapexTrackerPage() {
  const [projects, setProjects] = useState<InfrastructureProject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsApi.list({ limit: 200 }).then(setProjects).catch(() => []).finally(() => setLoading(false));
  }, []);

  // Aggregate capex by company
  const byCompany = Object.entries(
    projects.reduce<Record<string, number>>((acc, p) => {
      if (p.company && p.capex_millions) {
        acc[p.company] = (acc[p.company] || 0) + p.capex_millions;
      }
      return acc;
    }, {})
  )
    .map(([company, capex]) => ({ company, capex }))
    .sort((a, b) => b.capex - a.capex)
    .slice(0, 12);

  // Aggregate capex by type
  const byType = Object.entries(
    projects.reduce<Record<string, number>>((acc, p) => {
      if (p.project_type && p.capex_millions) {
        acc[p.project_type] = (acc[p.project_type] || 0) + p.capex_millions;
      }
      return acc;
    }, {})
  ).map(([type, capex]) => ({ type: type.replace('_', ' '), capex }));

  const totalCapex = projects.reduce((a, p) => a + (p.capex_millions || 0), 0);
  const projectsWithCapex = projects.filter((p) => p.capex_millions);
  const avgCapex = projectsWithCapex.length > 0 ? totalCapex / projectsWithCapex.length : 0;
  const largestDeal = Math.max(...projects.map((p) => p.capex_millions || 0), 0);

  return (
    <>
      <Header title="Capex Tracker" />
      <div className="p-6 space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Capex Tracked', value: `£${totalCapex.toLocaleString()}M`, color: 'text-primary', bg: 'bg-primary/10' },
            { label: 'Projects with Capex', value: projectsWithCapex.length, color: 'text-success', bg: 'bg-success/10' },
            { label: 'Average Deal Size', value: `£${Math.round(avgCapex).toLocaleString()}M`, color: 'text-warning', bg: 'bg-warning/10' },
            { label: 'Largest Single Deal', value: `£${largestDeal.toLocaleString()}M`, color: 'text-secondary', bg: 'bg-secondary/10' },
          ].map((card) => (
            <div key={card.label} className={`${card.bg} border border-border-subtle rounded-xl p-5`}>
              <p className={`text-3xl font-bold font-mono ${card.color}`}>{loading ? '…' : card.value}</p>
              <p className="text-text-muted text-sm mt-1">{card.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Capex by company */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[01] Investment by Company</h2>
            {loading ? (
              <div className="h-64 bg-background rounded animate-pulse" />
            ) : byCompany.length === 0 ? (
              <p className="text-text-muted text-sm">No capex data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={byCompany} layout="vertical" margin={{ left: 20, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis type="number" tick={{ fill: '#888', fontSize: 11 }} unit="M" />
                  <YAxis type="category" dataKey="company" tick={{ fill: '#ccc', fontSize: 11 }} width={100} />
                  <Tooltip
                    contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a3a', borderRadius: 8 }}
                    formatter={(v: number | undefined) => [`£${(v ?? 0).toLocaleString()}M`, 'Capex']}
                  />
                  <Bar dataKey="capex" fill="#ffb74d" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Capex by type */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[02] Investment by Project Type</h2>
            {loading ? (
              <div className="h-64 bg-background rounded animate-pulse" />
            ) : byType.length === 0 ? (
              <p className="text-text-muted text-sm">No data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={byType} margin={{ left: 10, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis dataKey="type" tick={{ fill: '#888', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#888', fontSize: 11 }} unit="M" />
                  <Tooltip
                    contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a3a', borderRadius: 8 }}
                    formatter={(v: number | undefined) => [`£${(v ?? 0).toLocaleString()}M`, 'Capex']}
                  />
                  <Bar dataKey="capex" fill="#81c784" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Project list with capex */}
        <div className="bg-surface border border-border-subtle rounded-xl p-5">
          <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[03] Projects by Investment</h2>
          {loading ? (
            <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i} className="h-10 bg-background rounded animate-pulse" />)}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-subtle">
                    <th className="text-left text-text-muted font-mono text-xs pb-2">Project</th>
                    <th className="text-left text-text-muted font-mono text-xs pb-2">Company</th>
                    <th className="text-left text-text-muted font-mono text-xs pb-2">Location</th>
                    <th className="text-right text-text-muted font-mono text-xs pb-2">Capex</th>
                    <th className="text-right text-text-muted font-mono text-xs pb-2">MW</th>
                  </tr>
                </thead>
                <tbody>
                  {projects
                    .filter((p) => p.capex_millions)
                    .sort((a, b) => (b.capex_millions || 0) - (a.capex_millions || 0))
                    .slice(0, 20)
                    .map((p) => (
                      <tr key={p.id} className="border-b border-border-subtle/50 hover:bg-background/50 transition-colors">
                        <td className="py-2.5 pr-4 text-text-main max-w-xs truncate">{p.name}</td>
                        <td className="py-2.5 pr-4 text-text-muted">{p.company || '—'}</td>
                        <td className="py-2.5 pr-4 text-text-muted">{p.location || '—'}</td>
                        <td className="py-2.5 text-right text-warning font-mono">£{p.capex_millions?.toLocaleString()}M</td>
                        <td className="py-2.5 text-right text-success font-mono">{p.capacity_mw ? `${p.capacity_mw} MW` : '—'}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
