'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { accountsApi, Account, Contact, TriggerSignal } from '@/lib/api';

const ACCOUNT_TYPES = ['All', 'Client', 'Prospect', 'Partner', 'Contractor'];

const SIGNAL_COLORS: Record<string, string> = {
  expansion: 'bg-green-500/20 text-green-400 border-green-500/30',
  renewal: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  pain: 'bg-red-500/20 text-red-400 border-red-500/30',
  tender: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  default: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

function signalColor(type: string) {
  return SIGNAL_COLORS[type?.toLowerCase()] ?? SIGNAL_COLORS.default;
}

interface NewAccountForm {
  name: string;
  type: string;
  location: string;
  website: string;
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
  description: string;
  source: string;
}

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [selected, setSelected] = useState<Account | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [signals, setSignals] = useState<TriggerSignal[]>([]);
  const [showNewAccount, setShowNewAccount] = useState(false);
  const [showNewContact, setShowNewContact] = useState(false);
  const [showNewSignal, setShowNewSignal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newAccount, setNewAccount] = useState<NewAccountForm>({ name: '', type: 'Client', location: '', website: '', notes: '' });
  const [newContact, setNewContact] = useState<NewContactForm>({ name: '', role: '', email: '', phone: '' });
  const [newSignal, setNewSignal] = useState<NewSignalForm>({ signal_type: 'expansion', description: '', source: '' });

  useEffect(() => {
    accountsApi.list().then(setAccounts).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function selectAccount(acc: Account) {
    setSelected(acc);
    const [c, s] = await Promise.all([
      accountsApi.listContacts(acc.id).catch(() => []),
      accountsApi.listTriggerSignals(acc.id).catch(() => []),
    ]);
    setContacts(c);
    setSignals(s);
  }

  async function handleCreateAccount(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const acc = await accountsApi.create(newAccount);
      setAccounts((prev) => [...prev, acc]);
      setShowNewAccount(false);
      setNewAccount({ name: '', type: 'Client', location: '', website: '', notes: '' });
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
      setNewSignal({ signal_type: 'expansion', description: '', source: '' });
    } finally {
      setSaving(false);
    }
  }

  const filtered = filter === 'All' ? accounts : accounts.filter((a) => a.type === filter);

  return (
    <>
      <Header
        title="Account Intelligence"
        action={
          <button
            onClick={() => setShowNewAccount(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            + New Account
          </button>
        }
      />
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
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-slate-800 border-slate-600 text-slate-300 hover:border-slate-400'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-slate-800 rounded animate-pulse" />)}</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-4xl mb-3">🏢</p>
              <p className="text-slate-400">No accounts yet. Add your first account to get started.</p>
            </div>
          ) : (
            <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left px-4 py-3 text-slate-400 font-medium">Name</th>
                    <th className="text-left px-4 py-3 text-slate-400 font-medium">Type</th>
                    <th className="text-left px-4 py-3 text-slate-400 font-medium hidden md:table-cell">Location</th>
                    <th className="text-left px-4 py-3 text-slate-400 font-medium hidden lg:table-cell">Stage</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((acc) => (
                    <tr
                      key={acc.id}
                      onClick={() => selectAccount(acc)}
                      className={`border-b border-slate-700/50 cursor-pointer transition-colors hover:bg-slate-700/50 ${
                        selected?.id === acc.id ? 'bg-slate-700/70' : ''
                      }`}
                    >
                      <td className="px-4 py-3 text-white font-medium">{acc.name}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs border border-blue-500/30">{acc.type}</span>
                      </td>
                      <td className="px-4 py-3 text-slate-300 hidden md:table-cell">{acc.location ?? '—'}</td>
                      <td className="px-4 py-3 text-slate-300 hidden lg:table-cell">{acc.stage ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Side panel */}
        {selected && (
          <div className="w-80 xl:w-96 border-l border-slate-700 bg-slate-800 overflow-auto p-5 flex-shrink-0">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-semibold text-lg truncate">{selected.name}</h2>
              <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-white ml-2">✕</button>
            </div>
            <div className="space-y-2 text-sm mb-5">
              <p className="text-slate-400">Type: <span className="text-slate-200">{selected.type}</span></p>
              <p className="text-slate-400">Location: <span className="text-slate-200">{selected.location ?? '—'}</span></p>
              <p className="text-slate-400">Website: <span className="text-slate-200">{selected.website ?? '—'}</span></p>
              {selected.notes && <p className="text-slate-400 text-xs">{selected.notes}</p>}
            </div>

            {/* Contacts */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white text-sm font-semibold">Contacts ({contacts.length})</h3>
                <button onClick={() => setShowNewContact(true)} className="text-blue-400 hover:text-blue-300 text-xs">+ Add</button>
              </div>
              {contacts.length === 0 ? (
                <p className="text-slate-500 text-xs">No contacts yet.</p>
              ) : (
                <ul className="space-y-2">
                  {contacts.map((c) => (
                    <li key={c.id} className="bg-slate-700/50 rounded-lg px-3 py-2">
                      <p className="text-white text-sm font-medium">{c.name}</p>
                      <p className="text-slate-400 text-xs">{c.role} {c.email && `· ${c.email}`}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Trigger Signals */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white text-sm font-semibold">Trigger Signals ({signals.length})</h3>
                <button onClick={() => setShowNewSignal(true)} className="text-blue-400 hover:text-blue-300 text-xs">+ Add</button>
              </div>
              {signals.length === 0 ? (
                <p className="text-slate-500 text-xs">No signals yet.</p>
              ) : (
                <ul className="space-y-2">
                  {signals.map((s) => (
                    <li key={s.id} className="bg-slate-700/50 rounded-lg px-3 py-2">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${signalColor(s.signal_type)}`}>{s.signal_type}</span>
                      </div>
                      <p className="text-slate-300 text-xs">{s.description}</p>
                      {s.source && <p className="text-slate-500 text-xs">Source: {s.source}</p>}
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
          <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-md p-6">
            <h2 className="text-white font-semibold text-lg mb-4">New Account</h2>
            <form onSubmit={handleCreateAccount} className="space-y-3">
              <input required placeholder="Company name" value={newAccount.name} onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <select value={newAccount.type} onChange={(e) => setNewAccount({ ...newAccount, type: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {['Client', 'Prospect', 'Partner', 'Contractor'].map((t) => <option key={t}>{t}</option>)}
              </select>
              <input placeholder="Location" value={newAccount.location} onChange={(e) => setNewAccount({ ...newAccount, location: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Website" value={newAccount.website} onChange={(e) => setNewAccount({ ...newAccount, website: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <textarea placeholder="Notes" value={newAccount.notes} onChange={(e) => setNewAccount({ ...newAccount, notes: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewAccount(false)} className="px-4 py-2 text-slate-300 hover:text-white text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Create Account'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Contact Modal */}
      {showNewContact && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-md p-6">
            <h2 className="text-white font-semibold text-lg mb-4">Add Contact</h2>
            <form onSubmit={handleCreateContact} className="space-y-3">
              <input required placeholder="Name" value={newContact.name} onChange={(e) => setNewContact({ ...newContact, name: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Role" value={newContact.role} onChange={(e) => setNewContact({ ...newContact, role: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Email" type="email" value={newContact.email} onChange={(e) => setNewContact({ ...newContact, email: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <input placeholder="Phone" value={newContact.phone} onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewContact(false)} className="px-4 py-2 text-slate-300 hover:text-white text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Add Contact'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Signal Modal */}
      {showNewSignal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-md p-6">
            <h2 className="text-white font-semibold text-lg mb-4">Add Trigger Signal</h2>
            <form onSubmit={handleCreateSignal} className="space-y-3">
              <select value={newSignal.signal_type} onChange={(e) => setNewSignal({ ...newSignal, signal_type: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                {['expansion', 'renewal', 'pain', 'tender'].map((t) => <option key={t}>{t}</option>)}
              </select>
              <textarea required placeholder="Description" value={newSignal.description} onChange={(e) => setNewSignal({ ...newSignal, description: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none" />
              <input placeholder="Source (e.g. LinkedIn, press)" value={newSignal.source} onChange={(e) => setNewSignal({ ...newSignal, source: e.target.value })} className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowNewSignal(false)} className="px-4 py-2 text-slate-300 hover:text-white text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving…' : 'Add Signal'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
