'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { projectsApi, type HeatmapPoint } from '@/lib/api';

export default function HeatmapPage() {
  const [data, setData] = useState<HeatmapPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsApi.getHeatmap().then(setData).catch(() => []).finally(() => setLoading(false));
  }, []);

  const maxCount = Math.max(...data.map((d) => d.project_count), 1);
  const maxMW = Math.max(...data.map((d) => d.total_mw), 1);

  return (
    <>
      <Header title="Regional Heatmap" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {[
            { label: 'Regions Tracked', value: data.length, color: 'text-primary', bg: 'bg-primary/10' },
            { label: 'Total MW', value: `${data.reduce((a, b) => a + b.total_mw, 0).toLocaleString()} MW`, color: 'text-success', bg: 'bg-success/10' },
            { label: 'Total Capex', value: `£${data.reduce((a, b) => a + b.total_capex, 0).toLocaleString()}M`, color: 'text-warning', bg: 'bg-warning/10' },
          ].map((card) => (
            <div key={card.label} className={`${card.bg} border border-border-subtle rounded-xl p-5`}>
              <p className={`text-3xl font-bold font-mono ${card.color}`}>{card.value}</p>
              <p className="text-text-muted text-sm mt-1">{card.label}</p>
            </div>
          ))}
        </div>

        <div className="bg-surface border border-border-subtle rounded-xl p-5">
          <h2 className="text-primary font-mono text-sm uppercase tracking-widest mb-4">[01] Infrastructure Growth by Region</h2>
          {loading ? (
            <div className="space-y-2">{[...Array(8)].map((_, i) => <div key={i} className="h-12 bg-background rounded animate-pulse" />)}</div>
          ) : data.length === 0 ? (
            <p className="text-text-muted text-sm">No regional data yet. Run the intelligence collectors to populate.</p>
          ) : (
            <div className="space-y-3">
              {data.map((point) => {
                const widthPct = Math.round((point.project_count / maxCount) * 100);
                const mwWidthPct = Math.round((point.total_mw / maxMW) * 100);
                return (
                  <div key={point.location} className="bg-background border border-border-subtle rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-text-main text-sm font-medium">{point.location}</span>
                      <div className="flex gap-4 text-xs font-mono">
                        <span className="text-primary">{point.project_count} projects</span>
                        <span className="text-success">{point.total_mw.toLocaleString()} MW</span>
                        {point.total_capex > 0 && (
                          <span className="text-warning">£{point.total_capex.toLocaleString()}M</span>
                        )}
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-text-faint text-xs w-16">Projects</span>
                        <div className="flex-1 bg-background rounded-full h-2 border border-border-subtle">
                          <div
                            className="h-2 rounded-full bg-primary transition-all"
                            style={{ width: `${widthPct}%` }}
                          />
                        </div>
                      </div>
                      {point.total_mw > 0 && (
                        <div className="flex items-center gap-2">
                          <span className="text-text-faint text-xs w-16">Capacity</span>
                          <div className="flex-1 bg-background rounded-full h-2 border border-border-subtle">
                            <div
                              className="h-2 rounded-full bg-success transition-all"
                              style={{ width: `${mwWidthPct}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
