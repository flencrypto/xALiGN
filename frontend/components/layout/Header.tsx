'use client';

import { useTheme } from '@/components/ThemeProvider';

interface HeaderProps {
  title: string;
  action?: React.ReactNode;
}

export default function Header({ title, action }: HeaderProps) {
  const { theme, setTheme } = useTheme();

  return (
    <header className="h-16 px-6 border-b border-border-subtle bg-background/80 backdrop-blur-md sticky top-0 z-20 flex items-center justify-between">
      <h1 className="text-xl font-semibold text-text-main tracking-tight">{title}</h1>
      <div className="flex items-center gap-3">
        {action && <div>{action}</div>}
        {/* Dark / Light toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center border border-border-subtle hover:border-primary transition-all duration-200"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  );
}

