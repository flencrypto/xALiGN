'use client';

import { useTheme } from '@/components/ThemeProvider';

interface HeaderProps {
  title: string;
  action?: React.ReactNode;
}

export default function Header({ title, action }: HeaderProps) {
  const { theme, setTheme } = useTheme();

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-align-metallic/10 bg-align-surface">
      <h1 className="text-xl font-semibold text-align-text">{title}</h1>
      <div className="flex items-center gap-3">
        {action && <div>{action}</div>}
        {/* Dark / Light toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="w-10 h-10 rounded-xl bg-align-bg flex items-center justify-center border border-align-metallic/20 hover:border-align-accent transition-all duration-200"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  );
}

