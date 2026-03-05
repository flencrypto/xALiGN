'use client';

import { useRouter } from 'next/navigation';
import AlignLogo from '@/components/layout/AlignLogo';

export default function Hero() {
  const router = useRouter();

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-background">
      {/* Blueprint grid */}
      <div className="absolute inset-0 bg-blueprint opacity-60" />

      {/* Radial glow accents */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary/5" />

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        {/* Logo — full structural beam */}
        <div className="flex justify-center mb-8">
          <AlignLogo />
        </div>

        {/* Main Tagline */}
        <h1 className="text-6xl md:text-7xl font-bold text-text-main tracking-tighter mb-4">
          Intelligence for
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary to-text-main">
            Data Centre Delivery
          </span>
        </h1>

        <p className="text-xl md:text-2xl text-text-muted max-w-2xl mx-auto mb-12">
          AI-native Bid + Delivery OS. Win more projects. Deliver with zero chaos.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => router.push('/dashboard')}
            className="px-10 py-4 bg-primary text-background font-semibold rounded-lg hover:bg-primary-dark transition-all duration-300 text-lg flex items-center justify-center gap-3 group glow-primary-hover"
          >
            Start Free Trial
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </button>

          <button
            onClick={() => router.push('/dashboard')}
            className="px-10 py-4 border border-primary text-primary font-medium rounded-lg hover:bg-primary/10 transition-all text-lg"
          >
            Book a 15-min Demo
          </button>
        </div>

        {/* Trust bar */}
        <div className="mt-16 flex flex-wrap items-center justify-center gap-6 md:gap-12 text-text-muted text-sm">
          <div>Trusted by ISG · Mace · Equinix · Kao Data</div>
          <div className="h-px w-12 bg-gradient-to-r from-transparent via-primary to-transparent hidden md:block" />
          <div>Used on 40+ live DC projects</div>
        </div>
      </div>

      {/* Floating tech element – bottom-left */}
      <div className="absolute bottom-12 left-12 w-64 h-64 border border-primary/20 rounded-2xl backdrop-blur-xl bg-surface/30 hidden lg:block" />

      {/* Year badge – top-right */}
      <div className="absolute top-32 right-20 text-primary text-xs font-mono tracking-widest opacity-50 hidden md:block">
        2026 · AI-DRIVEN DELIVERY
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-background to-transparent" />
    </section>
  );
}


