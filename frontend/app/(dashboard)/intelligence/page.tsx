'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import { intelligenceApi, projectsApi, type ProjectStats, type IntelligenceStatus, type NewsArticle } from '@/lib/api';
import IntegrationGate from '@/components/IntegrationGate';
import { useSetupStatus } from '@/lib/useSetupStatus';

export default function IntelligenceHubPage() {
  const { isConfigured } = useSetupStatus();
  const grokConfigured = isConfigured('grok_ai');
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [status, setStatus] = useState<IntelligenceStatus[]>([]);
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, st, n] = await Promise.all([
          projectsApi.getStats().catch(() => null),
          intelligenceApi.getStatus().catch(() => []),
          intelligenceApi.listNews({ limit: 10 }).catch(() => []),
        ]);
        setStats(s);
        setStatus(st);
        setNews(n);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleRun(collector: string, fn: () => Promise<unknown>) {
    setRunning(collector);
    try {
      await fn();
      const st = await intelligenceApi.getStatus().catch(() => []);
      setStatus(st);
    } finally {
      setRunning(null);
    }
  }

  const collectors = [
    { key: 'news_aggregator', label: 'News Aggregator', icon: '📰', fn: () => intelligenceApi.runNewsAggregator() },
    { key: 'planning_scraper', label: 'Planning Scraper', icon: '🏗️', fn: () => intelligenceApi.runPlanningScraper() },
    { key: 'press_release_harvester', label: 'Press Releases', icon: '📢', fn: () => intelligenceApi.runPressReleases() },
    { key: 'job_signal_detector', label: 'Job Signals', icon: '👔', fn: () => intelligenceApi.runJobDetector() },
    { key: 'infra_monitor', label: 'Infrastructure Monitor', icon: '⚡', fn: () => intelligenceApi.runInfraMonitor() },
  ];

  const views = [
    { href: '/intelligence/map', label: 'Global Expansion Map', icon: '🗺️', desc: 'Visualise all projects globally' },
    { href: '/intelligence/heatmap', label: 'Regional Heatmap', icon: '🔥', desc: 'Infrastructure growth by region' },
    { href: '/intelligence/capacity', label: 'Capacity Dashboard', icon: '⚡', desc: 'MW pipeline by company & region' },
    { href: '/intelligence/capex', label: 'Capex Tracker', icon: '💰', desc: 'Infrastructure investment globally' },
  ];

  return (
    <>
      <Header title="Market Intelligence" />
      <div className="p-6 space-y-6">

        {/* Stats row */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Projects Tracked', value: stats.total_projects, icon: '🏗️', color: 'text-primary', bg: 'bg-primary/10' },
              { label: 'Total MW Pipeline', value: `${stats.total_capacity_mw.toLocaleString()} MW`, icon: '⚡', color: 'text-success', bg: 'bg-success/10' },
              { label: 'Total Capex', value: `£${stats.total_capex_millions.toLocaleString()}M`, icon: '💰', color: 'text-warning', bg: 'bg-warning/10' },
              { label: 'Types Tracked', value: Object.keys(stats.by_type).length, icon: '🎯', color: 'text-secondary', bg: 'bg-secondary/10' },
            ].map((card) => (
              <div key={card.label} className={`${card.bg} border border-border-subtle rounded-xl p-5 card-hover`}>
                <span className="text-2xl">{card.icon}</span>
                {loading ? (
                  <div className="h-8 w-16 bg-surface rounded animate-pulse mt-2" />
                ) : (
                  <p className={`text-3xl font-bold font-mono mt-2 ${card.color}`}>{card.value}</p>
                )}
                <p className="text-text-muted text-sm mt-1">{card.label}</p>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Collector controls */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[01] Collection Agents</h2>
            <div className="space-y-3">
              {collectors.map((col) => {
                const st = status.find((s) => s.collector === col.key);
                return (
                  <div key={col.key} className="flex items-center justify-between bg-background rounded-lg p-3 border border-border-subtle">
                    <div>
                      <span className="mr-2">{col.icon}</span>
                      <span className="text-text-main text-sm font-medium">{col.label}</span>
                      {st && (
                        <p className="text-text-faint text-xs mt-0.5 font-mono">
                          {st.record_count} records
                          {st.last_collected_at ? ` · ${new Date(st.last_collected_at).toLocaleDateString()}` : ''}
                        </p>
                      )}
                    </div>
                    <IntegrationGate feature="grok_ai" isConfigured={grokConfigured}>
                      <button
                        onClick={() => handleRun(col.key, col.fn)}
                        disabled={running !== null}
                        className="px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-mono rounded border border-primary/30 transition-all disabled:opacity-50"
                      >
                        {running === col.key ? 'Running…' : 'Run'}
                      </button>
                    </IntegrationGate>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Visualisation links */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[02] Visualisation Views</h2>
            <div className="grid grid-cols-2 gap-3">
              {views.map((view) => (
                <Link
                  key={view.href}
                  href={view.href}
                  className="bg-background hover:bg-primary/5 border border-border-subtle hover:border-primary/50 rounded-lg p-4 transition-all group card-hover"
                >
                  <span className="text-2xl block mb-2">{view.icon}</span>
                  <p className="text-text-main text-sm font-medium group-hover:text-primary transition-colors">{view.label}</p>
                  <p className="text-text-muted text-xs mt-1">{view.desc}</p>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Latest news */}
        <div className="bg-surface border border-border-subtle rounded-xl p-5">
          <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[03] Latest Signals</h2>
          {loading ? (
            <div className="space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-background rounded animate-pulse" />)}</div>
          ) : news.length === 0 ? (
            <p className="text-text-muted text-sm">No signals collected yet. Run a collection agent above.</p>
          ) : (
            <div className="space-y-3">
              {news.map((article) => (
                <div key={article.id} className="flex items-start gap-3 bg-background rounded-lg p-3 border border-border-subtle">
                  <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded flex-shrink-0 mt-0.5">
                    {article.category?.toUpperCase() || 'NEWS'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-text-main text-sm font-medium truncate">{article.title}</p>
                    <p className="text-text-faint text-xs mt-0.5">
                      {article.source_name} · {article.published_at || 'Unknown date'}
                    </p>
                  </div>
                  {article.url && (
                    <a href={article.url} target="_blank" rel="noopener noreferrer" className="text-primary text-xs flex-shrink-0 hover:underline">↗</a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </>
  );
}
