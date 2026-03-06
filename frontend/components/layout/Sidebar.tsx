'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import AlignLogo from '@/components/layout/AlignLogo';

const navItems = [
  { href: '/dashboard', label: 'Command Centre', icon: '⊞' },
  { href: '/accounts', label: 'Account Intel', icon: '🏢' },
  { href: '/opportunities', label: 'Pipeline', icon: '🎯' },
  { href: '/bids', label: 'Bid Packs', icon: '📋' },
  { href: '/estimating', label: 'Estimating', icon: '📐' },
  { href: '/intel', label: 'Intelligence', icon: '🔍' },
  { href: '/intelligence', label: 'Market Intelligence', icon: '🌐' },
  { href: '/tenders', label: 'Tenders', icon: '📑' },
  { href: '/calls', label: 'Calls', icon: '📞' },
  { href: '/lead-times', label: 'Lead Times', icon: '⏱' },
  { href: '/frameworks', label: 'Frameworks', icon: '🏛' },
  { href: '/blog', label: 'News Feed', icon: '✍️' },
  { href: '/agents', label: 'Agents', icon: '🤖' },
  { href: '/setup', label: 'Setup', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="fixed top-4 left-4 z-50 md:hidden bg-surface border border-border-subtle text-text-main p-2 rounded"
        onClick={() => setOpen(!open)}
        aria-label="Toggle sidebar"
      >
        {open ? '✕' : '☰'}
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-64 border-r border-border-subtle z-40 flex flex-col glass-panel
          transition-transform duration-200
          ${open ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0 md:static md:h-screen
        `}
      >
        {/* Logo — blueprint grid panel */}
        <div className="px-6 py-5 border-b border-border-subtle bg-blueprint">
          <AlignLogo compact />
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 overflow-y-auto flex flex-col gap-1">
          {navItems.map((item) => {
            const isActive =
              item.href === '/dashboard' ? pathname === '/dashboard' : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all relative overflow-hidden
                  ${isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-text-muted hover:bg-white/5 hover:text-text-main'
                  }
                `}
              >
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-primary glow-primary" />
                )}
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-border-subtle">
          <p className="text-xs text-text-muted font-mono">AI-native Bid &amp; Delivery OS</p>
          <p className="text-xs text-text-faint font-mono mt-1">v0.1.0</p>
        </div>
      </aside>
    </>
  );
}
