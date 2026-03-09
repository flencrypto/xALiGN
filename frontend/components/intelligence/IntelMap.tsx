'use client';

import { useEffect, useRef } from 'react';
import 'leaflet/dist/leaflet.css';
import type * as Leaflet from 'leaflet';
import type { InfrastructureProject } from '@/lib/api';

interface Props {
  projects: InfrastructureProject[];
  stageColors: Record<string, string>;
}

export default function IntelMap({ projects, stageColors }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Leaflet.Map | null>(null);

  function escapeHtml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  useEffect(() => {
    if (!containerRef.current) return;

    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const L = require('leaflet') as typeof import('leaflet');

    // Fix Leaflet icon paths in Next.js
    delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });

    const map = L.map(containerRef.current, {
      center: [51.5, -0.1],
      zoom: 4,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update markers whenever projects change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const L = require('leaflet') as typeof import('leaflet');

    const markers: Leaflet.CircleMarker[] = [];

    projects
      .filter((p) => p.latitude != null && p.longitude != null)
      .forEach((p) => {
        const color = stageColors[p.stage || ''] || '#888';
        const radius = p.capacity_mw
          ? Math.min(Math.max(Math.sqrt(p.capacity_mw) * 0.8, 6), 25)
          : 6;

        const marker = L.circleMarker([p.latitude!, p.longitude!], {
          color,
          fillColor: color,
          fillOpacity: 0.7,
          weight: 1,
          radius,
        }).addTo(map);

        const popupContent = [
          `<strong style="color:#fff">${escapeHtml(p.name)}</strong>`,
          p.company ? `<p style="color:#aaa;margin:4px 0 0">${escapeHtml(p.company)}</p>` : '',
          p.location ? `<p style="color:#aaa;margin:2px 0 0">📍 ${escapeHtml(p.location)}</p>` : '',
          p.capacity_mw ? `<p style="color:#4db6ac;margin:2px 0 0">⚡ ${p.capacity_mw} MW</p>` : '',
          p.capex_millions ? `<p style="color:#ffb74d;margin:2px 0 0">💰 £${p.capex_millions}M</p>` : '',
          p.stage ? `<p style="color:${color};margin:4px 0 0;text-transform:capitalize">${escapeHtml(p.stage)}</p>` : '',
        ]
          .filter(Boolean)
          .join('');

        marker.bindPopup(`<div style="min-width:200px">${popupContent}</div>`);
        markers.push(marker);
      });

    return () => {
      markers.forEach((m) => m.remove());
    };
  }, [projects, stageColors]);

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', minHeight: '500px', background: '#0d1117' }}
    />
  );
}
