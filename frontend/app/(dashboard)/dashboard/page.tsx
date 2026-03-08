'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import { accountsApi, opportunitiesApi, bidsApi } from '@/lib/api';
import {
  Building2,
  Target,
  FileStack,
  Trophy,
  ArrowUpRight,
  Calculator,
  Activity,
  Zap,
  TrendingUp,
  Clock,
} from 'lucide-react';

interface Stats {
  totalAccounts: number;
  activeOpportunities: number;
  activeBids: number;
  winRate: number;
}

function AnimatedNumber({ value, loading }: { value: number | string; loading: boolean }) {
  if (loading) return <div className="h-9 w-20 rounded-lg shimmer" />;
  return <span className="tabular-nums">{value}</span>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ totalAccounts: 0, activeOpportunities: 0, activeBids: 0, winRate: 0 });
  const [loading, setLoading] = useState(true);
  const [activity, setActivity] = useState<{ text: string; type: string; time: string }[]>([]);

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

        const lines: { text: string; type: string; time: string }[] = [];
        accounts.slice(0, 3).forEach((a) => lines.push({ text: `Account "${a.name}" added`, type: 'account', time: 'Recent' }));
        opps.slice(0, 3).forEach((o) => lines.push({ text: `Opportunity "${o.title}" — ${o.stage}`, type: 'opportunity', time: 'Recent' }));
        bids.slice(0, 2).forEach((b) => lines.push({ text: `Bid "${b.title}" — ${b.status}`, type: 'bid', time: 'Recent' }));
        setActivity(lines.slice(0, 8));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const statCards = [
    { label: 'Total Accounts', value: stats.totalAccounts, Icon: Building2, gradient: 'from-cyan-500/20 to-cyan-500/5', accent: 'text-color-primary', ring: 'ring-cyan-500/20' },
    { label: 'Active Opportunities', value: stats.activeOpportunities, Icon: Target, gradient: 'from-green-500/20 to-green-500/5', accent: 'text-color-success', ring: 'ring-green-500/20' },
    { label: 'Active Bids', value: stats.activeBids, Icon: FileStack, gradient: 'from-amber-500/20 to-amber-500/5', accent: 'text-color-warning', ring: 'ring-amber-500/20' },
    { label: 'Win Rate', value: `${stats.winRate}%`, Icon: Trophy, gradient: 'from-indigo-500/20 to-indigo-500/5', accent: 'text-color-secondary', ring: 'ring-indigo-500/20' },
  ];

  const quickActions = [
    { href: '/accounts', label: 'Account Intelligence', desc: 'Track clients & trigger signals', Icon: Building2, color: 'group-hover:text-cyan-400' },
    { href: '/opportunities', label: 'Pipeline', desc: 'Qualify & track opportunities', Icon: Target, color: 'group-hover:text-green-400' },
    { href: '/bids', label: 'Bid Pack Builder', desc: 'Build & manage bid packs', Icon: FileStack, color: 'group-hover:text-amber-400' },
    { href: '/estimating', label: 'Estimating', desc: 'Scope gap analysis & costs', Icon: Calculator, color: 'group-hover:text-indigo-400' },
    { href: '/intel', label: 'Intelligence Hub', desc: 'Market insights & analysis', Icon: TrendingUp, color: 'group-hover:text-purple-400' },
    { href: '/tenders', label: 'Tenders', desc: 'Track & respond to tenders', Icon: Zap, color: 'group-hover:text-orange-400' },
  ];

  const typeIcon: Record<string, string> = {
    account: 'bg-cyan-500/20 text-cyan-400',
    opportunity: 'bg-green-500/20 text-green-400',
    bid: 'bg-amber-500/20 text-amber-400',
  };

  return (
    <>
      <Header title="Command Centre" />
      <div className="p-6 space-y-6">
        {/* Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card, i) => (
            <div
              key={card.label}
              className={`stat-card p-5 fade-in-up delay-${i + 1}`}
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} rounded-[inherit] pointer-events-none`} />
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-10 h-10 rounded-xl bg-color-surface/80 ring-1 ${card.ring} flex items-center justify-center`}>
                    <card.Icon size={20} className={card.accent} strokeWidth={1.8} />
                  </div>
                  <ArrowUpRight size={14} className="text-color-text-faint" />
                </div>
                <p className={`text-3xl font-bold font-mono ${card.accent} tracking-tight`}>
                  <AnimatedNumber value={card.value} loading={loading} />
                </p>
                <p className="text-color-text-muted text-xs mt-1.5 font-medium">{card.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Activity Feed - wider */}
          <div className="lg:col-span-2 glass-card rounded-2xl p-6 fade-in-up delay-5">
            <div className="flex items-center justify-between mb-5">
              <div className="section-header">
                <Activity size={14} />
                Live Activity
              </div>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-color-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-color-success"></span>
              </span>
            </div>
            {loading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => <div key={i} className="h-12 rounded-xl shimmer" />)}
              </div>
            ) : activity.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-12 h-12 rounded-2xl bg-color-primary/10 flex items-center justify-center mb-3">
                  <Activity size={24} className="text-color-primary" />
                </div>
                <p className="text-color-text-muted text-sm">No activity yet</p>
                <p className="text-color-text-faint text-xs mt-1">Start by adding an account</p>
              </div>
            ) : (
              <ul className="space-y-2">
                {activity.map((item, i) => (
                  <li
                    key={i}
                    className={`flex items-center gap-3 p-3 rounded-xl row-hover fade-in-up delay-${Math.min(i + 1, 8)}`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${typeIcon[item.type] || 'bg-color-surface'}`}>
                      {item.type === 'account' && <Building2 size={14} />}
                      {item.type === 'opportunity' && <Target size={14} />}
                      {item.type === 'bid' && <FileStack size={14} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-color-text-main truncate">{item.text}</p>
                    </div>
                    <div className="flex items-center gap-1 text-color-text-faint text-[10px] font-mono shrink-0">
                      <Clock size={10} />
                      {item.time}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Quick Actions - wider */}
          <div className="lg:col-span-3 glass-card rounded-2xl p-6 fade-in-up delay-6">
            <div className="section-header mb-5">
              <Zap size={14} />
              Quick Actions
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {quickActions.map((action, i) => (
                <Link
                  key={action.href}
                  href={action.href}
                  className={`group relative overflow-hidden rounded-xl border border-color-border-subtle/40 p-4 transition-all duration-300
                    hover:border-color-primary/30 hover:bg-color-primary/5 hover:shadow-glow
                    fade-in-up delay-${Math.min(i + 1, 8)}`}
                >
                  <div className="absolute inset-0 holo-shimmer opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                  <div className="relative">
                    <div className="w-9 h-9 rounded-xl bg-color-surface/80 border border-color-border-subtle/30 flex items-center justify-center mb-3 transition-all duration-300 group-hover:border-color-primary/30">
                      <action.Icon size={18} className={`text-color-text-muted transition-colors duration-300 ${action.color}`} strokeWidth={1.8} />
                    </div>
                    <p className="text-sm font-medium text-color-text-main group-hover:text-color-primary transition-colors duration-200">{action.label}</p>
                    <p className="text-color-text-faint text-xs mt-1 line-clamp-2">{action.desc}</p>
                  </div>
                  <ArrowUpRight size={14} className="absolute top-4 right-4 text-color-text-faint opacity-0 group-hover:opacity-100 transition-all duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
