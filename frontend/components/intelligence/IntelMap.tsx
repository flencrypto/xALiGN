'use client';

import { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { InfrastructureProject } from '@/lib/api';

interface Props {
  projects: InfrastructureProject[];
  stageColors: Record<string, string>;
}

export default function IntelMap({ projects, stageColors }: Props) {
  // Fix Leaflet icon paths in Next.js
  useEffect(() => {
    // Leaflet tries to load marker images — suppress this in Next.js
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const L = require('leaflet');
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });
  }, []);

  const center: [number, number] = [51.5, -0.1]; // London as default

  return (
    <MapContainer
      center={center}
      zoom={4}
      style={{ width: '100%', height: '100%', minHeight: '500px', background: '#0d1117' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      {projects
        .filter((p) => p.latitude && p.longitude)
        .map((p) => {
          const color = stageColors[p.stage || ''] || '#888';
          const radius = p.capacity_mw ? Math.min(Math.max(Math.sqrt(p.capacity_mw) * 0.8, 6), 25) : 6;
          return (
            <CircleMarker
              key={p.id}
              center={[p.latitude!, p.longitude!]}
              radius={radius}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.7,
                weight: 1,
              }}
            >
              <Popup>
                <div style={{ minWidth: 200 }}>
                  <strong style={{ color: '#fff' }}>{p.name}</strong>
                  {p.company && <p style={{ color: '#aaa', margin: '4px 0 0' }}>{p.company}</p>}
                  {p.location && <p style={{ color: '#aaa', margin: '2px 0 0' }}>📍 {p.location}</p>}
                  {p.capacity_mw && <p style={{ color: '#4db6ac', margin: '2px 0 0' }}>⚡ {p.capacity_mw} MW</p>}
                  {p.capex_millions && <p style={{ color: '#ffb74d', margin: '2px 0 0' }}>💰 £{p.capex_millions}M</p>}
                  {p.stage && <p style={{ color, margin: '4px 0 0', textTransform: 'capitalize' }}>{p.stage}</p>}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
    </MapContainer>
  );
}
