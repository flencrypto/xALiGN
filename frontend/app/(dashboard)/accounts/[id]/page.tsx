'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import {
  accountsApi,
  opportunitiesApi,
  bidsApi,
  type Account,
  type Contact,
  type TriggerSignal,
  type Opportunity,
  type Bid,
} from '@/lib/api';
import {
  Building2,
  Globe,
  MapPin,
  Tag,
  DollarSign,
  Calendar,
  ArrowLeft,
  Users,
  Zap,
  Target,
  FileStack,
  Phone,
  ExternalLink,
  Plus,
  ChevronRight,
  AlertCircle,
  Mail,
  User,
  Clock,
  TrendingUp,
  Shield,
} from 'lucide-react';

type Tab = 'overview' | 'contacts' | 'signals' | 'opportunities' | 'bids';

const DEFAULT_SIGNAL_FORM = { signal_type: 'planning', title: '', description: '', source_url: '' };

export default function AccountDetailPage() {
  const params = useParams();
  const accountId = Number(params.id);
  const router = useRouter();

  const [tab, setTab] = useState<Tab>('overview');
  const [account, setAccount] = useState<Account | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [signals, setSignals] = useState<TriggerSignal[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [bids, setBids] = useState<Bid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Modals
  const [showContactModal, setShowContactModal] = useState(false);
  const [showSignalModal, setShowSignalModal] = useState(false);
  const [contactForm, setContactForm] = useState({ name: '', role: '', email: '', phone: '' });
  const [signalForm, setSignalForm] = useState(DEFAULT_SIGNAL_FORM);

  useEffect(() => {
    async function load() {
      if (isNaN(accountId)) {
        setError('Invalid account ID');
        setLoading(false);
        return;
      }
      try {
        const [acc, cons, sigs, accOpps] = await Promise.all([
          accountsApi.get(accountId),
          accountsApi.listContacts(accountId).catch(() => []),
          accountsApi.listTriggerSignals(accountId).catch(() => []),
          opportunitiesApi.list({ account_id: accountId }).catch(() => []),
        ]);
        setAccount(acc);
        setContacts(cons);
        setSignals(sigs);
        setOpportunities(accOpps);
        // Fetch bids filtered by each opportunity
        const oppIds = accOpps.map((o) => o.id);
        const bidArrays = await Promise.all(
          oppIds.map((oppId) => bidsApi.list({ opportunity_id: oppId }).catch(() => []))
        );
        setBids(bidArrays.flat());
      } catch {
        setError('Failed to load account');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [accountId]);

  async function handleAddContact() {
    if (!contactForm.name.trim()) return;
    try {
      const c = await accountsApi.createContact(accountId, contactForm);
      setContacts([...contacts, c]);
      setContactForm({ name: '', role: '', email: '', phone: '' });
      setShowContactModal(false);
    } catch {
      setError('Failed to add contact');
    }
  }

  async function handleAddSignal() {
    if (!signalForm.title.trim()) return;
    try {
      const s = await accountsApi.createTriggerSignal(accountId, signalForm);
      setSignals([...signals, s]);
      setSignalForm(DEFAULT_SIGNAL_FORM);
      setShowSignalModal(false);
    } catch {
      setError('Failed to add signal');
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Account Detail" />
        <div className="p-6 space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-2xl shimmer" />
          ))}
        </div>
      </>
    );
  }

  if (error || !account) {
    return (
      <>
        <Header title="Account Not Found" />
        <div className="p-6 flex flex-col items-center justify-center py-24">
          <AlertCircle size={48} className="text-color-danger mb-4" />
          <p className="text-color-text-main text-lg">{error || 'Account not found'}</p>
          <button onClick={() => router.push('/accounts')} className="mt-4 px-4 py-2 bg-color-primary/10 text-color-primary rounded-xl hover:bg-color-primary/20 transition-colors text-sm">
            Back to Accounts
          </button>
        </div>
      </>
    );
  }

  const tabs: { key: Tab; label: string; Icon: typeof Building2; count?: number }[] = [
    { key: 'overview', label: 'Overview', Icon: Building2 },
    { key: 'contacts', label: 'Contacts', Icon: Users, count: contacts.length },
    { key: 'signals', label: 'Signals', Icon: Zap, count: signals.length },
    { key: 'opportunities', label: 'Opportunities', Icon: Target, count: opportunities.length },
    { key: 'bids', label: 'Bids', Icon: FileStack, count: bids.length },
  ];

  const pipelineValue = opportunities.reduce((sum, o) => sum + (o.estimated_value || 0), 0);
  const activeSignals = signals.filter((s) => s.status !== 'dismissed').length;

  return (
    <>
      <Header
        title={account.name}
        action={
          <button onClick={() => router.push('/accounts')} className="flex items-center gap-1.5 text-xs text-color-text-muted hover:text-color-primary transition-colors">
            <ArrowLeft size={14} /> All Accounts
          </button>
        }
      />
      <div className="p-6 space-y-6 fade-in">
        {/* Account Header Card */}
        <div className="metric-card rounded-2xl p-6 relative overflow-hidden">
          <div className="absolute inset-0 holo-shimmer pointer-events-none opacity-30" />
          <div className="relative flex flex-col md:flex-row md:items-start gap-6">
            {/* Avatar */}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-color-primary/20 to-color-secondary/10 border border-color-primary/20 flex items-center justify-center shrink-0 shadow-neon">
              {account.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={account.logo_url} alt="" className="w-12 h-12 rounded-xl object-cover" />
              ) : (
                <Building2 size={28} className="text-color-primary" />
              )}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className="text-2xl font-bold text-color-text-main">{account.name}</h2>
                <span className="px-2.5 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-color-primary/10 text-color-primary rounded-full border border-color-primary/20">
                  {account.type || 'Unknown'}
                </span>
                {account.tier_target && (
                  <span className="px-2.5 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-color-secondary/10 text-color-secondary rounded-full border border-color-secondary/20">
                    <Shield size={10} className="inline mr-1" />{account.tier_target}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-4 mt-3 text-sm text-color-text-muted">
                {account.location && (
                  <span className="flex items-center gap-1.5"><MapPin size={14} className="text-color-text-faint" />{account.location}</span>
                )}
                {account.website && (
                  <a href={account.website.startsWith('http') ? account.website : `https://${account.website}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-color-primary transition-colors">
                    <Globe size={14} className="text-color-text-faint" />{account.website}<ExternalLink size={10} />
                  </a>
                )}
                {account.tags && (
                  <span className="flex items-center gap-1.5"><Tag size={14} className="text-color-text-faint" />{account.tags}</span>
                )}
              </div>
            </div>

            {/* Quick stats */}
            <div className="flex gap-3 shrink-0">
              {[
                { label: 'Contacts', value: contacts.length, color: 'text-color-primary' },
                { label: 'Opps', value: opportunities.length, color: 'text-color-success' },
                { label: 'Signals', value: activeSignals, color: 'text-color-warning' },
              ].map((s) => (
                <div key={s.label} className="text-center p-3 rounded-xl bg-color-surface/50 border border-color-border-subtle/30 min-w-[80px] hover:border-color-primary/20 transition-all">
                  <p className={`text-xl font-bold font-mono ${s.color}`}>{s.value}</p>
                  <p className="text-[10px] text-color-text-faint font-mono uppercase tracking-wider mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Pipeline value banner */}
        {pipelineValue > 0 && (
          <div className="metric-card rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-success/15 flex items-center justify-center">
                <TrendingUp size={18} className="text-color-success" />
              </div>
              <div>
                <p className="text-[10px] font-mono uppercase tracking-wider text-color-text-faint">Total Pipeline Value</p>
                <p className="text-lg font-bold font-mono text-color-success neon-text">£{pipelineValue.toLocaleString()}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-color-text-muted font-mono">
              <span>{opportunities.length} opportunit{opportunities.length !== 1 ? 'ies' : 'y'}</span>
              <span className="text-color-text-faint">·</span>
              <span>{bids.length} bid{bids.length !== 1 ? 's' : ''}</span>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 p-1 rounded-xl bg-color-surface/40 border border-color-border-subtle/30 overflow-x-auto backdrop-blur-sm">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                tab === t.key
                  ? 'bg-color-primary/10 text-color-primary shadow-neon border border-color-primary/20'
                  : 'text-color-text-muted hover:text-color-text-main hover:bg-color-surface/60 border border-transparent'
              }`}
            >
              <t.Icon size={15} strokeWidth={tab === t.key ? 2.2 : 1.8} />
              {t.label}
              {t.count !== undefined && (
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
                  tab === t.key ? 'bg-color-primary/20 text-color-primary' : 'bg-color-surface text-color-text-faint'
                }`}>
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="fade-in">
          {/* ── Overview ── */}
          {tab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Company Info */}
              <div className="metric-card rounded-2xl p-6">
                <div className="section-header mb-4">Company Information</div>
                <div className="space-y-3">
                  {account.annual_revenue && (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-color-surface/40 border border-success/10 hover:border-success/20 transition-colors">
                      <span className="flex items-center gap-2 text-sm text-color-text-muted"><DollarSign size={14} className="text-success" /> Annual Revenue</span>
                      <span className="text-sm font-mono text-color-success font-bold">£{account.annual_revenue.toLocaleString()}</span>
                    </div>
                  )}
                  {account.stage && (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-color-surface/40 hover:bg-color-surface/60 transition-colors">
                      <span className="flex items-center gap-2 text-sm text-color-text-muted"><TrendingUp size={14} className="text-primary" /> Stage</span>
                      <span className="text-sm font-medium text-color-text-main">{account.stage}</span>
                    </div>
                  )}
                  {account.created_at && (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-color-surface/40 hover:bg-color-surface/60 transition-colors">
                      <span className="flex items-center gap-2 text-sm text-color-text-muted"><Calendar size={14} className="text-text-faint" /> Created</span>
                      <span className="text-sm font-mono text-color-text-main">{new Date(account.created_at).toLocaleDateString()}</span>
                    </div>
                  )}
                  {pipelineValue > 0 && (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-color-success/5 border border-color-success/10 hover:border-success/25 transition-colors">
                      <span className="flex items-center gap-2 text-sm text-color-text-muted"><DollarSign size={14} className="text-success" /> Pipeline Value</span>
                      <span className="text-sm font-mono text-color-success font-bold neon-text">£{pipelineValue.toLocaleString()}</span>
                    </div>
                  )}
                </div>
                {account.notes && (
                  <div className="mt-4 p-3 rounded-xl bg-color-surface/40 border border-color-border-subtle/20">
                    <p className="text-xs text-color-text-faint font-mono mb-1">Notes</p>
                    <p className="text-sm text-color-text-main whitespace-pre-wrap">{account.notes}</p>
                  </div>
                )}
              </div>

              {/* Cross-links panel */}
              <div className="space-y-4">
                {/* Recent Signals */}
                <div className="metric-card rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="section-header"><Zap size={14} />Recent Signals</div>
                    <button onClick={() => setTab('signals')} className="text-[10px] text-color-primary hover:underline font-mono">View All →</button>
                  </div>
                  {signals.length === 0 ? (
                    <p className="text-xs text-color-text-faint">No trigger signals</p>
                  ) : (
                    <div className="space-y-2">
                      {signals.slice(0, 3).map((s) => (
                        <div key={s.id} className="flex items-center gap-3 p-2.5 rounded-xl row-hover">
                          <div className="w-7 h-7 rounded-lg bg-amber-500/15 flex items-center justify-center">
                            <Zap size={12} className="text-amber-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-color-text-main truncate">{s.title}</p>
                            <p className="text-[10px] text-color-text-faint font-mono">{s.signal_type}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Recent Opportunities */}
                <div className="metric-card rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="section-header"><Target size={14} />Opportunities</div>
                    <button onClick={() => setTab('opportunities')} className="text-[10px] text-color-primary hover:underline font-mono">View All →</button>
                  </div>
                  {opportunities.length === 0 ? (
                    <p className="text-xs text-color-text-faint">No opportunities linked</p>
                  ) : (
                    <div className="space-y-2">
                      {opportunities.slice(0, 3).map((o) => (
                        <Link key={o.id} href={`/opportunities`} className="flex items-center gap-3 p-2.5 rounded-xl row-hover">
                          <div className="w-7 h-7 rounded-lg bg-green-500/15 flex items-center justify-center">
                            <Target size={12} className="text-green-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-color-text-main truncate">{o.title}</p>
                            <p className="text-[10px] text-color-text-faint font-mono">{o.stage}{o.estimated_value ? ` · £${o.estimated_value.toLocaleString()}` : ''}</p>
                          </div>
                          <ChevronRight size={14} className="text-color-text-faint" />
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                {/* Recent Contacts */}
                <div className="metric-card rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="section-header"><Users size={14} />Key Contacts</div>
                    <button onClick={() => setTab('contacts')} className="text-[10px] text-color-primary hover:underline font-mono">View All →</button>
                  </div>
                  {contacts.length === 0 ? (
                    <p className="text-xs text-color-text-faint">No contacts added</p>
                  ) : (
                    <div className="space-y-2">
                      {contacts.slice(0, 3).map((c) => (
                        <div key={c.id} className="flex items-center gap-3 p-2.5 rounded-xl row-hover">
                          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 flex items-center justify-center">
                            <User size={12} className="text-cyan-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-color-text-main truncate">{c.name}</p>
                            <p className="text-[10px] text-color-text-faint font-mono">{c.role || 'No role'}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ── Contacts Tab ── */}
          {tab === 'contacts' && (
            <div className="metric-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-5">
                <div className="section-header"><Users size={14} />Contacts ({contacts.length})</div>
                <button onClick={() => setShowContactModal(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-color-primary/10 text-color-primary rounded-xl hover:bg-color-primary/20 border border-color-primary/20 transition-colors">
                  <Plus size={14} /> Add Contact
                </button>
              </div>
              {contacts.length === 0 ? (
                <div className="text-center py-12">
                  <Users size={32} className="text-color-text-faint mx-auto mb-3" />
                  <p className="text-sm text-color-text-muted">No contacts yet</p>
                  <p className="text-xs text-color-text-faint mt-1">Add key stakeholders and decision makers</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {contacts.map((c) => (
                    <div key={c.id} className="p-4 rounded-xl border border-color-border-subtle/30 bg-color-surface/30 hover:border-color-primary/20 transition-colors">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/10 flex items-center justify-center">
                          <User size={18} className="text-cyan-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-color-text-main">{c.name}</p>
                          {c.role && <p className="text-[10px] text-color-text-faint font-mono">{c.role}</p>}
                        </div>
                      </div>
                      <div className="space-y-1.5">
                        {c.email && (
                          <a href={`mailto:${c.email}`} className="flex items-center gap-2 text-xs text-color-text-muted hover:text-color-primary transition-colors">
                            <Mail size={12} /> {c.email}
                          </a>
                        )}
                        {c.phone && (
                          <a href={`tel:${c.phone}`} className="flex items-center gap-2 text-xs text-color-text-muted hover:text-color-primary transition-colors">
                            <Phone size={12} /> {c.phone}
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Signals Tab ── */}
          {tab === 'signals' && (
            <div className="metric-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-5">
                <div className="section-header"><Zap size={14} />Trigger Signals ({signals.length})</div>
                <button onClick={() => setShowSignalModal(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-color-warning/10 text-color-warning rounded-xl hover:bg-color-warning/20 border border-color-warning/20 transition-colors">
                  <Plus size={14} /> Add Signal
                </button>
              </div>
              {signals.length === 0 ? (
                <div className="text-center py-12">
                  <Zap size={32} className="text-color-text-faint mx-auto mb-3" />
                  <p className="text-sm text-color-text-muted">No trigger signals</p>
                  <p className="text-xs text-color-text-faint mt-1">Track news, events, and triggers</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {signals.map((s) => (
                    <div key={s.id} className="flex items-center gap-4 p-4 rounded-xl border border-color-border-subtle/30 bg-color-surface/30 row-hover">
                      <div className="w-10 h-10 rounded-xl bg-amber-500/15 flex items-center justify-center shrink-0">
                        <Zap size={18} className="text-amber-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-color-text-main truncate">{s.title}</p>
                          <span className="px-1.5 py-0.5 text-[9px] font-mono uppercase bg-color-surface rounded-full text-color-text-faint">{s.signal_type}</span>
                        </div>
                        {s.description && <p className="text-xs text-color-text-muted mt-1 line-clamp-2">{s.description}</p>}
                      </div>
                      {s.source_url && (
                        <a href={s.source_url} target="_blank" rel="noopener noreferrer" title="View source" className="text-color-primary hover:text-color-primary/80 transition-colors shrink-0">
                          <ExternalLink size={14} />
                        </a>
                      )}
                      {s.detected_at && (
                        <span className="text-[10px] text-color-text-faint font-mono shrink-0">{new Date(s.detected_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Opportunities Tab ── */}
          {tab === 'opportunities' && (
            <div className="metric-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-5">
                <div className="section-header"><Target size={14} />Opportunities ({opportunities.length})</div>
                <Link href="/opportunities" className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-color-success/10 text-color-success rounded-xl hover:bg-color-success/20 border border-color-success/20 transition-colors">
                  Open Pipeline <ChevronRight size={14} />
                </Link>
              </div>
              {opportunities.length === 0 ? (
                <div className="text-center py-12">
                  <Target size={32} className="text-color-text-faint mx-auto mb-3" />
                  <p className="text-sm text-color-text-muted">No opportunities</p>
                  <p className="text-xs text-color-text-faint mt-1">Create opportunities from the Pipeline page</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {opportunities.map((o) => {
                    const stageColors: Record<string, string> = {
                      Identified: 'bg-blue-500/15 text-blue-400',
                      Qualified: 'bg-cyan-500/15 text-cyan-400',
                      Proposal: 'bg-amber-500/15 text-amber-400',
                      Negotiation: 'bg-purple-500/15 text-purple-400',
                      Won: 'bg-green-500/15 text-green-400',
                      Lost: 'bg-red-500/15 text-red-400',
                    };
                    const stageClass = stageColors[o.stage] || 'bg-color-surface text-color-text-muted';
                    return (
                      <div key={o.id} className="flex items-center gap-4 p-4 rounded-xl border border-color-border-subtle/30 bg-color-surface/30 row-hover">
                        <div className="w-10 h-10 rounded-xl bg-green-500/15 flex items-center justify-center shrink-0">
                          <Target size={18} className="text-green-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-color-text-main truncate">{o.title}</p>
                          {o.description && <p className="text-xs text-color-text-muted mt-0.5 line-clamp-1">{o.description}</p>}
                        </div>
                        <span className={`px-2 py-0.5 text-[10px] font-mono uppercase rounded-full shrink-0 ${stageClass}`}>{o.stage}</span>
                        {o.estimated_value && (
                          <span className="text-sm font-mono text-color-success shrink-0">£{o.estimated_value.toLocaleString()}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ── Bids Tab ── */}
          {tab === 'bids' && (
            <div className="metric-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-5">
                <div className="section-header"><FileStack size={14} />Bids ({bids.length})</div>
                <Link href="/bids" className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-color-warning/10 text-color-warning rounded-xl hover:bg-color-warning/20 border border-color-warning/20 transition-colors">
                  Open Bid Packs <ChevronRight size={14} />
                </Link>
              </div>
              {bids.length === 0 ? (
                <div className="text-center py-12">
                  <FileStack size={32} className="text-color-text-faint mx-auto mb-3" />
                  <p className="text-sm text-color-text-muted">No bids</p>
                  <p className="text-xs text-color-text-faint mt-1">Bids will appear here when linked to opportunities</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {bids.map((b) => {
                    const statusColors: Record<string, string> = {
                      Draft: 'bg-color-surface text-color-text-muted',
                      'In Progress': 'bg-blue-500/15 text-blue-400',
                      'Under Review': 'bg-amber-500/15 text-amber-400',
                      Submitted: 'bg-purple-500/15 text-purple-400',
                      Won: 'bg-green-500/15 text-green-400',
                      Lost: 'bg-red-500/15 text-red-400',
                    };
                    const statusClass = statusColors[b.status] || 'bg-color-surface text-color-text-muted';
                    return (
                      <div key={b.id} className="flex items-center gap-4 p-4 rounded-xl border border-color-border-subtle/30 bg-color-surface/30 row-hover">
                        <div className="w-10 h-10 rounded-xl bg-amber-500/15 flex items-center justify-center shrink-0">
                          <FileStack size={18} className="text-amber-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-color-text-main truncate">{b.title}</p>
                          {b.tender_ref && <p className="text-[10px] text-color-text-faint font-mono mt-0.5">Ref: {b.tender_ref}</p>}
                        </div>
                        <span className={`px-2 py-0.5 text-[10px] font-mono uppercase rounded-full shrink-0 ${statusClass}`}>{b.status}</span>
                        {b.submission_date && (
                          <span className="flex items-center gap-1 text-[10px] text-color-text-faint font-mono shrink-0">
                            <Clock size={10} /> {new Date(b.submission_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Add Contact Modal ── */}
      {showContactModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowContactModal(false)}>
          <div className="glass-card rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-color-text-main mb-4">Add Contact</h3>
            <div className="space-y-3">
              <input type="text" placeholder="Name *" value={contactForm.name} onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors" />
              <input type="text" placeholder="Role" value={contactForm.role} onChange={(e) => setContactForm({ ...contactForm, role: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors" />
              <input type="email" placeholder="Email" value={contactForm.email} onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors" />
              <input type="tel" placeholder="Phone" value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors" />
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShowContactModal(false)} className="px-4 py-2 text-sm text-color-text-muted hover:text-color-text-main transition-colors">Cancel</button>
              <button onClick={handleAddContact} className="px-4 py-2 text-sm font-medium bg-color-primary text-color-background rounded-xl hover:bg-color-primary/90 transition-colors">Add Contact</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Add Signal Modal ── */}
      {showSignalModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowSignalModal(false)}>
          <div className="glass-card rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-color-text-main mb-4">Add Trigger Signal</h3>
            <div className="space-y-3">
              <select aria-label="Signal type" value={signalForm.signal_type} onChange={(e) => setSignalForm({ ...signalForm, signal_type: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors">
                <option value="planning">Planning</option>
                <option value="grid">Grid</option>
                <option value="hiring_spike">Hiring Spike</option>
                <option value="framework_award">Framework Award</option>
                <option value="new_build">New Build</option>
                <option value="expansion">Expansion</option>
              </select>
              <input type="text" placeholder="Signal Title *" value={signalForm.title} onChange={(e) => setSignalForm({ ...signalForm, title: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors" />
              <textarea placeholder="Description" value={signalForm.description} onChange={(e) => setSignalForm({ ...signalForm, description: e.target.value })} rows={3}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors resize-none" />
              <input type="url" placeholder="Source URL" value={signalForm.source_url} onChange={(e) => setSignalForm({ ...signalForm, source_url: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-color-surface/80 border border-color-border-subtle text-color-text-main text-sm focus:border-color-primary focus:outline-none transition-colors" />
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShowSignalModal(false)} className="px-4 py-2 text-sm text-color-text-muted hover:text-color-text-main transition-colors">Cancel</button>
              <button onClick={handleAddSignal} className="px-4 py-2 text-sm font-medium bg-color-warning text-color-background rounded-xl hover:bg-color-warning/90 transition-colors">Add Signal</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
