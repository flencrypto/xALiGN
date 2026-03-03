'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '⊞' },
  { href: '/accounts', label: 'Accounts', icon: '🏢' },
  { href: '/opportunities', label: 'Opportunities', icon: '🎯' },
  { href: '/bids', label: 'Bids', icon: '📋' },
  { href: '/estimating', label: 'Estimating', icon: '📐' },
  { href: '/intel', label: 'Intelligence', icon: '🔍' },
  { href: '/tenders', label: 'Tenders', icon: '📑' },
  { href: '/calls', label: 'Calls', icon: '📞' },
  { href: '/blog', label: 'Blog', icon: '✍️' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="fixed top-4 left-4 z-50 md:hidden bg-slate-700 text-white p-2 rounded"
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
          fixed top-0 left-0 h-full w-56 bg-slate-800 border-r border-slate-700 z-40 flex flex-col
          transition-transform duration-200
          ${open ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0 md:static md:h-screen
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-5 py-5 border-b border-slate-700">
          <span className="text-2xl">👻</span>
          <span className="text-white font-bold text-lg tracking-tight">ContractGHOST</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 overflow-y-auto">
          {navItems.map((item) => {
            const isActive =
              item.href === '/dashboard' ? pathname === '/dashboard' : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`
                  flex items-center gap-3 px-5 py-3 text-sm font-medium transition-colors
                  ${isActive
                    ? 'bg-blue-600/20 text-blue-400 border-r-2 border-blue-500'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }
                `}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-slate-700">
          <p className="text-xs text-slate-500">AI-native Bid & Delivery OS</p>
          <p className="text-xs text-slate-600 mt-1">v0.1.0</p>
        </div>
      </aside>
    </>
  );
}
