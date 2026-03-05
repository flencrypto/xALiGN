'use client';

import { useState } from 'react';
import { swoopApi, SwoopResult, SwoopIntel } from '@/lib/api';

interface Props {
  /** Called after a successful swoop so the parent can refresh its account list. */
  onAccountCreated?: () => void;
}

function safeSocialUrl(raw: string | null | undefined, baseUrl: string): string | null {
  if (!raw) return null;
  try {
    // If already a full https URL, validate it points to the expected domain
    const trimmed = raw.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      const parsed = new URL(trimmed);
      // Only allow https links to expected social domains or explicit full paths
      if (parsed.protocol !== 'https:') return null;
      return parsed.href;
    }
    // Treat as a handle/path – construct the URL from a safe base
    const handle = trimmed.replace(/^[@/]+/, '');
    if (!handle || /[<>"'`\s]/.test(handle)) return null;
    return `${baseUrl}/${encodeURIComponent(handle)}`;
  } catch {
    return null;
  }
}

function IntelPanel({ intel, accountId, created }: { intel: SwoopIntel; accountId: number; created: boolean }) {
  return (
    <div className="mt-4 space-y-3 text-sm">
      {/* Status badge */}
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${created ? 'bg-success/10 border-success/30 text-success' : 'bg-primary/10 border-primary/30 text-primary'}`}>
        <span className="text-base">{created ? '✅' : '🔄'}</span>
        <span className="font-medium">
          {created ? 'New account created' : 'Existing account updated'} — ID #{accountId}
        </span>
      </div>

      {/* Intel summary */}
      {intel.intel_summary && (
        <div className="bg-surface/50 rounded-lg p-3">
          <p className="text-text-muted text-xs font-medium uppercase tracking-wider mb-1">📊 Intel Summary</p>
          <p className="text-text-main">{intel.intel_summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Company details */}
        <div className="bg-surface/50 rounded-lg p-3 space-y-1">
          <p className="text-text-muted text-xs font-medium uppercase tracking-wider mb-2">🏢 Company</p>
          {intel.company_name && <p className="text-text-main font-semibold">{intel.company_name}</p>}
          {intel.type && <p className="text-text-main"><span className="text-text-muted">Type:</span> {intel.type}</p>}
          {intel.location && <p className="text-text-main"><span className="text-text-muted">Location:</span> {intel.location}</p>}
          {intel.stock_ticker && (
            <p className="text-text-main font-mono">
              <span className="text-text-muted">Stock:</span>{' '}
              <span className="text-primary">{intel.stock_ticker}</span>
            </p>
          )}
          {intel.tags && intel.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {intel.tags.map((tag) => (
                <span key={tag} className="px-2 py-0.5 bg-surface rounded text-xs text-text-main">{tag}</span>
              ))}
            </div>
          )}
        </div>

        {/* Suggested touchpoint */}
        {intel.suggested_touchpoint && (
          <div className="bg-primary/10 border border-blue-500/20 rounded-lg p-3">
            <p className="text-primary text-xs font-medium uppercase tracking-wider mb-2">💬 Suggested Touchpoint</p>
            <p className="text-text-main italic text-xs leading-relaxed">&ldquo;{intel.suggested_touchpoint}&rdquo;</p>
          </div>
        )}
      </div>

      {/* Key personnel */}
      {intel.key_personnel && intel.key_personnel.length > 0 && (
        <div className="bg-surface/50 rounded-lg p-3">
          <p className="text-text-muted text-xs font-medium uppercase tracking-wider mb-2">👤 Key Personnel</p>
          <ul className="space-y-2">
            {intel.key_personnel.map((p, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-text-faint text-xs mt-0.5">•</span>
                <div>
                  <span className="text-text-main font-medium">{p.name}</span>
                  {p.role && <span className="text-text-muted text-xs ml-1">– {p.role}</span>}
                  <div className="flex gap-3 mt-0.5">
                    {(() => {
                      const url = safeSocialUrl(p.linkedin, 'https://www.linkedin.com/in');
                      return url ? (
                        <a href={url} target="_blank" rel="noopener noreferrer"
                          className="text-primary text-xs hover:underline">LinkedIn ↗</a>
                      ) : null;
                    })()}
                    {(() => {
                      const url = safeSocialUrl(p.x_handle, 'https://x.com');
                      return url ? (
                        <a href={url} target="_blank" rel="noopener noreferrer"
                          className="text-text-main text-xs hover:underline">✕ {p.x_handle}</a>
                      ) : null;
                    })()}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Triggers */}
        {intel.triggers && intel.triggers.length > 0 && (
          <div className="bg-surface/50 rounded-lg p-3">
            <p className="text-text-muted text-xs font-medium uppercase tracking-wider mb-2">⚡ Trigger Signals</p>
            <ul className="space-y-1">
              {intel.triggers.map((t, i) => (
                <li key={i} className="text-text-main text-xs flex gap-1.5">
                  <span className="text-warning flex-shrink-0">→</span>{t}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recent news */}
        {intel.recent_news && intel.recent_news.length > 0 && (
          <div className="bg-surface/50 rounded-lg p-3">
            <p className="text-text-muted text-xs font-medium uppercase tracking-wider mb-2">📰 Recent News</p>
            <ul className="space-y-1">
              {intel.recent_news.map((n, i) => (
                <li key={i} className="text-text-main text-xs flex gap-1.5">
                  <span className="text-text-faint flex-shrink-0">•</span>{n}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WebsiteSwoop({ onAccountCreated }: Props) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SwoopResult | null>(null);
  const [error, setError] = useState('');

  async function handleSwoop(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await swoopApi.swoop(url.trim());
      setResult(data);
      onAccountCreated?.();
      setUrl('');
    } catch (err: unknown) {
      const msg = (err as Error)?.message ?? 'Swoop failed. Ensure XAI_API_KEY is configured and the URL is accessible.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-surface border border-border-subtle rounded-xl p-5">
      <h2 className="text-text-main font-semibold mb-1">🌐 Website Swoop</h2>
      <p className="text-text-muted text-sm mb-4">
        Enter any company URL – Grok crawls the page and auto-fills a full account record
        including key personnel, trigger signals, recent news, and a suggested LinkedIn touchpoint.
      </p>

      <form onSubmit={handleSwoop} className="flex gap-3">
        <input
          type="url"
          placeholder="https://company.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          disabled={loading}
          className="flex-1 bg-background border border-border-subtle rounded-lg px-4 py-2 text-text-main text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="bg-primary hover:bg-blue-700 disabled:opacity-60 text-text-main px-5 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
        >
          {loading ? '⏳ Swooping…' : '🌐 Swoop'}
        </button>
      </form>

      {error && (
        <p className="text-danger text-sm mt-3 bg-danger/10 border border-danger/30 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {result && <IntelPanel intel={result.intel} accountId={result.account_id} created={result.created} />}
    </div>
  );
}
