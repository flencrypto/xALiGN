'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { intelApi, uploadsApi, CompanyIntel, CompanyIntelSummary, NewsItem, UploadedPhoto } from '@/lib/api';

const CATEGORY_COLORS: Record<string, string> = {
  expansion: 'bg-success/20 text-success border-success/30',
  earnings: 'bg-primary/20 text-primary border-primary/30',
  technology: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  competitor: 'bg-danger/20 text-danger border-danger/30',
  hiring: 'bg-warning/20 text-warning border-warning/30',
  funding: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  general: 'bg-surface text-text-muted border-border-subtle',
};

function categoryColor(cat: string) {
  return CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.general;
}

function formatDate(d?: string) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function tryParseJson(val?: string | null): string {
  if (!val) return '—';
  try {
    const parsed = JSON.parse(val);
    if (Array.isArray(parsed)) return parsed.join(', ');
    return String(parsed);
  } catch {
    return val;
  }
}

export default function IntelPage() {
  const [companies, setCompanies] = useState<CompanyIntelSummary[]>([]);
  const [selected, setSelected] = useState<CompanyIntel | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [photos, setPhotos] = useState<UploadedPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [researching, setResearching] = useState(false);
  const [websiteInput, setWebsiteInput] = useState('');
  const [error, setError] = useState('');
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [photoAlt, setPhotoAlt] = useState('');

  useEffect(() => {
    Promise.all([
      intelApi.listCompanies().catch(() => []),
      intelApi.listNews().catch(() => []),
    ]).then(([cos, ns]) => {
      setCompanies(cos);
      setNews(ns);
    }).finally(() => setLoading(false));
  }, []);

  async function handleResearch(e: React.FormEvent) {
    e.preventDefault();
    if (!websiteInput.trim()) return;
    setResearching(true);
    setError('');
    try {
      const intel = await intelApi.researchCompany(websiteInput.trim());
      setCompanies((prev) => [{ id: intel.id, website: intel.website, company_name: intel.company_name, created_at: intel.created_at }, ...prev]);
      setSelected(intel);
      setWebsiteInput('');
    } catch (err: unknown) {
      setError((err as Error)?.message ?? 'Research failed. Ensure XAI_API_KEY is configured.');
    } finally {
      setResearching(false);
    }
  }

  async function selectCompany(summary: CompanyIntelSummary) {
    const intel = await intelApi.getCompany(summary.id).catch(() => null);
    setSelected(intel);
    if (intel) {
      const [ns, ps] = await Promise.all([
        intelApi.listNews(intel.id).catch(() => []),
        uploadsApi.list({ company_intel_id: intel.id }).catch(() => []),
      ]);
      setNews(ns);
      setPhotos(ps);
    }
  }

  async function handleDeleteCompany(id: number) {
    if (!confirm('Delete this intelligence snapshot?')) return;
    await intelApi.deleteCompany(id).catch(() => {});
    setCompanies((prev) => prev.filter((c) => c.id !== id));
    if (selected?.id === id) setSelected(null);
  }

  async function handlePhotoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selected) return;
    setUploadingPhoto(true);
    try {
      const photo = await uploadsApi.uploadPhoto(file, {
        alt_text: photoAlt || undefined,
        company_intel_id: selected.id,
      });
      setPhotos((prev) => [photo, ...prev]);
      setPhotoAlt('');
    } catch (err: unknown) {
      setError((err as Error)?.message ?? 'Upload failed');
    } finally {
      setUploadingPhoto(false);
      e.target.value = '';
    }
  }

  async function handleDeletePhoto(photoId: number) {
    await uploadsApi.delete(photoId).catch(() => {});
    setPhotos((prev) => prev.filter((p) => p.id !== photoId));
  }

  return (
    <>
      <Header title="Company Intelligence" />
      <div className="p-6 space-y-6">
        {/* Research Form */}
        <div className="bg-surface border border-border-subtle rounded-xl p-5">
          <h2 className="text-text-main font-semibold mb-3">🔍 Deep Research a Company</h2>
          <p className="text-text-muted text-sm mb-4">
            Enter a company website URL. Grok AI will crawl public pages and extract structured intelligence signals.
          </p>
          <form onSubmit={handleResearch} className="flex gap-3">
            <input
              type="url"
              placeholder="https://example.com"
              value={websiteInput}
              onChange={(e) => setWebsiteInput(e.target.value)}
              className="flex-1 bg-background border border-border-subtle rounded-lg px-4 py-2 text-text-main text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500"
              required
            />
            <button
              type="submit"
              disabled={researching}
              className="bg-primary hover:bg-blue-700 disabled:opacity-60 text-text-main px-5 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              {researching ? '⏳ Researching…' : 'Research'}
            </button>
          </form>
          {error && <p className="text-danger text-sm mt-2">{error}</p>}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Company List */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-text-main font-semibold mb-4">Tracked Companies</h2>
            {loading ? (
              <div className="space-y-2" aria-label="Loading companies">{[...Array(3)].map((_, i) => <div key={i} className="h-12 bg-background rounded animate-pulse" />)}</div>
            ) : companies.length === 0 ? (
              <p className="text-text-muted text-sm">No companies tracked yet.</p>
            ) : (
              <ul className="space-y-2">
                {companies.map((c) => (
                  <li
                    key={c.id}
                    className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${selected?.id === c.id ? 'bg-primary/20 border border-blue-500/40' : 'hover:bg-background border border-border-subtle'}`}
                    onClick={() => selectCompany(c)}
                  >
                    <div>
                      <p className="text-text-main text-sm font-medium">{c.company_name || c.website}</p>
                      <p className="text-text-muted text-xs">{formatDate(c.created_at)}</p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteCompany(c.id); }}
                      className="text-text-faint hover:text-danger text-xs ml-2 transition-colors"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Intelligence Detail */}
          <div className="lg:col-span-2 space-y-4">
            {!selected ? (
              <div className="bg-surface border border-border-subtle rounded-xl p-10 text-center">
                <p className="text-text-muted">Select a company or run research to see intelligence.</p>
              </div>
            ) : (
              <>
                {/* Company Summary */}
                <div className="bg-surface border border-border-subtle rounded-xl p-5">
                  <h3 className="text-text-main font-semibold text-lg mb-4">
                    {selected.company_name || selected.website}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    {[
                      { label: '📍 Locations', value: selected.locations },
                      { label: '💼 Business Model', value: selected.business_model },
                      { label: '📈 Expansion Signals', value: selected.expansion_signals },
                      { label: '🤖 Technology Indicators', value: selected.technology_indicators },
                      { label: '💰 Financial Summary', value: selected.financial_summary },
                      { label: '📢 Earnings Highlights', value: selected.earnings_highlights },
                      { label: '⚔️ Competitor Mentions', value: selected.competitor_mentions },
                      { label: '⚠️ Strategic Risks', value: selected.strategic_risks },
                      { label: '🎯 Bid Opportunities', value: selected.bid_opportunities },
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-background/40 rounded-lg p-3">
                        <p className="text-text-muted text-xs mb-1">{label}</p>
                        <p className="text-text-main text-sm">{tryParseJson(value)}</p>
                      </div>
                    ))}
                    {/* Stock price / ticker */}
                    {(selected.stock_ticker || selected.stock_price) && (
                      <div className="bg-background/40 rounded-lg p-3">
                        <p className="text-text-muted text-xs mb-1">📊 Stock</p>
                        <p className="text-text-main text-sm font-mono">
                          {selected.stock_ticker && <span className="text-primary mr-2">{selected.stock_ticker}</span>}
                          {selected.stock_price || '—'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Social Media Posts */}
                {(selected.linkedin_posts || selected.x_posts) && (
                  <div className="bg-surface border border-border-subtle rounded-xl p-5">
                    <h3 className="text-text-main font-semibold mb-4">📣 Recent Social Media</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {selected.linkedin_posts && (() => {
                        const posts: string[] = (() => {
                          try { return JSON.parse(selected.linkedin_posts!) as string[]; } catch { return [selected.linkedin_posts!]; }
                        })();
                        return posts.length > 0 ? (
                          <div>
                            <p className="text-primary text-xs font-semibold uppercase tracking-wider mb-2">🔗 LinkedIn</p>
                            <ul className="space-y-2">
                              {posts.map((post, i) => (
                                <li key={i} className="bg-background/40 rounded-lg p-3 text-text-main text-sm">
                                  {post}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : null;
                      })()}
                      {selected.x_posts && (() => {
                        const posts: string[] = (() => {
                          try { return JSON.parse(selected.x_posts!) as string[]; } catch { return [selected.x_posts!]; }
                        })();
                        return posts.length > 0 ? (
                          <div>
                            <p className="text-text-main text-xs font-semibold uppercase tracking-wider mb-2">✕ X.com</p>
                            <ul className="space-y-2">
                              {posts.map((post, i) => (
                                <li key={i} className="bg-background/40 rounded-lg p-3 text-text-main text-sm">
                                  {post}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : null;
                      })()}
                    </div>
                  </div>
                )}

                {/* Executive Profiles */}
                {selected.executives && selected.executives.length > 0 && (
                  <div className="bg-surface border border-border-subtle rounded-xl p-5">
                    <h3 className="text-text-main font-semibold mb-4">👤 Executive Profiles (Public)</h3>
                    <div className="space-y-4">
                      {selected.executives.map((exec) => (
                        <div key={exec.id} className="bg-background/40 rounded-lg p-4">
                          <p className="text-text-main font-medium">{exec.name}</p>
                          {exec.role && <p className="text-text-muted text-sm">{exec.role}</p>}
                          {exec.professional_focus && (
                            <p className="text-text-main text-sm mt-2">
                              <span className="text-text-muted">Focus: </span>{tryParseJson(exec.professional_focus)}
                            </p>
                          )}
                          {exec.conversation_angles && (
                            <p className="text-text-main text-sm mt-1">
                              <span className="text-text-muted">💬 Rapport angle: </span>{tryParseJson(exec.conversation_angles)}
                            </p>
                          )}
                          {exec.conference_appearances && (
                            <p className="text-text-main text-sm mt-1">
                              <span className="text-text-muted">🎤 Conferences: </span>{tryParseJson(exec.conference_appearances)}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Photo Uploader */}
                <div className="bg-surface border border-border-subtle rounded-xl p-5">
                  <h3 className="text-text-main font-semibold mb-4">📷 Photos & Documents</h3>
                  <div className="flex gap-3 mb-4">
                    <input
                      type="text"
                      placeholder="Alt text / description (optional)"
                      value={photoAlt}
                      onChange={(e) => setPhotoAlt(e.target.value)}
                      className="flex-1 bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    />
                    <label className={`bg-primary hover:bg-blue-700 text-text-main px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors ${uploadingPhoto ? 'opacity-60 cursor-not-allowed' : ''}`}>
                      {uploadingPhoto ? '⏳ Uploading…' : '⬆ Upload'}
                      <input
                        type="file"
                        className="hidden"
                        accept="image/*,.pdf"
                        onChange={handlePhotoUpload}
                        disabled={uploadingPhoto}
                      />
                    </label>
                  </div>
                  {photos.length === 0 ? (
                    <p className="text-text-muted text-sm">No photos uploaded yet.</p>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {photos.map((photo) => (
                        <div key={photo.id} className="bg-background/40 rounded-lg p-3 relative">
                          {photo.content_type?.startsWith('image/') ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={uploadsApi.fileUrl(photo.id)}
                              alt={photo.alt_text || 'Uploaded photo'}
                              className="w-full h-24 object-cover rounded mb-2"
                            />
                          ) : (
                            <div className="w-full h-24 flex items-center justify-center bg-surface rounded mb-2">
                              <span className="text-3xl">📄</span>
                            </div>
                          )}
                          <p className="text-text-main text-xs truncate">{photo.original_filename}</p>
                          {photo.alt_text && <p className="text-text-muted text-xs truncate">{photo.alt_text}</p>}
                          <div className="flex gap-2 mt-2">
                            <a
                              href={uploadsApi.fileUrl(photo.id)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary text-xs hover:underline"
                            >
                              View
                            </a>
                            <button
                              onClick={() => handleDeletePhoto(photo.id)}
                              className="text-danger text-xs hover:underline"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* News Feed */}
        <div className="bg-surface border border-border-subtle rounded-xl p-5">
          <h2 className="text-text-main font-semibold mb-4">📰 News & Intelligence Feed</h2>
          {news.length === 0 ? (
            <p className="text-text-muted text-sm">No news items tracked. Research a company to populate the feed.</p>
          ) : (
            <div className="space-y-3">
              {news.map((item) => (
                <div key={item.id} className="flex items-start gap-4 p-3 bg-background/40 rounded-lg">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0 ${categoryColor(item.category)}`}>
                    {item.category}
                  </span>
                  <div className="min-w-0">
                    <p className="text-text-main text-sm font-medium">{item.title}</p>
                    {item.summary && <p className="text-text-muted text-xs mt-0.5 line-clamp-2">{item.summary}</p>}
                    {item.source_url && (
                      <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-primary text-xs hover:underline">
                        Source ↗
                      </a>
                    )}
                  </div>
                  <p className="text-text-faint text-xs flex-shrink-0">{formatDate(item.detected_at)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
