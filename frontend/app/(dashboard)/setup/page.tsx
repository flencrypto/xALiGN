'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { setupApi, type SetupStatus } from '@/lib/api';
import { INTEGRATIONS } from '@/lib/integrations';
import Link from 'next/link';

function StatusBadge({ configured, optional }: { configured: boolean; optional: boolean }) {
  if (configured) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium bg-success/15 text-success border border-success/30">
        ✓ Configured
      </span>
    );
  }
  if (optional) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium bg-surface text-text-muted border border-border-subtle">
        ○ Optional – not set
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium bg-error/15 text-error border border-error/30">
      ✗ Required – missing
    </span>
  );
}

export default function SetupPage() {
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setupApi.getStatus()
      .then(setStatus)
      .catch(() => setStatus(null))
      .finally(() => setLoading(false));
  }, []);

  const allGood = status?.all_required_configured ?? false;

  return (
    <>
      <Header title="Setup & Integrations" />
      <div className="p-6 space-y-6 max-w-4xl">

        {/* Banner */}
        <div className={`rounded-xl border p-5 flex items-start gap-4 ${
          loading
            ? 'bg-surface border-border-subtle'
            : allGood
            ? 'bg-success/5 border-success/30'
            : 'bg-warning/5 border-warning/30'
        }`}>
          <span className="text-2xl flex-shrink-0">
            {loading ? '⏳' : allGood ? '✅' : '⚠️'}
          </span>
          <div>
            <h2 className="text-text-main font-semibold">
              {loading
                ? 'Checking configuration…'
                : allGood
                ? 'All required integrations are configured'
                : 'Some required integrations are not yet configured'}
            </h2>
            <p className="text-text-muted text-sm mt-1">
              {loading
                ? 'Fetching integration status from the server…'
                : allGood
                ? 'Your aLiGN instance is fully operational. Optional integrations can still be enabled below.'
                : 'Set the missing environment variables on your server and restart. See instructions below.'}
            </p>
          </div>
        </div>

        {/* System info */}
        {status && (
          <div className="bg-surface border border-border-subtle rounded-xl p-4 flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-text-faint text-xs font-mono uppercase">Auth Provider</span>
              <p className="text-text-main font-mono mt-0.5">{status.auth_provider}</p>
            </div>
            <div>
              <span className="text-text-faint text-xs font-mono uppercase">Storage Backend</span>
              <p className="text-text-main font-mono mt-0.5">{status.storage_backend}</p>
            </div>
          </div>
        )}

        {/* Integration cards */}
        <div className="space-y-4">
          {INTEGRATIONS.map((integration) => {
            const serverStatus = status?.integrations[integration.id];
            const configured = serverStatus?.configured ?? false;
            const missingVars = serverStatus?.missing_vars ?? integration.requiredServerVars;

            return (
              <div
                key={integration.id}
                id={integration.id}
                className={`bg-surface border rounded-xl p-5 space-y-4 scroll-mt-4 ${
                  configured
                    ? 'border-border-subtle'
                    : integration.optional
                    ? 'border-border-subtle'
                    : 'border-warning/40'
                }`}
              >
                {/* Header row */}
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{integration.icon}</span>
                    <div>
                      <h3 className="text-text-main font-semibold">{integration.name}</h3>
                      <p className="text-text-muted text-sm mt-0.5">{integration.description}</p>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <StatusBadge configured={loading ? true : configured} optional={integration.optional} />
                  </div>
                </div>

                {/* Missing vars (only when not configured) */}
                {!loading && !configured && missingVars.length > 0 && (
                  <div className="bg-background rounded-lg p-3 border border-border-subtle">
                    <p className="text-xs font-mono text-warning uppercase tracking-wider mb-2">
                      Missing Environment Variables (server-side only)
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {missingVars.map((v) => (
                        <code
                          key={v}
                          className="text-xs bg-warning/10 text-warning border border-warning/30 rounded px-2 py-0.5 font-mono"
                        >
                          {v}
                        </code>
                      ))}
                    </div>
                  </div>
                )}

                {/* All required vars (for reference) */}
                {integration.requiredServerVars.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">
                        Required Server Vars
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {integration.requiredServerVars.map((v) => (
                          <code
                            key={v}
                            className="text-xs bg-background text-text-muted border border-border-subtle rounded px-2 py-0.5 font-mono"
                          >
                            {v}
                          </code>
                        ))}
                      </div>
                    </div>
                    {integration.optionalServerVars && integration.optionalServerVars.length > 0 && (
                      <div>
                        <p className="text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">
                          Optional Server Vars
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {integration.optionalServerVars.map((v) => (
                            <code
                              key={v}
                              className="text-xs bg-background text-text-faint border border-border-subtle rounded px-2 py-0.5 font-mono"
                            >
                              {v}
                            </code>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* How to get it */}
                <div>
                  <p className="text-xs font-mono text-text-faint uppercase tracking-wider mb-2">
                    How to Obtain
                  </p>
                  <ol className="space-y-1.5">
                    {integration.howToGet.map((step, i) => (
                      <li key={i} className="flex gap-2 text-sm text-text-muted">
                        <span className="text-primary font-mono flex-shrink-0 w-5 text-right">{i + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>

                {/* Server-only note */}
                {integration.serverOnlyNote && (
                  <div className="flex gap-2 bg-error/5 border border-error/20 rounded-lg p-3">
                    <span className="text-error flex-shrink-0">🔒</span>
                    <p className="text-error text-xs leading-relaxed">{integration.serverOnlyNote}</p>
                  </div>
                )}

                {/* Used by */}
                {integration.usedBy.length > 0 && (
                  <div>
                    <p className="text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">
                      Used By
                    </p>
                    <ul className="space-y-0.5">
                      {integration.usedBy.map((u, i) => (
                        <li key={i} className="text-xs text-text-muted font-mono">• {u}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Link */}
                <div>
                  <a
                    href={integration.officialLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
                  >
                    {integration.officialLinkLabel} ↗
                  </a>
                </div>
              </div>
            );
          })}
        </div>

        {/* .env example snippet */}
        <div className="bg-surface border border-border-subtle rounded-xl p-5 space-y-3">
          <h2 className="text-primary font-mono text-xs uppercase tracking-widest">.env Quick Reference</h2>
          <pre className="text-xs font-mono text-text-muted bg-background rounded-lg p-4 overflow-x-auto whitespace-pre leading-relaxed">
{`# ── Required for all AI features ─────────────────────────
XAI_API_KEY=xai-your-key-here

# ── Optional: S3 File Storage (default: local) ───────────
# STORAGE_BACKEND=s3
# S3_BUCKET=your-bucket-name
# S3_REGION=eu-west-2
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...

# ── Optional: Authentication (default: none / open) ──────
# AUTH_PROVIDER=clerk
# CLERK_ISSUER=https://your-instance.clerk.accounts.dev
# CLERK_SECRET_KEY=sk_...
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...

# ── Frontend ─────────────────────────────────────────────
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`}
          </pre>
          <p className="text-text-faint text-xs">
            Copy this into a <code className="font-mono">.env</code> file at the backend root, fill in your values, and restart the server.
            Never commit .env files to version control.
          </p>
        </div>

        <div className="text-center pb-4">
          <Link href="/dashboard" className="text-primary text-sm hover:underline">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    </>
  );
}
