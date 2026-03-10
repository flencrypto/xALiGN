'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import { accountsApi, opportunitiesApi, bidsApi, Account, Opportunity, Bid } from '@/lib/api';
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
  Search,
  Globe,
  Radar,
  BarChart3,
  ArrowRight,
  Layers,
  Shield,
} from 'lucide-react';

interface Stats {
  totalAccounts: number;
  activeOpportunities: number;
  activeBids: number;
  winRate: number;
  pipelineValue: number;
  newThisWeek: number;
}

function AnimatedNumber({ value, loading }: { value: number | string; loading: boolean }) {
  if (loading) return <div className="h-9 w-24 rounded-lg shimmer" />;
  return <span className="tabular-nums">{value}</span>;
}

function ProgressRing({ value, max, size = 48, stroke = 3, color }: { value: number; max: number; size?: number; stroke?: number; color: string }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = max > 0 ? (value / max) * circumference : 0;
  return (
    <svg width={size} height={size} className="progress-ring">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgb(var(--color-border-subtle) / 0.30)" strokeWidth={stroke} />
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={stroke} strokeDasharray={circumference} strokeDashoffset={circumference - progress} strokeLinecap="round" />
    </svg>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ totalAccounts: 0, activeOpportunities: 0, activeBids: 0, winRate: 0, pipelineValue: 0, newThisWeek: 0 });
  const [loading, setLoading] = useState(true);
  const [activity, setActivity] = useState<{ text: string; type: string; time: string; detail?: string }[]>([]);
  const [topAccounts, setTopAccounts] = useState<Account[]>([]);
  const [recentOpps, setRecentOpps] = useState<Opportunity[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [accounts, opps, bids] = await Promise.all([
          accountsApi.list().catch(() => [] as Account[]),
          opportunitiesApi.list().catch(() => [] as Opportunity[]),
          bidsApi.list().catch(() => [] as Bid[]),
        ]);
        const activeOpps = opps.filter((o) => !['Won', 'Lost'].includes(o.stage));
        const activeBids = bids.filter((b) => !['Won', 'Lost'].includes(b.status));
        const won = bids.filter((b) => b.status === 'Won').length;
        const total = bids.filter((b) => ['Won', 'Lost'].includes(b.status)).length;
        const winRate = total > 0 ? Math.round((won / total) * 100) : 0;
        const pipelineValue = activeOpps.reduce((s, o) => s + (o.estimated_value || 0), 0);
        setStats({ totalAccounts: accounts.length, activeOpportunities: activeOpps.length, activeBids: activeBids.length, winRate, pipelineValue, newThisWeek: Math.min(accounts.length, 3) });
        setTopAccounts(accounts.slice(0, 5));
        setRecentOpps(activeOpps.slice(0, 5));

        const lines: { text: string; type: string; time: string; detail?: string }[] = [];
        accounts.slice(0, 4).forEach((a) => lines.push({ text: a.name, type: 'account', time: 'Recent', detail: `${a.type || 'Account'} · ${a.location || 'No location'}` }));
        opps.slice(0, 4).forEach((o) => lines.push({ text: o.title, type: 'opportunity', time: 'Recent', detail: `${o.stage}${o.estimated_value ? ` · £${o.estimated_value.toLocaleString()}` : ''}` }));
        bids.slice(0, 3).forEach((b) => lines.push({ text: b.title, type: 'bid', time: 'Recent', detail: `Status: ${b.status}` }));
        setActivity(lines.slice(0, 10));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const statCards = [
    { label: 'Total Accounts', value: stats.totalAccounts, Icon: Building2, color: 'rgb(0,229,255)', gradient: 'from-cyan-500/15 via-cyan-500/5 to-transparent', accent: 'text-color-primary', ring: 'ring-cyan-500/20', max: 50 },
    { label: 'Active Pipeline', value: stats.activeOpportunities, Icon: Target, color: 'rgb(34,197,94)', gradient: 'from-green-500/15 via-green-500/5 to-transparent', accent: 'text-color-success', ring: 'ring-green-500/20', max: 20 },
    { label: 'Live Bids', value: stats.activeBids, Icon: FileStack, color: 'rgb(245,158,11)', gradient: 'from-amber-500/15 via-amber-500/5 to-transparent', accent: 'text-color-warning', ring: 'ring-amber-500/20', max: 10 },
    { label: 'Win Rate', value: `${stats.winRate}%`, Icon: Trophy, color: 'rgb(99,102,241)', gradient: 'from-indigo-500/15 via-indigo-500/5 to-transparent', accent: 'text-color-secondary', ring: 'ring-indigo-500/20', max: 100 },
  ];

  const quickActions = [
    { href: '/accounts', label: 'Account Intelligence', desc: 'Client CRM & trigger signals', Icon: Building2, color: 'group-hover:text-cyan-400', iconBg: 'bg-cyan-500/10 group-hover:bg-cyan-500/20' },
    { href: '/opportunities', label: 'Opportunity Pipeline', desc: 'Qualify & track live opps', Icon: Target, color: 'group-hover:text-green-400', iconBg: 'bg-green-500/10 group-hover:bg-green-500/20' },
    { href: '/bids', label: 'Bid Pack Builder', desc: 'Compliance, RFIs, documents', Icon: FileStack, color: 'group-hover:text-amber-400', iconBg: 'bg-amber-500/10 group-hover:bg-amber-500/20' },
    { href: '/estimating', label: 'Estimating Engine', desc: 'Scope gaps & cost models', Icon: Calculator, color: 'group-hover:text-indigo-400', iconBg: 'bg-indigo-500/10 group-hover:bg-indigo-500/20' },
    { href: '/intel', label: 'Deep Intelligence', desc: 'AI research & company intel', Icon: Search, color: 'group-hover:text-purple-400', iconBg: 'bg-purple-500/10 group-hover:bg-purple-500/20' },
    { href: '/intelligence', label: 'Market Intel', desc: 'News, planning, infra data', Icon: Globe, color: 'group-hover:text-teal-400', iconBg: 'bg-teal-500/10 group-hover:bg-teal-500/20' },
    { href: '/tenders', label: 'Tender Tracker', desc: 'Track & respond to tenders', Icon: Zap, color: 'group-hover:text-orange-400', iconBg: 'bg-orange-500/10 group-hover:bg-orange-500/20' },
    { href: '/frameworks', label: 'Frameworks', desc: 'Framework agreements & status', Icon: Layers, color: 'group-hover:text-pink-400', iconBg: 'bg-pink-500/10 group-hover:bg-pink-500/20' },
  ];

  const typeIcon: Record<string, { bg: string; Icon: typeof Building2 }> = {
    account: { bg: 'bg-cyan-500/15 text-cyan-400', Icon: Building2 },
    opportunity: { bg: 'bg-green-500/15 text-green-400', Icon: Target },
    bid: { bg: 'bg-amber-500/15 text-amber-400', Icon: FileStack },
  };

  return (
    <>
      <Header title="Command Centre" />
      <div className="p-6 space-y-6">
        {/* ── Hero Stats Row ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card, i) => (
            <div key={card.label} className="metric-card p-5 fade-in-up" style={{ animationDelay: `${(i + 1) * 0.05}s` }}>
              <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} rounded-[inherit] pointer-events-none`} />
              <div className="relative">
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-11 h-11 rounded-2xl bg-color-surface/60 ring-1 ${card.ring} flex items-center justify-center backdrop-blur-sm`}>
                    <card.Icon size={20} className={card.accent} strokeWidth={1.6} />
                  </div>
                  <ProgressRing value={typeof card.value === 'number' ? card.value : stats.winRate} max={card.max} color={card.color} />
                </div>
                <p className={`text-3xl font-bold font-mono ${card.accent} tracking-tight neon-text`}>
                  <AnimatedNumber value={card.value} loading={loading} />
                </p>
                <p className="text-color-text-muted text-[11px] mt-1.5 font-medium uppercase tracking-wider">{card.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* ── Pipeline Value Banner ── */}
        {stats.pipelineValue > 0 && (
          <div className="glass-card rounded-2xl p-4 flex items-center justify-between fade-in-up delay-5">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-color-success/10 flex items-center justify-center">
                <BarChart3 size={20} className="text-color-success" />
              </div>
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-color-text-faint">Active Pipeline Value</p>
                <p className="text-2xl font-bold font-mono text-color-success neon-text">
                  £{loading ? '—' : stats.pipelineValue.toLocaleString()}
                </p>
              </div>
            </div>
            <Link href="/opportunities" className="flex items-center gap-1.5 text-xs text-color-primary hover:text-color-primary/80 transition-colors font-mono">
              View Pipeline <ArrowRight size={14} />
            </Link>
          </div>
        )}

        {/* ── Main Grid: Activity + Actions ── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Activity Feed */}
          <div className="lg:col-span-5 glass-card rounded-2xl p-6 fade-in-up delay-5 data-stream" style={{ containerType: 'size' }}>
            <div className="flex items-center justify-between mb-5">
              <div className="section-header">
                <Activity size={14} />
                Live Feed
              </div>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-color-success opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-color-success"></span>
                </span>
                <span className="text-[10px] font-mono text-color-text-faint">{activity.length} events</span>
              </div>
            </div>
            {loading ? (
              <div className="space-y-3">
                {[...Array(6)].map((_, i) => <div key={i} className="h-14 rounded-xl shimmer" />)}
              </div>
            ) : activity.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-14 h-14 rounded-2xl bg-color-primary/10 flex items-center justify-center mb-4 radar-ping">
                  <Radar size={24} className="text-color-primary" />
                </div>
                <p className="text-color-text-muted text-sm font-medium">Awaiting intelligence</p>
                <p className="text-color-text-faint text-xs mt-1.5 max-w-[200px]">Start by adding an account or opportunity</p>
              </div>
            ) : (
              <ul className="space-y-1.5">
                {activity.map((item, i) => {
                  const icon = typeIcon[item.type] || typeIcon.account;
                  return (
                    <li
                      key={i}
                      className="flex items-center gap-3 p-3 rounded-xl row-hover fade-in-up"
                      style={{ animationDelay: `${Math.min((i + 1) * 0.05, 0.4)}s` }}
                    >
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${icon.bg}`}>
                        <icon.Icon size={15} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-color-text-main font-medium truncate">{item.text}</p>
                        {item.detail && <p className="text-[10px] text-color-text-faint font-mono mt-0.5 truncate">{item.detail}</p>}
                      </div>
                      <div className="flex items-center gap-1.5 text-color-text-faint text-[10px] font-mono shrink-0">
                        <Clock size={10} />
                        {item.time}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {/* Quick Actions Grid */}
          <div className="lg:col-span-7 fade-in-up delay-6">
            <div className="section-header mb-4">
              <Zap size={14} />
              Mission Control
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {quickActions.map((action, i) => (
                <Link
                  key={action.href}
                  href={action.href}
                  className="group action-card p-4 fade-in-up"
                  style={{ animationDelay: `${Math.min((i + 1) * 0.05, 0.4)}s` }}
                >
                  <div className="absolute inset-0 holo-shimmer opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                  <div className="relative">
                    <div className={`w-10 h-10 rounded-xl ${action.iconBg} border border-color-border-subtle/20 flex items-center justify-center mb-3 transition-all duration-300 group-hover:border-color-primary/20`}>
                      <action.Icon size={18} className={`text-color-text-muted transition-colors duration-300 ${action.color}`} strokeWidth={1.6} />
                    </div>
                    <p className="text-sm font-medium text-color-text-main group-hover:text-color-primary transition-colors duration-200 leading-tight">{action.label}</p>
                    <p className="text-color-text-faint text-[10px] mt-1 line-clamp-2 leading-relaxed">{action.desc}</p>
                  </div>
                  <ArrowUpRight size={12} className="absolute top-3 right-3 text-color-text-faint/50 opacity-0 group-hover:opacity-100 transition-all duration-200" />
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* ── Bottom Row: Top Accounts + Recent Pipeline ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Accounts */}
          <div className="glass-card rounded-2xl p-6 fade-in-up delay-7">
            <div className="flex items-center justify-between mb-4">
              <div className="section-header">
                <Shield size={14} />
                Key Accounts
              </div>
              <Link href="/accounts" className="text-[10px] text-color-primary hover:underline font-mono flex items-center gap-1">
                All Accounts <ArrowRight size={10} />
              </Link>
            </div>
            {loading ? (
              <div className="space-y-2">
                {[...Array(4)].map((_, i) => <div key={i} className="h-14 rounded-xl shimmer" />)}
              </div>
            ) : topAccounts.length === 0 ? (
              <p className="text-xs text-color-text-faint py-8 text-center">No accounts yet</p>
            ) : (
              <div className="space-y-1.5">
                {topAccounts.map((acc) => (
                  <Link
                    key={acc.id}
                    href={`/accounts/${acc.id}`}
                    className="flex items-center gap-3 p-3 rounded-xl row-hover group"
                  >
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/10 border border-cyan-500/15 flex items-center justify-center shrink-0">
                      <Building2 size={15} className="text-cyan-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-color-text-main font-medium truncate group-hover:text-color-primary transition-colors">{acc.name}</p>
                      <p className="text-[10px] text-color-text-faint font-mono truncate">{acc.type || 'Unknown'} · {acc.location || 'No location'}</p>
                    </div>
                    <ArrowUpRight size={12} className="text-color-text-faint/40 group-hover:text-color-primary transition-colors shrink-0" />
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Recent Pipeline */}
          <div className="glass-card rounded-2xl p-6 fade-in-up delay-8">
            <div className="flex items-center justify-between mb-4">
              <div className="section-header">
                <TrendingUp size={14} />
                Recent Pipeline
              </div>
              <Link href="/opportunities" className="text-[10px] text-color-primary hover:underline font-mono flex items-center gap-1">
                Full Pipeline <ArrowRight size={10} />
              </Link>
            </div>
            {loading ? (
              <div className="space-y-2">
                {[...Array(4)].map((_, i) => <div key={i} className="h-14 rounded-xl shimmer" />)}
              </div>
            ) : recentOpps.length === 0 ? (
              <p className="text-xs text-color-text-faint py-8 text-center">No active opportunities</p>
            ) : (
              <div className="space-y-1.5">
                {recentOpps.map((opp) => (
                  <Link
                    key={opp.id}
                    href="/opportunities"
                    className="flex items-center gap-3 p-3 rounded-xl row-hover group"
                  >
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-green-500/15 to-emerald-500/10 border border-green-500/15 flex items-center justify-center shrink-0">
                      <Target size={15} className="text-green-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-color-text-main font-medium truncate group-hover:text-color-primary transition-colors">{opp.title}</p>
                      <p className="text-[10px] text-color-text-faint font-mono truncate">
                        {opp.stage}{opp.estimated_value ? ` · £${opp.estimated_value.toLocaleString()}` : ''}
                      </p>
                    </div>
                    <span className="px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider bg-green-500/10 text-green-400 rounded-full border border-green-500/20 shrink-0">
                      {opp.stage}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
