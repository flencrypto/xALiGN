'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import Header from '@/components/layout/Header';
import { projectsApi, type InfrastructureProject } from '@/lib/api';

// Dynamically import the map to avoid SSR/window issues with Leaflet
const IntelMap = dynamic(() => import('@/components/intelligence/IntelMap'), {
  ssr: false,
  loading: () => (
    <div className="flex-1 flex items-center justify-center bg-surface rounded-xl border border-border-subtle">
      <p className="text-text-muted font-mono text-sm">Loading map…</p>
    </div>
  ),
});

const STAGE_COLORS: Record<string, string> = {
  announced: '#4fc3f7',
  planning: '#ffb74d',
  approved: '#81c784',
  construction: '#ff8a65',
  operational: '#4db6ac',
  cancelled: '#e57373',
};

export default function MapPage() {
  const [projects, setProjects] = useState<InfrastructureProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [stageFilter, setStageFilter] = useState<string>('');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await projectsApi.getMapData(stageFilter || undefined).catch(() => []);
        setProjects(data);
        setTotal(data.length);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [stageFilter]);

  return (
    <>
      <Header title="Global Expansion Map" />
      <div className="p-6 flex flex-col gap-4 h-full">
        {/* Controls */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex gap-2 flex-wrap">
            {['', 'announced', 'planning', 'approved', 'construction', 'operational'].map((stage) => (
              <button
                key={stage}
                onClick={() => setStageFilter(stage)}
                className={`px-3 py-1.5 text-xs font-mono rounded border transition-all ${
                  stageFilter === stage
                    ? 'bg-primary/20 border-primary text-primary'
                    : 'border-border-subtle text-text-muted hover:border-primary/50'
                }`}
              >
                {stage || 'All Stages'}
              </button>
            ))}
          </div>
          <span className="text-text-faint text-xs font-mono ml-auto">{total} projects</span>
        </div>

        {/* Legend */}
        <div className="flex gap-4 flex-wrap">
          {Object.entries(STAGE_COLORS).map(([stage, color]) => (
            <div key={stage} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-text-faint text-xs capitalize">{stage}</span>
            </div>
          ))}
        </div>

        {/* Map container */}
        <div className="flex-1 min-h-[500px] rounded-xl overflow-hidden border border-border-subtle">
          {loading ? (
            <div className="w-full h-full flex items-center justify-center bg-surface">
              <p className="text-text-muted font-mono text-sm">Loading projects…</p>
            </div>
          ) : (
            <IntelMap projects={projects} stageColors={STAGE_COLORS} />
          )}
        </div>
      </div>
    </>
  );
}
