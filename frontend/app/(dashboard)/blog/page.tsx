'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { blogApi, BlogPost, BlogPostSummary } from '@/lib/api';
import IntegrationGate from '@/components/IntegrationGate';
import { useSetupStatus } from '@/lib/useSetupStatus';

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-surface text-text-muted border-border-subtle',
  approved: 'bg-warning/20 text-warning border-warning/30',
  published: 'bg-success/20 text-success border-success/30',
};

function statusColor(s: string) {
  return STATUS_COLORS[s] ?? STATUS_COLORS.draft;
}

function formatDate(d?: string) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

interface GenerateForm {
  topic: string;
  tone: string;
  target_persona: string;
  word_count: number;
  seo_keywords: string;
  cta: string;
}

export default function BlogPage() {
  const { isConfigured } = useSetupStatus();
  const grokConfigured = isConfigured('grok_ai');
  const [posts, setPosts] = useState<BlogPostSummary[]>([]);
  const [selected, setSelected] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editBody, setEditBody] = useState('');
  const [error, setError] = useState('');
  const [form, setForm] = useState<GenerateForm>({
    topic: '',
    tone: 'institutional',
    target_persona: 'infrastructure decision-maker',
    word_count: 800,
    seo_keywords: '',
    cta: '',
  });

  useEffect(() => {
    blogApi.list().then(setPosts).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setGenerating(true);
    setError('');
    try {
      const post = await blogApi.generate({
        topic: form.topic,
        tone: form.tone,
        target_persona: form.target_persona,
        word_count: form.word_count,
        seo_keywords: form.seo_keywords || undefined,
        cta: form.cta || undefined,
      });
      setPosts((prev) => [{ id: post.id, title: post.title, slug: post.slug, status: post.status, created_at: post.created_at }, ...prev]);
      setSelected(post);
      setShowGenerate(false);
      setForm({ topic: '', tone: 'institutional', target_persona: 'infrastructure decision-maker', word_count: 800, seo_keywords: '', cta: '' });
    } catch (err: unknown) {
      setError((err as Error)?.message ?? 'Generation failed. Ensure XAI_API_KEY is configured.');
    } finally {
      setGenerating(false);
    }
  }

  async function selectPost(summary: BlogPostSummary) {
    const post = await blogApi.get(summary.id).catch(() => null);
    setSelected(post);
    setEditMode(false);
    setEditBody(post?.body_markdown ?? '');
  }

  async function handleSave() {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await blogApi.update(selected.id, { body_markdown: editBody });
      setSelected(updated);
      setEditMode(false);
      setPosts((prev) => prev.map((p) => p.id === updated.id ? { ...p, title: updated.title } : p));
    } finally {
      setSaving(false);
    }
  }

  async function handleApprove() {
    if (!selected) return;
    const updated = await blogApi.approve(selected.id).catch((err) => { setError(err?.message); return null; });
    if (updated) {
      setSelected(updated);
      setPosts((prev) => prev.map((p) => p.id === updated.id ? { ...p, status: updated.status } : p));
    }
  }

  async function handlePublish() {
    if (!selected) return;
    const updated = await blogApi.publish(selected.id).catch((err) => { setError(err?.message); return null; });
    if (updated) {
      setSelected(updated);
      setPosts((prev) => prev.map((p) => p.id === updated.id ? { ...p, status: updated.status } : p));
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this blog post?')) return;
    await blogApi.delete(id).catch(() => {});
    setPosts((prev) => prev.filter((p) => p.id !== id));
    if (selected?.id === id) setSelected(null);
  }

  return (
    <>
      <Header title="News Feed" />
      <div className="p-6 space-y-6">
        {/* Top bar */}
        <div className="flex items-center justify-between">
          <p className="text-text-muted text-sm">{posts.length} blog post{posts.length !== 1 ? 's' : ''}</p>
          <IntegrationGate feature="grok_ai" isConfigured={grokConfigured}>
            <button
              onClick={() => setShowGenerate(true)}
              className="bg-primary hover:bg-blue-700 text-text-main px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              ✍️ Generate Post
            </button>
          </IntegrationGate>
        </div>

        {/* Generate Modal */}
        {showGenerate && (
          <div
            className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="generate-modal-title"
          >
            <div className="bg-surface border border-border-subtle rounded-xl p-6 w-full max-w-lg space-y-4">
              <h3 id="generate-modal-title" className="text-text-main font-semibold text-lg">Generate Blog Post with Grok AI</h3>
              {error && <p className="text-danger text-sm">{error}</p>}
              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-text-muted text-xs mb-1">Topic / Title</label>
                  <input
                    type="text"
                    value={form.topic}
                    onChange={(e) => setForm((f) => ({ ...f, topic: e.target.value }))}
                    required
                    className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    placeholder="e.g. Data Centre Expansion Trends in 2025"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="blog-tone" className="block text-text-muted text-xs mb-1">Tone</label>
                    <select
                      id="blog-tone"
                      value={form.tone}
                      onChange={(e) => setForm((f) => ({ ...f, tone: e.target.value }))}
                      className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm focus:outline-none focus:border-blue-500"
                    >
                      <option value="institutional">Institutional</option>
                      <option value="conversational">Conversational</option>
                      <option value="technical">Technical</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="blog-word-count" className="block text-text-muted text-xs mb-1">Word Count</label>
                    <input
                      id="blog-word-count"
                      type="number"
                      min={300}
                      max={3000}
                      value={form.word_count}
                      onChange={(e) => setForm((f) => ({ ...f, word_count: Number(e.target.value) }))}
                      className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-text-muted text-xs mb-1">Target Persona</label>
                  <input
                    type="text"
                    value={form.target_persona}
                    onChange={(e) => setForm((f) => ({ ...f, target_persona: e.target.value }))}
                    className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    placeholder="infrastructure decision-maker"
                  />
                </div>
                <div>
                  <label className="block text-text-muted text-xs mb-1">SEO Keywords (optional)</label>
                  <input
                    type="text"
                    value={form.seo_keywords}
                    onChange={(e) => setForm((f) => ({ ...f, seo_keywords: e.target.value }))}
                    className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    placeholder="data centre, MEP, refurbishment"
                  />
                </div>
                <div>
                  <label className="block text-text-muted text-xs mb-1">CTA (optional)</label>
                  <input
                    type="text"
                    value={form.cta}
                    onChange={(e) => setForm((f) => ({ ...f, cta: e.target.value }))}
                    className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    placeholder="Contact us for a free scope review"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={generating}
                    className="flex-1 bg-primary hover:bg-blue-700 disabled:opacity-60 text-text-main py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    {generating ? '⏳ Generating…' : '✍️ Generate'}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowGenerate(false); setError(''); }}
                    className="px-4 py-2 bg-background hover:bg-surface text-text-main rounded-lg text-sm transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Post List */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <h2 className="text-text-main font-semibold mb-4">Posts</h2>
            {loading ? (
              <div className="space-y-2" aria-label="Loading blog posts">{[...Array(3)].map((_, i) => <div key={i} className="h-14 bg-background rounded animate-pulse" />)}</div>
            ) : posts.length === 0 ? (
              <p className="text-text-muted text-sm">No posts yet. Generate one with Grok AI.</p>
            ) : (
              <ul className="space-y-2">
                {posts.map((p) => (
                  <li
                    key={p.id}
                    onClick={() => selectPost(p)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${selected?.id === p.id ? 'bg-primary/20 border border-blue-500/40' : 'hover:bg-background border border-border-subtle'}`}
                  >
                    <p className="text-text-main text-sm font-medium line-clamp-2">{p.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium border ${statusColor(p.status)}`}>{p.status}</span>
                      <span className="text-text-faint text-xs">{formatDate(p.created_at)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Post Detail */}
          <div className="lg:col-span-2">
            {!selected ? (
              <div className="bg-surface border border-border-subtle rounded-xl p-10 text-center">
                <p className="text-text-muted">Select a post or generate a new one.</p>
              </div>
            ) : (
              <div className="bg-surface border border-border-subtle rounded-xl p-5 space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-text-main font-semibold text-lg">{selected.title}</h3>
                    <p className="text-text-muted text-sm">/{selected.slug}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium border flex-shrink-0 ${statusColor(selected.status)}`}>
                    {selected.status}
                  </span>
                </div>

                {error && <p className="text-danger text-sm">{error}</p>}

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  {selected.status === 'draft' && (
                    <button onClick={handleApprove} className="bg-yellow-600 hover:bg-yellow-700 text-text-main px-3 py-1.5 rounded text-xs font-medium transition-colors">
                      ✓ Approve
                    </button>
                  )}
                  {selected.status === 'approved' && (
                    <button onClick={handlePublish} className="bg-green-600 hover:bg-green-700 text-text-main px-3 py-1.5 rounded text-xs font-medium transition-colors">
                      🚀 Publish
                    </button>
                  )}
                  <button
                    onClick={() => { setEditMode(!editMode); setEditBody(selected.body_markdown); }}
                    className="bg-surface hover:bg-primary/20 text-text-main px-3 py-1.5 rounded text-xs font-medium transition-colors"
                  >
                    {editMode ? 'Cancel Edit' : '✏️ Edit'}
                  </button>
                  <button
                    onClick={() => handleDelete(selected.id)}
                    className="bg-red-600/20 hover:bg-red-600/40 text-danger px-3 py-1.5 rounded text-xs font-medium transition-colors"
                  >
                    🗑 Delete
                  </button>
                </div>

                {/* Meta */}
                {selected.meta_description && (
                  <div className="bg-background/40 rounded-lg p-3">
                    <p className="text-text-muted text-xs mb-1">Meta Description</p>
                    <p className="text-text-main text-sm">{selected.meta_description}</p>
                  </div>
                )}

                {/* Body */}
                {editMode ? (
                  <div className="space-y-3">
                    <textarea
                      aria-label="Edit blog post content"
                      value={editBody}
                      onChange={(e) => setEditBody(e.target.value)}
                      rows={20}
                      className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm font-mono focus:outline-none focus:border-blue-500"
                    />
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="bg-primary hover:bg-blue-700 disabled:opacity-60 text-text-main px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      {saving ? 'Saving…' : 'Save'}
                    </button>
                  </div>
                ) : (
                  <div className="bg-background/40 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                    <pre className="text-text-main text-sm whitespace-pre-wrap font-sans">{selected.body_markdown}</pre>
                  </div>
                )}

                {/* Social Variants */}
                {(selected.linkedin_variant || selected.x_variant) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selected.linkedin_variant && (
                      <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
                        <p className="text-primary text-xs font-medium mb-2">LinkedIn Post</p>
                        <p className="text-text-main text-sm">{selected.linkedin_variant}</p>
                      </div>
                    )}
                    {selected.x_variant && (
                      <div className="bg-background/40 border border-border-subtle rounded-lg p-4">
                        <p className="text-text-muted text-xs font-medium mb-2">𝕏 Post</p>
                        <p className="text-text-main text-sm">{selected.x_variant}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
