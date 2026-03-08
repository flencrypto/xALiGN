'use client';

import { useEffect, useRef, useState } from 'react';
import Header from '@/components/layout/Header';
import WebsiteSwoop from '@/components/WebsiteSwoop';
import { accountsApi, accountsCsvApi, callsApi, Account, Contact, TriggerSignal, CallIntelligence, CsvImportResult } from '@/lib/api';

const ACCOUNT_TYPES = ['All', 'operator', 'hyperscaler', 'developer', 'colo', 'enterprise'];

const SIGNAL_COLORS: Record<string, string> = {
  planning: 'bg-success/20 text-success border-success/30',
  framework_award: 'bg-primary/20 text-primary border-primary/30',
  hiring_spike: 'bg-danger/20 text-danger border-danger/30',
  grid: 'bg-warning/20 text-warning border-warning/30',
  land_acquisition: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  roadworks: 'bg-surface text-text-muted border-border-subtle',
  default: 'bg-surface text-text-muted border-border-subtle',
};

function signalColor(type: string) {
  return SIGNAL_COLORS[type?.toLowerCase()] ?? SIGNAL_COLORS.default;
}

interface NewAccountForm {
  name: string;
  type: string;
  stage: string;
  location: string;
  website: string;
  logo_url: string;
  tags: string;
  notes: string;
}

interface NewContactForm {
  name: string;
  role: string;
  email: string;
  phone: string;
}

interface NewSignalForm {
  signal_type: string;
  title: string;
  description: string;
  source_url: string;
}

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [selected, setSelected] = useState<Account | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [signals, setSignals] = useState<TriggerSignal[]>([]);
    const [calls, setCalls] = useState<CallIntelligence[]>([]);
  const [showNewAccount, setShowNewAccount] = useState(false);
  const [showNewContact, setShowNewContact] = useState(false);
  const [showNewSignal, setShowNewSignal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newAccount, setNewAccount] = useState<NewAccountForm>({ name: '', type: 'operator', stage: 'Target', location: '', website: '', logo_url: '', tags: '', notes: '' });
  const [newContact, setNewContact] = useState<NewContactForm>({ name: '', role: '', email: '', phone: '' });
  const [newSignal, setNewSignal] = useState<NewSignalForm>({ signal_type: 'planning', title: '', description: '', source_url: '' });
  const [csvImporting, setCsvImporting] = useState(false);
  const [csvResult, setCsvResult] = useState<CsvImportResult | null>(null);
  const csvInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    accountsApi.list().then(setAccounts).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function selectAccount(acc: Account) {
    setSelected(acc);
    const [c, s, calls] = await Promise.all([
      accountsApi.listContacts(acc.id).catch(() => []),
      accountsApi.listTriggerSignals(acc.id).catch(() => []),
      callsApi.list({ account_id: acc.id }).catch(() => []),
    ]);
    setContacts(c);
    setSignals(s);
    setCalls(calls);
  }

  async function handleCreateAccount(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const acc = await accountsApi.create(newAccount);
      setAccounts((prev) => [...prev, acc]);
      setShowNewAccount(false);
      setNewAccount({ name: '', type: 'operator', stage: 'Target', location: '', website: '', logo_url: '', tags: '', notes: '' });
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateContact(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setSaving(true);
    try {
      const c = await accountsApi.createContact(selected.id, newContact);
      setContacts((prev) => [...prev, c]);
      setShowNewContact(false);
      setNewContact({ name: '', role: '', email: '', phone: '' });
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateSignal(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setSaving(true);
    try {
      const s = await accountsApi.createTriggerSignal(selected.id, newSignal);
      setSignals((prev) => [...prev, s]);
      setShowNewSignal(false);
      setNewSignal({ signal_type: 'planning', title: '', description: '', source_url: '' });
    } finally {
      setSaving(false);
    }
  }

  async function handleCsvImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvImporting(true);
    setCsvResult(null);
    try {
      const result = await accountsCsvApi.import(file);
      setCsvResult(result);
      // Refresh accounts list after import
      const updated = await accountsApi.list().catch(() => accounts);
      setAccounts(updated);
    } catch (err: unknown) {
      setCsvResult({
        created: 0,
        skipped: 0,
        errors: [(err as Error)?.message ?? 'Import failed'],
        message: 'Import failed.',
      });
    } finally {
      setCsvImporting(false);
      if (csvInputRef.current) csvInputRef.current.value = '';
    }
  }

  const filtered = filter === 'All' ? accounts : accounts.filter((a) => a.type === filter);

  return (
    <>
      <Header
        title="Account Intelligence"
        action={
          <div className="flex gap-2 flex-wrap">
            {/* CSV toolbar */}
            <a
              href={accountsCsvApi.templateUrl()}
              download="accounts_import_template.csv"
              className="bg-background hover:bg-surface text-text-main px-3 py-2 rounded-lg text-xs font-medium transition-colors border border-border-subtle"
            >
              ⬇ Template
            </a>
            <label className={`bg-background hover:bg-surface text-text-main px-3 py-2 rounded-lg text-xs font-medium transition-colors border border-border-subtle cursor-pointer ${csvImporting ? 'opacity-60 cursor-not-allowed' : ''}`}>
              {csvImporting ? '⏳ Importing…' : '⬆ Import CSV'}
              <input
                ref={csvInputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleCsvImport}
                disabled={csvImporting}
              />
            </label>
            <a
              href={accountsCsvApi.exportUrl()}
              download="accounts_export.csv"
              className="bg-background hover:bg-surface text-text-main px-3 py-2 rounded-lg text-xs font-medium transition-colors border border-border-subtle"
            >
              ⬇ Export CSV
            </a>
            <button
              onClick={() => setShowNewAccount(true)}
              className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              + New Account
            </button>
          </div>
        }
      />

      {/* CSV import result banner */}
      {csvResult && (
        <div className={`mx-6 mt-4 p-4 rounded-lg border text-sm ${csvResult.errors.length === 0 ? 'bg-success/10 border-success/30 text-success' : 'bg-warning/10 border-warning/30 text-warning'}`}>
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium">{csvResult.message}</span>
            <button onClick={() => setCsvResult(null)} className="text-text-muted hover:text-text-main ml-4">✕</button>
          </div>
          {csvResult.errors.length > 0 && (
            <ul className="list-disc list-inside space-y-0.5 mt-2 text-xs text-warning">
              {csvResult.errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
                    {/* Calls */}
                    <div className="mb-5">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-text-main text-sm font-semibold">Calls ({calls.length})</h3>
                        <a 
                          href="/calls" 
                          className="text-primary hover:text-primary text-xs"
                        >
                          View All →
                        </a>
                      </div>
                      {calls.length === 0 ? (
                        <p className="text-text-faint text-xs">No call records yet.</p>
                      ) : (
                        <ul className="space-y-2">
                          {calls.map((call) => {
                            const sentimentColor = 
                              call.sentiment_score == null ? 'text-text-muted' :
                              call.sentiment_score >= 0.5 ? 'text-emerald-400' :
                              call.sentiment_score >= 0 ? 'text-primary' :
                              call.sentiment_score >= -0.5 ? 'text-amber-400' : 'text-danger';
                    
                            return (
                              <li key={call.id} className="bg-surface/50 rounded-lg px-3 py-2">
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex-1 min-w-0">
                                    {call.executive_name && (
                                      <p className="text-text-main text-sm font-medium truncate">{call.executive_name}</p>
                                    )}
                                    <p className="text-text-muted text-xs">
                                      {call.call_date 
                                        ? new Date(call.call_date).toLocaleDateString()
                                        : call.created_at 
                                        ? new Date(call.created_at).toLocaleDateString()
                                        : 'No date'}
                                    </p>
                                    {call.key_points && call.key_points.length > 0 && (
                                      <p className="text-text-faint text-xs mt-1">
                                        {call.key_points.length} key point{call.key_points.length > 1 ? 's' : ''}
                                      </p>
                                    )}
                                  </div>
                                  {call.sentiment_score != null && (
                                    <span className={`text-xs font-medium ${sentimentColor}`}>
                                      {call.sentiment_score > 0 ? '+' : ''}{call.sentiment_score.toFixed(2)}
                                    </span>
                                  )}
                                </div>
                                {call.audio_file_url && (
                                  <div className="mt-2">
                                    <audio controls className="w-full h-8" style={{ maxHeight: '32px' }}>
                                      <source src={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${call.audio_file_url}`} />
                                    </audio>
                                  </div>
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </div>

        </div>
      )}

      {/* Website Swoop */}
      <div className="px-6 pt-4">
        <WebsiteSwoop
          onAccountCreated={() => {
            accountsApi.list().then(setAccounts).catch(console.error);
          }}
        />
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Main table */}
        <div className="flex-1 p-6 overflow-auto">
          {/* Filter */}
          <div className="flex gap-2 mb-4 flex-wrap">
            {ACCOUNT_TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setFilter(t)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  filter === t
                    ? 'bg-primary border-blue-600 text-text-main'
                    : 'bg-surface border-border-subtle text-text-main hover:border-primary/50'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-surface rounded animate-pulse" />)}</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-4xl mb-3">🏢</p>
              <p className="text-text-muted">No accounts yet. Add your first account or import from CSV.</p>
            </div>
          ) : (
            <div className="bg-surface border border-border-subtle rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-subtle">
                    <th className="text-left px-4 py-3 text-text-muted font-medium">Name</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">Type</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium hidden md:table-cell">Location</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium hidden lg:table-cell">Website</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium hidden lg:table-cell">Stage</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((acc) => (
                    <tr
                      key={acc.id}
                      onClick={() => selectAccount(acc)}
                      className={`border-b border-border-subtle/50 cursor-pointer transition-colors hover:bg-surface/50 ${
                        selected?.id === acc.id ? 'bg-background/70' : ''
                      }`}
                    >
                      <td className="px-4 py-3 text-text-main font-medium flex items-center gap-2">
                        {acc.logo_url && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={acc.logo_url} alt={`${acc.name} logo`} className="h-6 w-6 object-contain rounded" />
                        )}
                        {acc.name}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-primary/20 text-primary rounded text-xs border border-primary/30">{acc.type}</span>
                      </td>
                      <td className="px-4 py-3 text-text-main hidden md:table-cell">{acc.location ?? '—'}</td>
                      <td className="px-4 py-3 text-text-main hidden lg:table-cell">
                        {acc.website ? (
                          <a href={acc.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline text-xs" onClick={(e) => e.stopPropagation()}>
                            {acc.website.replace(/^https?:\/\//, '')}
                          </a>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-3 text-text-main hidden lg:table-cell">{acc.stage ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Side panel */}
        {selected && (
          <div className="w-80 xl:w-96 border-l border-border-subtle bg-surface overflow-auto p-5 flex-shrink-0">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {selected.logo_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={selected.logo_url} alt={`${selected.name} logo`} className="h-8 w-8 object-contain rounded" />
                )}
                <h2 className="text-text-main font-semibold text-lg truncate">{selected.name}</h2>
              </div>
              <button onClick={() => setSelected(null)} className="text-text-muted hover:text-text-main ml-2">✕</button>
            </div>
            <div className="space-y-2 text-sm mb-5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 bg-primary/20 text-primary rounded text-xs border border-primary/30">{selected.type}</span>
                {selected.stage && <span className="px-2 py-0.5 bg-success/20 text-success rounded text-xs border border-success/30">{selected.stage}</span>}
                {selected.tier_target && <span className="px-2 py-0.5 bg-surface text-text-main rounded text-xs">{selected.tier_target}</span>}
              </div>
              <p className="text-text-muted">Location: <span className="text-text-main">{selected.location ?? '—'}</span></p>
              <p className="text-text-muted">Website:{' '}
                {selected.website ? (
                  <a href={selected.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    {selected.website.replace(/^https?:\/\//, '')}
                  </a>
                ) : <span className="text-text-main">—</span>}
              </p>
              {selected.annual_revenue != null && (
                <p className="text-text-muted">Revenue: <span className="text-text-main">${selected.annual_revenue.toLocaleString()}</span></p>
              )}
              {selected.tags && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {selected.tags.split(',').map((t) => t.trim()).filter(Boolean).map((tag) => (
                    <span key={tag} className="px-2 py-0.5 bg-background rounded text-xs text-text-main">{tag}</span>
                  ))}
                </div>
              )}
              {selected.notes && (
                <div className="bg-background/40 rounded-lg p-3 mt-2">
                  <p className="text-text-main text-xs whitespace-pre-wrap">{selected.notes}</p>
                </div>
              )}
            </div>

            {/* Contacts */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-text-main text-sm font-semibold">Contacts ({contacts.length})</h3>
                <button onClick={() => setShowNewContact(true)} className="text-primary hover:text-primary text-xs">+ Add</button>
              </div>
              {contacts.length === 0 ? (
                <p className="text-text-faint text-xs">No contacts yet.</p>
              ) : (
                <ul className="space-y-2">
                  {contacts.map((c) => (
                    <li key={c.id} className="bg-surface/50 rounded-lg px-3 py-2">
                      <p className="text-text-main text-sm font-medium">{c.name}</p>
                      <p className="text-text-muted text-xs">{c.role} {c.email && `· ${c.email}`}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Trigger Signals */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-text-main text-sm font-semibold">Trigger Signals ({signals.length})</h3>
                <button onClick={() => setShowNewSignal(true)} className="text-primary hover:text-primary text-xs">+ Add</button>
              </div>
              {signals.length === 0 ? (
                <p className="text-text-faint text-xs">No signals yet.</p>
              ) : (
                <ul className="space-y-2">
                  {signals.map((s) => (
                    <li key={s.id} className="bg-surface/50 rounded-lg px-3 py-2">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${signalColor(s.signal_type)}`}>{s.signal_type}</span>
                      </div>
                      <p className="text-text-main text-xs font-medium">{s.title}</p>
                      {s.description && <p className="text-text-muted text-xs mt-0.5">{s.description}</p>}
                      {s.source_url && <p className="text-text-faint text-xs">Source: {s.source_url}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>

      {/* New Account Modal */}
      {showNewAccount && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-md p-6">
            <h2 className="text-text-main font-semibold text-lg mb-4">New Account</h2>
            <form onSubmit={handleCreateAccount} className="space-y-3">
              <input required placeholder="Company name" value={newAccount.name} onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <div className="grid grid-cols-2 gap-3">
                <select value={newAccount.type} onChange={(e) => setNewAccount({ ...newAccount, type: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                  {['operator', 'hyperscaler', 'developer', 'colo', 'enterprise'].map((t) => <option key={t}>{t}</option>)}
                </select>
                <input placeholder="Stage (e.g. Target)" value={newAccount.stage} onChange={(e) => setNewAccount({ ...newAccount, stage: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <input placeholder="Location" value={newAccount.location} onChange={(e) => setNewAccount({ ...newAccount, location: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Website (https://...)" value={newAccount.website} onChange={(e) => setNewAccount({ ...newAccount, website: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Logo URL (https://...)" value={newAccount.logo_url} onChange={(e) => setNewAccount({ ...newAccount, logo_url: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Tags (comma-separated, e.g. ai, renewable)" value={newAccount.tags} onChange={(e) => setNewAccount({ ...newAccount, tags: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <textarea placeholder="Notes / intel summary" value={newAccount.notes} onChange={(e) => setNewAccount({ ...newAccount, notes: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewAccount(false)} className="px-4 py-2 text-text-main hover:text-text-main text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Create Account'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Contact Modal */}
      {showNewContact && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-md p-6">
            <h2 className="text-text-main font-semibold text-lg mb-4">Add Contact</h2>
            <form onSubmit={handleCreateContact} className="space-y-3">
              <input required placeholder="Name" value={newContact.name} onChange={(e) => setNewContact({ ...newContact, name: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Role" value={newContact.role} onChange={(e) => setNewContact({ ...newContact, role: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Email" type="email" value={newContact.email} onChange={(e) => setNewContact({ ...newContact, email: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Phone" value={newContact.phone} onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewContact(false)} className="px-4 py-2 text-text-main hover:text-text-main text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Add Contact'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Signal Modal */}
      {showNewSignal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle rounded-xl w-full max-w-md p-6">
            <h2 className="text-text-main font-semibold text-lg mb-4">Add Trigger Signal</h2>
            <form onSubmit={handleCreateSignal} className="space-y-3">
              <select value={newSignal.signal_type} onChange={(e) => setNewSignal({ ...newSignal, signal_type: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {['planning', 'grid', 'land_acquisition', 'hiring_spike', 'framework_award', 'roadworks'].map((t) => <option key={t}>{t}</option>)}
              </select>
              <input required placeholder="Signal title (e.g. £1bn funding round)" value={newSignal.title} onChange={(e) => setNewSignal({ ...newSignal, title: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <textarea placeholder="Description (optional)" value={newSignal.description} onChange={(e) => setNewSignal({ ...newSignal, description: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
              <input placeholder="Source URL (e.g. https://linkedin.com/...)" value={newSignal.source_url} onChange={(e) => setNewSignal({ ...newSignal, source_url: e.target.value })} className="w-full bg-background border border-border-subtle text-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewSignal(false)} className="px-4 py-2 text-text-main hover:text-text-main text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-primary hover:bg-primary-dark text-text-main px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Add Signal'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
