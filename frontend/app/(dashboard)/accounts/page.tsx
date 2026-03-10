'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import WebsiteSwoop from '@/components/WebsiteSwoop';
import { accountsApi, accountsCsvApi, callsApi, Account, Contact, TriggerSignal, CallIntelligence, CsvImportResult } from '@/lib/api';
import {
  Building2, MapPin, Globe, Plus, Download, Upload, X, Users,
  Signal, ChevronRight, Search, ExternalLink, Phone, Mail, FileDown,
  TrendingUp, Zap, BarChart3,
} from 'lucide-react';

const ACCOUNT_TYPES = ['All', 'operator', 'hyperscaler', 'developer', 'colo', 'enterprise'];

const TYPE_COLORS: Record<string, string> = {
  operator: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  hyperscaler: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
  developer: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  colo: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  enterprise: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
};

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

function typeColor(type: string) {
  return TYPE_COLORS[type?.toLowerCase()] ?? 'bg-surface text-text-muted border-border-subtle';
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
  const [search, setSearch] = useState('');
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
    const [c, s, callData] = await Promise.all([
      accountsApi.listContacts(acc.id).catch(() => []),
      accountsApi.listTriggerSignals(acc.id).catch(() => []),
      callsApi.list({ account_id: acc.id }).catch(() => []),
    ]);
    setContacts(c);
    setSignals(s);
    setCalls(callData);
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

  const filtered = accounts
    .filter((a) => filter === 'All' || a.type === filter)
    .filter((a) => !search || a.name.toLowerCase().includes(search.toLowerCase()) || a.location?.toLowerCase().includes(search.toLowerCase()));

  return (
    <>
      <Header
        title="Account Intelligence"
        action={
          <div className="flex gap-2 flex-wrap items-center">
            <a
              href={accountsCsvApi.templateUrl()}
              download="accounts_import_template.csv"
              className="glass-card !p-0 px-3 py-2 text-xs font-medium flex items-center gap-1.5 hover:border-primary/40 transition-colors"
            >
              <FileDown className="w-3.5 h-3.5 text-text-muted" /> Template
            </a>
            <label className={`glass-card !p-0 px-3 py-2 text-xs font-medium flex items-center gap-1.5 cursor-pointer hover:border-primary/40 transition-colors ${csvImporting ? 'opacity-60 cursor-not-allowed' : ''}`}>
              <Upload className="w-3.5 h-3.5 text-text-muted" />
              {csvImporting ? 'Importing…' : 'Import CSV'}
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
              className="glass-card !p-0 px-3 py-2 text-xs font-medium flex items-center gap-1.5 hover:border-primary/40 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-text-muted" /> Export
            </a>
            <button
              onClick={() => setShowNewAccount(true)}
              className="bg-gradient-to-r from-primary to-secondary text-white px-4 py-2 rounded-lg text-sm font-medium transition-all hover:shadow-glow flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" /> New Account
            </button>
          </div>
        }
      />

      {/* CSV import result banner */}
      {csvResult && (
        <div className={`mx-6 mt-4 p-4 rounded-xl border text-sm fade-in ${csvResult.errors.length === 0 ? 'bg-success/10 border-success/30 text-success' : 'bg-warning/10 border-warning/30 text-warning'}`}>
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium">{csvResult.message}</span>
            <button aria-label="Dismiss" onClick={() => setCsvResult(null)} className="text-text-muted hover:text-text-main ml-4"><X className="w-4 h-4" /></button>
          </div>
          {csvResult.errors.length > 0 && (
            <ul className="list-disc list-inside space-y-0.5 mt-2 text-xs text-warning">
              {csvResult.errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
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

      {/* Summary Stats */}
      {!loading && accounts.length > 0 && (
        <div className="px-6 pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 fade-in">
          {[
            { label: 'Total Accounts', value: accounts.length, icon: Building2, color: 'text-primary' },
            { label: 'Operators', value: accounts.filter(a => a.type === 'operator').length, icon: Zap, color: 'text-cyan-400' },
            { label: 'Hyperscalers', value: accounts.filter(a => a.type === 'hyperscaler').length, icon: TrendingUp, color: 'text-indigo-400' },
            { label: 'Pipeline Value', value: accounts.reduce((s, a) => s + (a.annual_revenue || 0), 0), icon: BarChart3, color: 'text-success', isCurrency: true },
          ].map((stat) => (
            <div key={stat.label} className="metric-card rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-faint">{stat.label}</span>
              </div>
              <p className={`text-xl font-bold font-mono ${stat.color}`}>
                {stat.isCurrency ? `£${stat.value.toLocaleString()}` : stat.value}
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Main table */}
        <div className="flex-1 p-6 overflow-auto">
          {/* Search + Filter bar */}
          <div className="flex items-center gap-4 mb-5 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-sm group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-faint group-focus-within:text-primary transition-colors" />
              <input
                type="text"
                placeholder="Search accounts…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-color-surface/50 border border-color-border-subtle text-color-text-main rounded-lg pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:border-primary/60 focus:shadow-neon backdrop-blur-sm transition-all"
              />
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {ACCOUNT_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => setFilter(t)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    filter === t
                      ? 'bg-primary/20 border-primary/40 text-primary shadow-glow'
                      : 'bg-color-surface/30 border-color-border-subtle text-color-text-muted hover:border-primary/30 hover:text-color-text-main'
                  }`}
                >
                  {t === 'All' ? 'All' : t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
            <span className="text-text-faint text-xs font-mono ml-auto tabular-nums">{filtered.length} account{filtered.length !== 1 ? 's' : ''}</span>
          </div>

          {loading ? (
            <div className="space-y-3">{[...Array(6)].map((_, i) => <div key={i} className="shimmer h-16 rounded-xl" />)}</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20 fade-in">
              <div className="radar-ping mx-auto mb-4 w-12 h-12" />
              <Building2 className="w-12 h-12 text-text-faint mx-auto mb-3" />
              <p className="text-text-muted">No accounts found. Add your first account or import from CSV.</p>
            </div>
          ) : (
            <div className="glass-card !p-0 overflow-hidden fade-in border-color-border-subtle/40">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-color-border-subtle/60 bg-color-surface/30">
                    <th className="text-left px-5 py-3.5 text-text-faint font-medium text-xs uppercase tracking-wider font-mono">Company</th>
                    <th className="text-left px-4 py-3.5 text-text-faint font-medium text-xs uppercase tracking-wider font-mono">Type</th>
                    <th className="text-left px-4 py-3.5 text-text-faint font-medium text-xs uppercase tracking-wider font-mono hidden md:table-cell">Location</th>
                    <th className="text-left px-4 py-3.5 text-text-faint font-medium text-xs uppercase tracking-wider font-mono hidden lg:table-cell">Website</th>
                    <th className="text-left px-4 py-3.5 text-text-faint font-medium text-xs uppercase tracking-wider font-mono hidden lg:table-cell">Stage</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((acc, i) => (
                    <tr
                      key={acc.id}
                      onClick={() => selectAccount(acc)}
                      className={`border-b border-color-border-subtle/30 cursor-pointer transition-all row-hover fade-in-up ${
                        selected?.id === acc.id ? 'bg-primary/5 border-l-2 border-l-primary shadow-neon' : ''
                      }`}
                      style={{ animationDelay: `${Math.min(i * 30, 300)}ms` }}
                    >
                      <td className="px-5 py-3.5">
                        <Link href={`/accounts/${acc.id}`} onClick={(e) => e.stopPropagation()} className="flex items-center gap-3 group">
                          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 border border-color-border-subtle flex items-center justify-center flex-shrink-0 overflow-hidden group-hover:border-primary/40 group-hover:shadow-glow transition-all">
                            {acc.logo_url ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img src={acc.logo_url} alt={`${acc.name} logo`} className="w-full h-full object-contain" />
                            ) : (
                              <Building2 className="w-4 h-4 text-primary" />
                            )}
                          </div>
                          <div>
                            <p className="text-color-text-main font-medium group-hover:text-primary transition-colors">{acc.name}</p>
                            {acc.tags && (
                              <div className="flex gap-1 mt-0.5">
                                {acc.tags.split(',').slice(0, 2).map((t) => t.trim()).filter(Boolean).map((tag) => (
                                  <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-primary/5 border border-primary/10 rounded text-text-faint">{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </Link>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`px-2 py-1 rounded-md text-xs font-medium border ${typeColor(acc.type)}`}>{acc.type}</span>
                      </td>
                      <td className="px-4 py-3.5 text-text-muted hidden md:table-cell">
                        {acc.location ? (
                          <span className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-text-faint" />{acc.location}</span>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-3.5 hidden lg:table-cell">
                        {acc.website ? (
                          <a href={acc.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline text-xs flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                            <Globe className="w-3 h-3" />{acc.website.replace(/^https?:\/\/(www\.)?/, '')}
                          </a>
                        ) : <span className="text-text-faint">—</span>}
                      </td>
                      <td className="px-4 py-3.5 hidden lg:table-cell">
                        {acc.stage ? (
                          <span className="text-xs text-text-muted">{acc.stage}</span>
                        ) : <span className="text-text-faint">—</span>}
                      </td>
                      <td className="px-2 py-3.5">
                        <Link href={`/accounts/${acc.id}`} onClick={(e) => e.stopPropagation()} className="text-text-faint hover:text-primary transition-colors">
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Side panel */}
        {selected && (
          <div className="w-80 xl:w-96 border-l border-color-border-subtle/40 bg-color-surface/80 backdrop-blur-lg overflow-auto p-5 flex-shrink-0 fade-in">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 border border-primary/20 flex items-center justify-center flex-shrink-0 overflow-hidden shadow-neon">
                  {selected.logo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={selected.logo_url} alt="" className="w-full h-full object-contain" />
                  ) : (
                    <Building2 className="w-5 h-5 text-primary" />
                  )}
                </div>
                <h2 className="text-color-text-main font-semibold text-lg truncate">{selected.name}</h2>
              </div>
              <button aria-label="Close panel" onClick={() => setSelected(null)} className="text-text-faint hover:text-color-text-main transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* View Full Profile link */}
            <Link
              href={`/accounts/${selected.id}`}
              className="action-card flex items-center justify-center gap-2 w-full py-2.5 mb-5 rounded-lg bg-gradient-to-r from-primary/10 to-secondary/10 border border-primary/20 text-primary text-sm font-medium hover:border-primary/40 hover:shadow-glow transition-all"
            >
              <ExternalLink className="w-4 h-4" /> View Full Profile
            </Link>

            <div className="space-y-2 text-sm mb-5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2 py-0.5 rounded-md text-xs font-medium border ${typeColor(selected.type)}`}>{selected.type}</span>
                {selected.stage && <span className="px-2 py-0.5 bg-success/15 text-success rounded-md text-xs border border-success/30">{selected.stage}</span>}
                {selected.tier_target && <span className="px-2 py-0.5 bg-color-surface text-color-text-main rounded-md text-xs">{selected.tier_target}</span>}
              </div>
              {selected.location && (
                <p className="text-text-muted flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-text-faint" /> {selected.location}</p>
              )}
              {selected.website && (
                <p className="flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-text-faint" />
                  <a href={selected.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline text-sm">
                    {selected.website.replace(/^https?:\/\/(www\.)?/, '')}
                  </a>
                </p>
              )}
              {selected.annual_revenue != null && (
                <p className="text-text-muted text-xs">Revenue: <span className="text-color-text-main font-medium">${selected.annual_revenue.toLocaleString()}</span></p>
              )}
              {selected.tags && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {selected.tags.split(',').map((t) => t.trim()).filter(Boolean).map((tag) => (
                    <span key={tag} className="px-2 py-0.5 bg-color-background rounded-md text-xs text-text-muted">{tag}</span>
                  ))}
                </div>
              )}
              {selected.notes && (
                <div className="bg-color-background/40 rounded-lg p-3 mt-2 border border-color-border-subtle/50">
                  <p className="text-color-text-main text-xs whitespace-pre-wrap">{selected.notes}</p>
                </div>
              )}
            </div>

            {/* Contacts */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-color-text-main text-xs font-semibold uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-primary" /> Contacts ({contacts.length})
                </h3>
                <button onClick={() => setShowNewContact(true)} className="text-primary hover:text-primary/80 text-xs flex items-center gap-1"><Plus className="w-3.5 h-3.5" /> Add</button>
              </div>
              {contacts.length === 0 ? (
                <p className="text-text-faint text-xs">No contacts yet.</p>
              ) : (
                <ul className="space-y-2">
                  {contacts.map((c) => (
                    <li key={c.id} className="bg-color-background/40 rounded-lg px-3 py-2 border border-color-border-subtle/30">
                      <p className="text-color-text-main text-sm font-medium">{c.name}</p>
                      <p className="text-text-muted text-xs">{c.role}</p>
                      <div className="flex items-center gap-3 mt-1">
                        {c.email && <a href={`mailto:${c.email}`} className="text-primary text-xs flex items-center gap-1 hover:underline"><Mail className="w-3 h-3" />{c.email}</a>}
                        {c.phone && <a href={`tel:${c.phone}`} className="text-text-muted text-xs flex items-center gap-1 hover:text-color-text-main"><Phone className="w-3 h-3" />{c.phone}</a>}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Trigger Signals */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-color-text-main text-xs font-semibold uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <Signal className="w-3.5 h-3.5 text-warning" /> Signals ({signals.length})
                </h3>
                <button onClick={() => setShowNewSignal(true)} className="text-primary hover:text-primary/80 text-xs flex items-center gap-1"><Plus className="w-3.5 h-3.5" /> Add</button>
              </div>
              {signals.length === 0 ? (
                <p className="text-text-faint text-xs">No signals yet.</p>
              ) : (
                <ul className="space-y-2">
                  {signals.map((s) => (
                    <li key={s.id} className="bg-color-background/40 rounded-lg px-3 py-2 border border-color-border-subtle/30">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${signalColor(s.signal_type)}`}>{s.signal_type}</span>
                      </div>
                      <p className="text-color-text-main text-xs font-medium">{s.title}</p>
                      {s.description && <p className="text-text-muted text-xs mt-0.5">{s.description}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Calls */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-color-text-main text-xs font-semibold uppercase tracking-wider font-mono">Calls ({calls.length})</h3>
                <Link href="/calls" className="text-primary hover:text-primary/80 text-xs">View All →</Link>
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
                      <li key={call.id} className="bg-color-background/40 rounded-lg px-3 py-2 border border-color-border-subtle/30">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            {call.executive_name && <p className="text-color-text-main text-sm font-medium truncate">{call.executive_name}</p>}
                            <p className="text-text-muted text-xs">
                              {call.call_date ? new Date(call.call_date).toLocaleDateString()
                                : call.created_at ? new Date(call.created_at).toLocaleDateString()
                                : 'No date'}
                            </p>
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
      </div>

      {/* New Account Modal */}
      {showNewAccount && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 fade-in">
          <div className="glass-card w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-color-text-main font-semibold text-lg flex items-center gap-2"><Building2 className="w-5 h-5 text-primary" /> New Account</h2>
              <button aria-label="Close" onClick={() => setShowNewAccount(false)} className="text-text-faint hover:text-color-text-main"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleCreateAccount} className="space-y-3">
              <input required placeholder="Company name" value={newAccount.name} onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <div className="grid grid-cols-2 gap-3">
                <select aria-label="Account type" value={newAccount.type} onChange={(e) => setNewAccount({ ...newAccount, type: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors">
                  {['operator', 'hyperscaler', 'developer', 'colo', 'enterprise'].map((t) => <option key={t}>{t}</option>)}
                </select>
                <input placeholder="Stage (e.g. Target)" value={newAccount.stage} onChange={(e) => setNewAccount({ ...newAccount, stage: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              </div>
              <input placeholder="Location" value={newAccount.location} onChange={(e) => setNewAccount({ ...newAccount, location: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <input placeholder="Website (https://...)" value={newAccount.website} onChange={(e) => setNewAccount({ ...newAccount, website: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <input placeholder="Logo URL (https://...)" value={newAccount.logo_url} onChange={(e) => setNewAccount({ ...newAccount, logo_url: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <input placeholder="Tags (comma-separated, e.g. ai, renewable)" value={newAccount.tags} onChange={(e) => setNewAccount({ ...newAccount, tags: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <textarea placeholder="Notes / intel summary" value={newAccount.notes} onChange={(e) => setNewAccount({ ...newAccount, notes: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors h-20 resize-none" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewAccount(false)} className="px-4 py-2 text-text-muted hover:text-color-text-main text-sm transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="bg-gradient-to-r from-primary to-secondary text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50 hover:shadow-glow transition-all">{saving ? 'Saving…' : 'Create Account'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Contact Modal */}
      {showNewContact && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 fade-in">
          <div className="glass-card w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-color-text-main font-semibold text-lg flex items-center gap-2"><Users className="w-5 h-5 text-primary" /> Add Contact</h2>
              <button aria-label="Close" onClick={() => setShowNewContact(false)} className="text-text-faint hover:text-color-text-main"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleCreateContact} className="space-y-3">
              <input required placeholder="Name" value={newContact.name} onChange={(e) => setNewContact({ ...newContact, name: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <input placeholder="Role" value={newContact.role} onChange={(e) => setNewContact({ ...newContact, role: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <input placeholder="Email" type="email" value={newContact.email} onChange={(e) => setNewContact({ ...newContact, email: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <input placeholder="Phone" value={newContact.phone} onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewContact(false)} className="px-4 py-2 text-text-muted hover:text-color-text-main text-sm transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="bg-gradient-to-r from-primary to-secondary text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50 hover:shadow-glow transition-all">{saving ? 'Saving…' : 'Add Contact'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Signal Modal */}
      {showNewSignal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 fade-in">
          <div className="glass-card w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-color-text-main font-semibold text-lg flex items-center gap-2"><Signal className="w-5 h-5 text-warning" /> Add Trigger Signal</h2>
              <button aria-label="Close" onClick={() => setShowNewSignal(false)} className="text-text-faint hover:text-color-text-main"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleCreateSignal} className="space-y-3">
              <select aria-label="Signal type" value={newSignal.signal_type} onChange={(e) => setNewSignal({ ...newSignal, signal_type: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors">
                {['planning', 'grid', 'land_acquisition', 'hiring_spike', 'framework_award', 'roadworks'].map((t) => <option key={t}>{t}</option>)}
              </select>
              <input required placeholder="Signal title (e.g. £1bn funding round)" value={newSignal.title} onChange={(e) => setNewSignal({ ...newSignal, title: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <textarea placeholder="Description (optional)" value={newSignal.description} onChange={(e) => setNewSignal({ ...newSignal, description: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors h-20 resize-none" />
              <input placeholder="Source URL (e.g. https://linkedin.com/...)" value={newSignal.source_url} onChange={(e) => setNewSignal({ ...newSignal, source_url: e.target.value })} className="w-full bg-color-background border border-color-border-subtle text-color-text-main rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/60 transition-colors" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewSignal(false)} className="px-4 py-2 text-text-muted hover:text-color-text-main text-sm transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="bg-gradient-to-r from-primary to-secondary text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50 hover:shadow-glow transition-all">{saving ? 'Saving…' : 'Add Signal'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
