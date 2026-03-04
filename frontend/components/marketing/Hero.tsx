import Link from "next/link";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-slate-950">
      {/* Architectural grid background */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(to right, #e2e8f0 1px, transparent 1px)",
          backgroundSize: "64px 64px",
        }}
      />

      {/* Radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(59,130,246,0.08)_0%,transparent_70%)]" />

      <div className="relative z-10 max-w-4xl mx-auto px-6 py-40 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-slate-700 bg-slate-900/80 text-slate-400 text-xs font-medium tracking-wide mb-10">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          AI-native · Infrastructure Bids · Data Centre OS
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6 text-balance">
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">
            aLiGN
          </span>
        </h1>

        <p className="text-xl md:text-2xl text-slate-400 font-light max-w-2xl mx-auto mb-6 text-balance leading-relaxed">
          The operating system for infrastructure bid teams.
        </p>

        <p className="text-base text-slate-500 max-w-xl mx-auto mb-12 text-balance">
          Target the right accounts. Qualify with precision. Build winning bid
          packs. Deliver without gaps. Built for data centre refurbs and new
          builds.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-8 py-3.5 rounded-lg font-semibold text-sm transition-colors"
          >
            Enter Dashboard
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </Link>
          <a
            href="#platform"
            className="inline-flex items-center gap-2 text-slate-400 hover:text-white px-8 py-3.5 rounded-lg font-medium text-sm border border-slate-700 hover:border-slate-600 transition-colors"
          >
            How it works
          </a>
        </div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-slate-950 to-transparent" />
    </section>
  );
}
