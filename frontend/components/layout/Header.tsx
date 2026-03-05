'use client';

import { useTheme } from '@/components/ThemeProvider';

interface HeaderProps {
  title: string;
  action?: React.ReactNode;
}

export default function Header({ title, action }: HeaderProps) {
  const { theme, setTheme } = useTheme();

  return (
    <header
      className="h-16 px-6 border-b border-border-subtle sticky top-0 z-20 flex items-center justify-between overflow-hidden"
      style={{
        backgroundImage: "url('/header-bg.jpg')",
        backgroundSize: 'cover',
        backgroundPosition: 'center 30%',
        backgroundRepeat: 'no-repeat',
      }}
    >
      {/* Dark overlay so text stays readable over the photo */}
      <div className="absolute inset-0 bg-background/75 backdrop-blur-sm pointer-events-none" />

      {/* Content sits above overlay */}
      <h1 className="relative text-xl font-semibold text-text-main tracking-tight drop-shadow-sm">{title}</h1>
      <div className="relative flex items-center gap-3">
        {action && <div>{action}</div>}
        {/* Dark / Light toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="w-10 h-10 rounded-lg bg-surface/80 flex items-center justify-center border border-border-subtle hover:border-primary transition-all duration-200"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  );
}

