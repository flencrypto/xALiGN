'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import { accountsApi, opportunitiesApi, bidsApi } from '@/lib/api';

interface Stats {
  totalAccounts: number;
  activeOpportunities: number;
  activeBids: number;
  winRate: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ totalAccounts: 0, activeOpportunities: 0, activeBids: 0, winRate: 0 });
  const [loading, setLoading] = useState(true);
  const [activity, setActivity] = useState<string[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [accounts, opps, bids] = await Promise.all([
          accountsApi.list().catch(() => []),
          opportunitiesApi.list().catch(() => []),
          bidsApi.list().catch(() => []),
        ]);
        const activeOpps = opps.filter((o) => !['Won', 'Lost'].includes(o.stage));
        const activeBids = bids.filter((b) => !['Won', 'Lost'].includes(b.status));
        const won = bids.filter((b) => b.status === 'Won').length;
        const total = bids.filter((b) => ['Won', 'Lost'].includes(b.status)).length;
        const winRate = total > 0 ? Math.round((won / total) * 100) : 0;
        setStats({ totalAccounts: accounts.length, activeOpportunities: activeOpps.length, activeBids: activeBids.length, winRate });
        const lines: string[] = [];
        accounts.slice(0, 2).forEach((a) => lines.push(`Account "${a.name}" added`));
        opps.slice(0, 2).forEach((o) => lines.push(`Opportunity "${o.title}" — ${o.stage}`));
        bids.slice(0, 2).forEach((b) => lines.push(`Bid "${b.title}" — ${b.status}`));
        setActivity(lines.slice(0, 6));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const statCards = [
    { label: 'Total Accounts', value: stats.totalAccounts, color: 'text-blue-400', bg: 'bg-blue-500/10', icon: '🏢' },
    { label: 'Active Opportunities', value: stats.activeOpportunities, color: 'text-green-400', bg: 'bg-green-500/10', icon: '🎯' },
    { label: 'Active Bids', value: stats.activeBids, color: 'text-yellow-400', bg: 'bg-yellow-500/10', icon: '📋' },
    { label: 'Win Rate', value: `${stats.winRate}%`, color: 'text-purple-400', bg: 'bg-purple-500/10', icon: '🏆' },
  ];

  const quickActions = [
    { href: '/accounts', label: 'Account Intelligence', desc: 'Track clients & trigger signals', icon: '🏢' },
    { href: '/opportunities', label: 'Pipeline', desc: 'Qualify & track opportunities', icon: '🎯' },
    { href: '/bids', label: 'Bid Pack Builder', desc: 'Build & manage bid packs', icon: '📋' },
    { href: '/estimating', label: 'Estimating', desc: 'Scope gap analysis & costs', icon: '📐' },
  ];

  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card) => (
            <div key={card.label} className={`${card.bg} border border-slate-700 rounded-xl p-5`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{card.icon}</span>
              </div>
              {loading ? (
                <div className="h-8 w-16 bg-slate-700 rounded animate-pulse" />
              ) : (
                <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
              )}
              <p className="text-slate-400 text-sm mt-1">{card.label}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
            <h2 className="text-white font-semibold mb-4">Recent Activity</h2>
            {loading ? (
              <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-5 bg-slate-700 rounded animate-pulse" />)}</div>
            ) : activity.length === 0 ? (
              <p className="text-slate-400 text-sm">No activity yet. Start by adding an account.</p>
            ) : (
              <ul className="space-y-3">
                {activity.map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm text-slate-300">
                    <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
            <h2 className="text-white font-semibold mb-4">Quick Actions</h2>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((action) => (
                <Link key={action.href} href={action.href} className="bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-lg p-4 transition-colors group">
                  <span className="text-2xl block mb-2">{action.icon}</span>
                  <p className="text-white text-sm font-medium group-hover:text-blue-400 transition-colors">{action.label}</p>
                  <p className="text-slate-400 text-xs mt-1">{action.desc}</p>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
