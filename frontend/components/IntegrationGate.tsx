'use client';

/**
 * IntegrationGate – wraps any action that requires an external integration.
 *
 * Usage:
 *   <IntegrationGate feature="grok_ai" isConfigured={grokConfigured}>
 *     <button onClick={doAiThing}>Generate</button>
 *   </IntegrationGate>
 *
 * When isConfigured=false, clicking the child intercepts and shows a modal
 * explaining what is missing and how to set it up.
 */

import { useState, cloneElement, isValidElement, ReactElement, ReactNode } from 'react';
import Link from 'next/link';
import { INTEGRATIONS } from '@/lib/integrations';

interface IntegrationGateProps {
  /** Integration id from the INTEGRATIONS registry, e.g. "grok_ai" */
  feature: string;
  /** Pass true when the integration is confirmed configured */
  isConfigured: boolean;
  /** The child element whose onClick will be intercepted when not configured */
  children: ReactNode;
}

export default function IntegrationGate({ feature, isConfigured, children }: IntegrationGateProps) {
  const [showModal, setShowModal] = useState(false);

  const integration = INTEGRATIONS.find((i) => i.id === feature);

  // If configured (or integration unknown), render children as-is
  if (isConfigured || !integration) {
    return <>{children}</>;
  }

  // Intercept click on the child element
  function intercept(child: ReactNode): ReactNode {
    if (isValidElement(child)) {
      return cloneElement(child as ReactElement<{ onClick?: () => void }>, {
        onClick: (e?: React.MouseEvent) => {
          e?.preventDefault?.();
          e?.stopPropagation?.();
          setShowModal(true);
        },
      });
    }
    return <span onClick={() => setShowModal(true)}>{child}</span>;
  }

  return (
    <>
      {intercept(children)}

      {showModal && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="gate-modal-title"
          onClick={(e) => { if (e.target === e.currentTarget) setShowModal(false); }}
        >
          <div className="bg-surface border border-border-subtle rounded-xl p-6 w-full max-w-md space-y-4 shadow-2xl">
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{integration.icon}</span>
                <div>
                  <h3 id="gate-modal-title" className="text-text-main font-semibold">
                    {integration.name} Required
                  </h3>
                  <p className="text-primary text-xs font-mono mt-0.5">Integration not configured</p>
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-text-faint hover:text-text-main text-lg leading-none mt-0.5 flex-shrink-0"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            {/* Description */}
            <p className="text-text-muted text-sm leading-relaxed">{integration.description}</p>

            {/* Missing vars */}
            {integration.requiredServerVars.length > 0 && (
              <div className="bg-background border border-border-subtle rounded-lg p-3">
                <p className="text-warning text-xs font-mono uppercase tracking-wider mb-2">
                  Missing Environment Variables
                </p>
                <div className="flex flex-wrap gap-2">
                  {integration.requiredServerVars.map((v) => (
                    <code key={v} className="text-xs bg-warning/10 text-warning border border-warning/30 rounded px-2 py-0.5 font-mono">
                      {v}
                    </code>
                  ))}
                </div>
              </div>
            )}

            {/* Server-only note */}
            {integration.serverOnlyNote && (
              <div className="bg-error/5 border border-error/20 rounded-lg p-3 flex gap-2">
                <span className="text-error flex-shrink-0">🔒</span>
                <p className="text-error text-xs leading-relaxed">{integration.serverOnlyNote}</p>
              </div>
            )}

            {/* Quick steps */}
            <div>
              <p className="text-text-muted text-xs font-mono uppercase tracking-wider mb-2">Quick Setup</p>
              <ol className="space-y-1.5 list-none">
                {integration.howToGet.slice(0, 3).map((step, i) => (
                  <li key={i} className="flex gap-2 text-xs text-text-muted">
                    <span className="text-primary font-mono flex-shrink-0">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
                {integration.howToGet.length > 3 && (
                  <li className="text-xs text-text-faint italic pl-4">
                    + {integration.howToGet.length - 3} more steps on the Setup page →
                  </li>
                )}
              </ol>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <Link
                href="/setup"
                onClick={() => setShowModal(false)}
                className="flex-1 text-center py-2 bg-primary/10 hover:bg-primary/20 text-primary text-sm font-mono rounded-lg border border-primary/30 transition-all"
              >
                Go to Setup →
              </Link>
              <a
                href={integration.officialLink}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-background hover:bg-surface text-text-muted text-sm rounded-lg border border-border-subtle transition-all"
              >
                {integration.officialLinkLabel} ↗
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
