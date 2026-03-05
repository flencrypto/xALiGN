import Link from "next/link";

const pillars = [
  { label: "Audit-ready", desc: "Every decision logged and traceable" },
  { label: "Role-based", desc: "Admin, manager, and contributor access" },
  { label: "Agent-extensible", desc: "AI layers on top of structured data" },
  { label: "Scalable", desc: "From a single team to enterprise multi-tenant" },
];

export default function CTA() {
  return (
    <section className="py-32 bg-background border-t border-border-subtle">
      <div className="max-w-6xl mx-auto px-6">
        {/* Investor narrative */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 mb-24">
          <div>
            <p className="text-primary text-sm font-semibold tracking-widest uppercase mb-4">
              The Problem
            </p>
            <h2 className="text-4xl font-bold text-text-main tracking-tight mb-6">
              Infrastructure bids are won and lost on process.
            </h2>
            <p className="text-text-muted leading-relaxed mb-4">
              Data centre refurb and new build projects are complex, high-value,
              and unforgiving. Bid teams operate across spreadsheets, shared
              drives, and disconnected tools — leading to missed compliance,
              undetected scope gaps, and poor handover quality.
            </p>
            <p className="text-text-muted leading-relaxed">
              The cost of a lost bid isn&apos;t just the fee — it&apos;s the
              weeks of team time spent on a disorganised process that could have
              been caught earlier.
            </p>
          </div>
          <div>
            <p className="text-success text-sm font-semibold tracking-widest uppercase mb-4">
              The Category
            </p>
            <h2 className="text-4xl font-bold text-text-main tracking-tight mb-6">
              A new category: Bid Operating System.
            </h2>
            <p className="text-text-muted leading-relaxed mb-4">
              aLiGN isn&apos;t a CRM. It isn&apos;t a document manager.
              It is a structured operating system — purpose-built for
              infrastructure bid teams — that enforces process, surfaces risk,
              and creates institutional knowledge.
            </p>
            <p className="text-text-muted leading-relaxed">
              Powered by AI agents that enrich accounts, score risk, detect
              scope omissions, and validate compliance — automatically.
            </p>
          </div>
        </div>

        {/* Pillars */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-24">
          {pillars.map((p) => (
            <div
              key={p.label}
              className="bg-surface border border-border-subtle rounded-xl p-5"
            >
              <p className="text-text-main font-semibold text-sm mb-2">{p.label}</p>
              <p className="text-text-muted text-xs leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>

        {/* Final CTA */}
        <div className="text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-text-main tracking-tight mb-4">
            Ready to take control?
          </h2>
          <p className="text-text-muted text-lg mb-10 max-w-xl mx-auto">
            Enter the aLiGN platform and start building a structured,
            auditable bid operation.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 bg-primary hover:bg-primary-dark text-text-main px-10 py-4 rounded-lg font-semibold text-base transition-colors"
          >
            Enter Dashboard
            <svg
              className="w-5 h-5"
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
        </div>
      </div>
    </section>
  );
}
