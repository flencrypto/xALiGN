'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { projectsApi, type ProjectStats } from '@/lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

const STAGE_COLORS: Record<string, string> = {
  announced: '#4fc3f7',
  planning: '#ffb74d',
  approved: '#81c784',
  construction: '#ff8a65',
  operational: '#4db6ac',
  cancelled: '#e57373',
};

export default function CapacityDashboardPage() {
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [projects, setProjects] = useState<{ company: string; capacity_mw: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, p] = await Promise.all([
          projectsApi.getStats().catch(() => null),
          projectsApi.list({ has_mw: true, limit: 200 }).catch(() => []),
        ]);
        setStats(s);
        // Aggregate by company
        const byCompany: Record<string, number> = {};
        p.forEach((proj) => {
          if (proj.company && proj.capacity_mw) {
            byCompany[proj.company] = (byCompany[proj.company] || 0) + proj.capacity_mw;
          }
        });
        const sorted = Object.entries(byCompany)
          .map(([company, capacity_mw]) => ({ company, capacity_mw }))
          .sort((a, b) => b.capacity_mw - a.capacity_mw)
          .slice(0, 15);
        setProjects(sorted);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const stageData = stats
    ? Object.entries(stats.by_stage)
        .filter(([, count]) => count > 0)
        .map(([stage, count]) => ({ stage, count }))
    : [];

  return (
    <>
      <Header title="Capacity Dashboard" />
      <div className="p-6 space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats && [
            { label: 'Total Projects', value: stats.total_projects, color: 'text-primary', bg: 'bg-primary/10' },
            { label: 'Total MW Pipeline', value: `${stats.total_capacity_mw.toLocaleString()} MW`, color: 'text-success', bg: 'bg-success/10' },
            { label: 'Under Construction', value: stats.by_stage.construction || 0, color: 'text-warning', bg: 'bg-warning/10' },
            { label: 'Operational', value: stats.by_stage.operational || 0, color: 'text-secondary', bg: 'bg-secondary/10' },
          ].map((card) => (
            <div key={card.label} className={`${card.bg} border border-border-subtle rounded-xl p-5`}>
              <p className={`text-3xl font-bold font-mono ${card.color}`}>{card.value}</p>
              <p className="text-text-muted text-sm mt-1">{card.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* MW by company chart */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[01] MW Pipeline by Company</h2>
            {loading ? (
              <div className="h-64 bg-background rounded animate-pulse" />
            ) : projects.length === 0 ? (
              <p className="text-text-muted text-sm">No MW data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={projects} layout="vertical" margin={{ left: 20, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis type="number" tick={{ fill: '#888', fontSize: 11 }} unit=" MW" />
                  <YAxis type="category" dataKey="company" tick={{ fill: '#ccc', fontSize: 11 }} width={100} />
                  <Tooltip
                    contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a3a', borderRadius: 8 }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(v: number | undefined) => [`${(v ?? 0).toLocaleString()} MW`, 'Capacity']}
                  />
                  <Bar dataKey="capacity_mw" fill="#4fc3f7" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Projects by stage chart */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[02] Projects by Stage</h2>
            {loading ? (
              <div className="h-64 bg-background rounded animate-pulse" />
            ) : stageData.length === 0 ? (
              <p className="text-text-muted text-sm">No stage data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={stageData} margin={{ left: 10, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis dataKey="stage" tick={{ fill: '#888', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#888', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a3a', borderRadius: 8 }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {stageData.map((entry) => (
                      <Cell key={entry.stage} fill={STAGE_COLORS[entry.stage] || '#888'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Top companies table */}
        {stats && stats.top_companies_by_mw.length > 0 && (
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[03] Top Companies by MW</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-subtle">
                    <th className="text-left text-text-muted font-mono text-xs pb-2">Rank</th>
                    <th className="text-left text-text-muted font-mono text-xs pb-2">Company</th>
                    <th className="text-right text-text-muted font-mono text-xs pb-2">Total MW</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.top_companies_by_mw.map((row, i) => (
                    <tr key={row.company} className="border-b border-border-subtle/50">
                      <td className="py-2.5 pr-4 text-text-faint font-mono text-xs">#{i + 1}</td>
                      <td className="py-2.5 text-text-main">{row.company}</td>
                      <td className="py-2.5 text-right text-success font-mono">{row.total_mw.toLocaleString()} MW</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
