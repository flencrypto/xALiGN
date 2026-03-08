'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import AlignLogo from '@/components/layout/AlignLogo';
import {
  LayoutDashboard,
  Building2,
  Target,
  FileStack,
  Calculator,
  Search,
  Globe,
  FileText,
  Phone,
  Clock,
  Landmark,
  Newspaper,
  Bot,
  Settings,
  ChevronLeft,
  Menu,
  X,
  Radio,
} from 'lucide-react';

const navGroups = [
  {
    label: 'Core',
    items: [
      { href: '/dashboard', label: 'Command Centre', Icon: LayoutDashboard },
      { href: '/accounts', label: 'Account Intel', Icon: Building2 },
      { href: '/opportunities', label: 'Pipeline', Icon: Target },
      { href: '/bids', label: 'Bid Packs', Icon: FileStack },
      { href: '/estimating', label: 'Estimating', Icon: Calculator },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { href: '/intel', label: 'Intelligence', Icon: Search },
      { href: '/intelligence', label: 'Market Intel', Icon: Globe },
      { href: '/tenders', label: 'Tenders', Icon: FileText },
      { href: '/signals', label: 'Signals 📡', Icon: Radio },
    ],
  },
  {
    label: 'Operations',
    items: [
      { href: '/calls', label: 'Calls', Icon: Phone },
      { href: '/lead-times', label: 'Lead Times', Icon: Clock },
      { href: '/frameworks', label: 'Frameworks', Icon: Landmark },
    ],
  },
  {
    label: 'Tools',
    items: [
      { href: '/blog', label: 'News Feed', Icon: Newspaper },
      { href: '/agents', label: 'Agents', Icon: Bot },
      { href: '/setup', label: 'Setup', Icon: Settings },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="fixed top-4 left-4 z-50 md:hidden glass-card p-2.5 rounded-xl text-color-text-main"
        onClick={() => setOpen(!open)}
        aria-label="Toggle sidebar"
      >
        {open ? <X size={18} /> : <Menu size={18} />}
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full z-40 flex flex-col
          border-r border-color-border-subtle/50
          bg-gradient-to-b from-color-surface/90 to-color-background/95
          backdrop-blur-xl
          transition-all duration-300 ease-out
          ${collapsed ? 'w-[72px]' : 'w-64'}
          ${open ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0 md:static md:h-screen
        `}
      >
        {/* Logo */}
        <div className="relative px-4 py-5 border-b border-color-border-subtle/30">
          <div className="flex items-center justify-between">
            {!collapsed && <AlignLogo compact />}
            {collapsed && (
              <div className="mx-auto w-8 h-8 rounded-lg bg-color-primary/10 flex items-center justify-center">
                <span className="text-color-primary font-bold text-sm font-mono">aL</span>
              </div>
            )}
          </div>
          {/* Collapse toggle - desktop only */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full
              bg-color-surface border border-color-border-subtle items-center justify-center
              text-color-text-muted hover:text-color-primary hover:border-color-primary/40
              transition-all duration-200 shadow-sm"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft size={14} className={`transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Nav groups */}
        <nav className="flex-1 py-3 px-2 overflow-y-auto space-y-4">
          {navGroups.map((group) => (
            <div key={group.label}>
              {!collapsed && (
                <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-color-text-faint font-mono">
                  {group.label}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive =
                    item.href === '/dashboard'
                      ? pathname === '/dashboard'
                      : pathname.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(false)}
                      title={collapsed ? item.label : undefined}
                      className={`
                        group flex items-center gap-3 rounded-xl text-sm font-medium transition-all duration-200 relative
                        ${collapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2'}
                        ${isActive
                          ? 'bg-color-primary/10 text-color-primary shadow-sm shadow-color-primary/5'
                          : 'text-color-text-muted hover:bg-color-primary/5 hover:text-color-text-main'
                        }
                      `}
                    >
                      {/* Active indicator */}
                      {isActive && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-color-primary shadow-[0_0_8px_rgba(0,229,255,0.4)]" />
                      )}
                      <item.Icon
                        size={18}
                        strokeWidth={isActive ? 2.2 : 1.8}
                        className={`shrink-0 transition-all duration-200 ${
                          isActive ? 'drop-shadow-[0_0_4px_rgba(0,229,255,0.3)]' : 'group-hover:scale-105'
                        }`}
                      />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className={`border-t border-color-border-subtle/30 ${collapsed ? 'px-2 py-3' : 'px-4 py-4'}`}>
          {!collapsed ? (
            <>
              <p className="text-[10px] text-color-text-faint font-mono tracking-wider uppercase">AI-native Bid &amp; Delivery OS</p>
              <div className="flex items-center gap-2 mt-1.5">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-color-success opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-color-success"></span>
                </span>
                <p className="text-[10px] text-color-text-faint font-mono">v0.2.0 · Online</p>
              </div>
            </>
          ) : (
            <div className="flex justify-center">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-color-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-color-success"></span>
              </span>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
