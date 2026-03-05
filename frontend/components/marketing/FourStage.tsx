const stages = [
  {
    number: "01",
    label: "Target",
    title: "Account Intelligence",
    description:
      "Identify and track high-value infrastructure accounts. Monitor trigger signals — expansions, renewals, tenders — before competitors do.",
    detail: "Account scoring · Trigger signals · DC footprint detection",
    color: "text-primary",
    border: "border-blue-500/20",
    bg: "bg-blue-500/5",
  },
  {
    number: "02",
    label: "Qualify",
    title: "Go / No-Go Scoring",
    description:
      "Score every opportunity across technical fit, commercial viability, and risk exposure. Make disciplined bid decisions with structured data.",
    detail: "Weighted scoring · Risk flags · Recommendation engine",
    color: "text-cyan-400",
    border: "border-cyan-500/20",
    bg: "bg-cyan-500/5",
  },
  {
    number: "03",
    label: "Build",
    title: "Bid Pack Assembly",
    description:
      "Assemble compliant, complete bid responses. Auto-generate compliance matrices and RFI lists from uploaded specification documents.",
    detail: "Compliance matrix · RFI generation · Document management",
    color: "text-violet-400",
    border: "border-violet-500/20",
    bg: "bg-violet-500/5",
  },
  {
    number: "04",
    label: "Deliver",
    title: "Scope Gap & Handover",
    description:
      "Detect scope omissions before they become commercial liabilities. Structure handover with full documentation and outstanding item tracking.",
    detail: "Scope gap analysis · Checklist tracking · Handover packs",
    color: "text-emerald-400",
    border: "border-emerald-500/20",
    bg: "bg-emerald-500/5",
  },
];

export default function FourStage() {
  return (
    <section id="platform" className="py-32 bg-background">
      <div className="max-w-6xl mx-auto px-6">
        {/* Header */}
        <div className="max-w-2xl mb-20">
          <p className="text-primary text-sm font-semibold tracking-widest uppercase mb-4">
            The Platform
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-text-main tracking-tight mb-6">
            Four stages.
            <br />
            <span className="text-text-muted font-light">
              One operating system.
            </span>
          </h2>
          <p className="text-text-muted text-lg leading-relaxed">
            aLiGN structures the entire bid lifecycle — from initial
            targeting to structured delivery handover — into a single, auditable
            platform.
          </p>
        </div>

        {/* Stages grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {stages.map((stage) => (
            <div
              key={stage.number}
              className={`${stage.bg} border ${stage.border} rounded-2xl p-8`}
            >
              <div className="flex items-start justify-between mb-6">
                <span className={`text-xs font-bold tracking-widest uppercase ${stage.color}`}>
                  {stage.number} — {stage.label}
                </span>
              </div>
              <h3 className="text-text-main text-2xl font-bold mb-3">
                {stage.title}
              </h3>
              <p className="text-text-muted leading-relaxed mb-6">
                {stage.description}
              </p>
              <p className={`text-xs font-medium ${stage.color} opacity-70`}>
                {stage.detail}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
