'use client';

import { Show, SignInButton, SignUpButton, UserButton } from '@clerk/nextjs';
import { useTheme } from '@/components/ThemeProvider';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Sun, Moon, ChevronRight, Bell } from 'lucide-react';

interface HeaderProps {
  title: string;
  action?: React.ReactNode;
}

function useBreadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);
  const crumbs: { label: string; href: string }[] = [];

  const labelMap: Record<string, string> = {
    dashboard: 'Command Centre',
    accounts: 'Accounts',
    opportunities: 'Pipeline',
    bids: 'Bid Packs',
    estimating: 'Estimating',
    intel: 'Intelligence',
    intelligence: 'Market Intel',
    tenders: 'Tenders',
    calls: 'Calls',
    'lead-times': 'Lead Times',
    frameworks: 'Frameworks',
    blog: 'News Feed',
    agents: 'Agents',
    setup: 'Setup',
  };

  let path = '';
  for (const seg of segments) {
    path += `/${seg}`;
    crumbs.push({ label: labelMap[seg] || seg.charAt(0).toUpperCase() + seg.slice(1), href: path });
  }

  return crumbs;
}

export default function Header({ title, action }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const breadcrumbs = useBreadcrumbs();

  return (
    <header className="h-16 px-6 border-b border-color-border-subtle/40 sticky top-0 z-20 flex items-center justify-between overflow-hidden bg-color-background/80 backdrop-blur-xl">
      {/* Subtle top accent line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-color-primary/30 to-transparent" />

      {/* Left: Breadcrumbs + Title */}
      <div className="relative flex flex-col justify-center">
        {breadcrumbs.length > 1 && (
          <nav className="flex items-center gap-1 text-[10px] font-mono tracking-wider text-color-text-faint mb-0.5">
            {breadcrumbs.map((crumb, i) => (
              <span key={crumb.href} className="flex items-center gap-1">
                {i > 0 && <ChevronRight size={10} className="text-color-text-faint/50" />}
                {i < breadcrumbs.length - 1 ? (
                  <Link href={crumb.href} className="hover:text-color-primary transition-colors">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-color-text-muted">{crumb.label}</span>
                )}
              </span>
            ))}
          </nav>
        )}
        <h1 className="relative text-lg font-semibold text-color-text-main tracking-tight">{title}</h1>
      </div>

      {/* Right: Actions */}
      <div className="relative flex items-center gap-2">
        {action && <div>{action}</div>}

        {/* Notifications placeholder */}
        <button className="w-9 h-9 rounded-xl bg-color-surface/60 flex items-center justify-center border border-color-border-subtle/50 hover:border-color-primary/30 hover:bg-color-primary/5 transition-all duration-200 relative">
          <Bell size={16} className="text-color-text-muted" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-color-primary animate-pulse" />
        </button>
        
        {/* Clerk Auth UI */}
        <Show when="signed-out">
          <SignInButton mode="modal">
            <button className="px-3.5 py-1.5 text-xs font-medium text-color-text-main bg-color-surface/60 border border-color-border-subtle/50 rounded-xl hover:border-color-primary/40 transition-all duration-200">
              Sign In
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="px-3.5 py-1.5 text-xs font-medium text-color-background bg-color-primary rounded-xl hover:bg-color-primary/90 transition-all duration-200 shadow-sm shadow-color-primary/20">
              Sign Up
            </button>
          </SignUpButton>
        </Show>
        <Show when="signed-in">
          <UserButton afterSignOutUrl="/" />
        </Show>

        {/* Dark / Light toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="w-9 h-9 rounded-xl bg-color-surface/60 flex items-center justify-center border border-color-border-subtle/50 hover:border-color-primary/30 hover:bg-color-primary/5 transition-all duration-200"
        >
          {theme === 'dark' ? <Sun size={16} className="text-color-warning" /> : <Moon size={16} className="text-color-secondary" />}
        </button>
      </div>
    </header>
  );
}
