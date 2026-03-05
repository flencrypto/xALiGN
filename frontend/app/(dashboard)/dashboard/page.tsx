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
    { label: 'Total Accounts', value: stats.totalAccounts, color: 'text-primary', bg: 'bg-primary/10', icon: '🏢' },
    { label: 'Active Opportunities', value: stats.activeOpportunities, color: 'text-success', bg: 'bg-success/10', icon: '🎯' },
    { label: 'Active Bids', value: stats.activeBids, color: 'text-warning', bg: 'bg-warning/10', icon: '📋' },
    { label: 'Win Rate', value: `${stats.winRate}%`, color: 'text-secondary', bg: 'bg-secondary/10', icon: '🏆' },
  ];

  const quickActions = [
    { href: '/accounts', label: 'Account Intelligence', desc: 'Track clients & trigger signals', icon: '🏢' },
    { href: '/opportunities', label: 'Pipeline', desc: 'Qualify & track opportunities', icon: '🎯' },
    { href: '/bids', label: 'Bid Pack Builder', desc: 'Build & manage bid packs', icon: '📋' },
    { href: '/estimating', label: 'Estimating', desc: 'Scope gap analysis & costs', icon: '📐' },
  ];

  return (
    <>
      <Header title="Command Centre" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card) => (
            <div key={card.label} className={`${card.bg} border border-border-subtle rounded-xl p-5 card-hover`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{card.icon}</span>
              </div>
              {loading ? (
                <div className="h-8 w-16 bg-surface rounded animate-pulse" />
              ) : (
                <p className={`text-3xl font-bold font-mono ${card.color}`}>{card.value}</p>
              )}
              <p className="text-text-muted text-sm mt-1">{card.label}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-text-main font-semibold mb-4 font-mono text-sm uppercase tracking-widest text-primary">[01] Recent Activity</h2>
            {loading ? (
              <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-5 bg-background rounded animate-pulse" />)}</div>
            ) : activity.length === 0 ? (
              <p className="text-text-muted text-sm">No activity yet. Start by adding an account.</p>
            ) : (
              <ul className="space-y-3">
                {activity.map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm text-text-main">
                    <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0 pulse-cyan" />
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[02] Quick Actions</h2>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((action) => (
                <Link key={action.href} href={action.href} className="bg-background hover:bg-primary/5 border border-border-subtle hover:border-primary/50 rounded-lg p-4 transition-all group card-hover">
                  <span className="text-2xl block mb-2">{action.icon}</span>
                  <p className="text-text-main text-sm font-medium group-hover:text-primary transition-colors">{action.label}</p>
                  <p className="text-text-muted text-xs mt-1">{action.desc}</p>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
