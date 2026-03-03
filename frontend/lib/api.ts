// Set NEXT_PUBLIC_API_URL in .env.local to point to your backend (default: http://localhost:8000/api/v1)
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface Account {
  id: number;
  name: string;
  type: string;
  location?: string;
  website?: string;
  notes?: string;
  stage?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Contact {
  id: number;
  account_id: number;
  name: string;
  role?: string;
  email?: string;
  phone?: string;
}

export interface TriggerSignal {
  id: number;
  account_id: number;
  signal_type: string;
  description?: string;
  source?: string;
  detected_at?: string;
}

export interface Opportunity {
  id: number;
  account_id: number;
  title: string;
  stage: string;
  estimated_value?: number;
  probability?: number;
  qualification_score?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Qualification {
  id: number;
  opportunity_id: number;
  score: number;
  criteria: Record<string, number>;
  recommendation?: string;
  notes?: string;
  created_at?: string;
}

export interface Bid {
  id: number;
  opportunity_id: number;
  title: string;
  status: string;
  win_themes?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BidDocument {
  id: number;
  bid_id: number;
  filename: string;
  doc_type?: string;
  content_text?: string;
  extracted_requirements?: string;
  uploaded_at?: string;
}

export interface ComplianceItem {
  id: number;
  bid_id: number;
  requirement: string;
  compliance_status: string;
  evidence?: string;
  owner?: string;
  category?: string;
  notes?: string;
}

export interface RFI {
  id: number;
  bid_id: number;
  question: string;
  category?: string;
  priority: string;
  status: string;
  answer?: string;
  submitted_at?: string;
  answered_at?: string;
}

export interface EstimatingProject {
  id: number;
  bid_id?: number;
  title: string;
  project_type?: string;
  tier?: string;
  budget?: number;
  scope_gap_score?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ScopeGap {
  id: number;
  estimating_id: number;
  category: string;
  item: string;
  status: string;
  risk_level?: string;
  notes?: string;
}

export interface ChecklistItem {
  id: number;
  estimating_id: number;
  category: string;
  item: string;
  checked: boolean;
  notes?: string;
}

// ── Accounts ───────────────────────────────────────────────────────────────

export const accountsApi = {
  list: () => request<Account[]>('/accounts'),
  create: (data: Partial<Account>) => request<Account>('/accounts', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: number) => request<Account>(`/accounts/${id}`),
  update: (id: number, data: Partial<Account>) => request<Account>(`/accounts/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/accounts/${id}`, { method: 'DELETE' }),
  listContacts: (id: number) => request<Contact[]>(`/contacts?account_id=${id}`),
  createContact: (id: number, data: Partial<Contact>) => request<Contact>(`/contacts`, { method: 'POST', body: JSON.stringify({ ...data, account_id: id }) }),
  listTriggerSignals: (id: number) => request<TriggerSignal[]>(`/trigger-signals?account_id=${id}`),
  createTriggerSignal: (id: number, data: Partial<TriggerSignal>) => request<TriggerSignal>(`/trigger-signals`, { method: 'POST', body: JSON.stringify({ ...data, account_id: id }) }),
};

// ── Opportunities ──────────────────────────────────────────────────────────

export const opportunitiesApi = {
  list: () => request<Opportunity[]>('/opportunities'),
  create: (data: Partial<Opportunity>) => request<Opportunity>('/opportunities', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: number) => request<Opportunity>(`/opportunities/${id}`),
  update: (id: number, data: Partial<Opportunity>) => request<Opportunity>(`/opportunities/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/opportunities/${id}`, { method: 'DELETE' }),
  qualify: (id: number, data: Partial<Qualification>) => request<Qualification>(`/opportunities/${id}/qualify`, { method: 'POST', body: JSON.stringify(data) }),
  getQualification: (id: number) => request<Qualification>(`/opportunities/${id}/qualification`),
};

// ── Bids ───────────────────────────────────────────────────────────────────

export const bidsApi = {
  list: () => request<Bid[]>('/bids'),
  create: (data: Partial<Bid>) => request<Bid>('/bids', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: number) => request<Bid>(`/bids/${id}`),
  update: (id: number, data: Partial<Bid>) => request<Bid>(`/bids/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/bids/${id}`, { method: 'DELETE' }),
  listDocuments: (id: number) => request<BidDocument[]>(`/bids/${id}/documents`),
  createDocument: (id: number, data: Partial<BidDocument>) => request<BidDocument>(`/bids/${id}/documents`, { method: 'POST', body: JSON.stringify(data) }),
  listComplianceItems: (id: number) => request<ComplianceItem[]>(`/bids/${id}/compliance`),
  createComplianceItem: (id: number, data: Partial<ComplianceItem>) => request<ComplianceItem>(`/bids/${id}/compliance`, { method: 'POST', body: JSON.stringify(data) }),
  listRFIs: (id: number) => request<RFI[]>(`/bids/${id}/rfis`),
  createRFI: (id: number, data: Partial<RFI>) => request<RFI>(`/bids/${id}/rfis`, { method: 'POST', body: JSON.stringify(data) }),
  generateComplianceMatrix: (id: number) => request<ComplianceItem[]>(`/bids/${id}/generate-compliance-matrix`, { method: 'POST' }),
  generateRFIs: (id: number) => request<RFI[]>(`/bids/${id}/generate-rfis`, { method: 'POST' }),
};

// ── Estimating ─────────────────────────────────────────────────────────────

export const estimatingApi = {
  list: () => request<EstimatingProject[]>('/estimating'),
  create: (data: Partial<EstimatingProject>) => request<EstimatingProject>('/estimating', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: number) => request<EstimatingProject>(`/estimating/${id}`),
  listScopeGaps: (id: number) => request<ScopeGap[]>(`/estimating/${id}/scope-gaps`),
  createScopeGap: (id: number, data: Partial<ScopeGap>) => request<ScopeGap>(`/estimating/${id}/scope-gaps`, { method: 'POST', body: JSON.stringify(data) }),
  listChecklist: (id: number) => request<ChecklistItem[]>(`/estimating/${id}/checklist`),
  createChecklistItem: (id: number, data: Partial<ChecklistItem>) => request<ChecklistItem>(`/estimating/${id}/checklist`, { method: 'POST', body: JSON.stringify(data) }),
  getScopeGapReport: (id: number) => request<{ score: number; items: ScopeGap[] }>(`/estimating/${id}/scope-gap-report`),
};

// ── Intelligence Types ─────────────────────────────────────────────────────

export interface ExecutiveProfile {
  id: number;
  company_intel_id: number;
  name: string;
  role?: string;
  professional_focus?: string;
  public_interests?: string;
  recent_interviews?: string;
  conference_appearances?: string;
  charity_involvement?: string;
  communication_style?: string;
  conversation_angles?: string;
  created_at?: string;
}

export interface NewsItem {
  id: number;
  company_intel_id?: number;
  title: string;
  summary?: string;
  source_url?: string;
  category: string;
  company_name?: string;
  published_at?: string;
  detected_at?: string;
}

export interface CompanyIntel {
  id: number;
  website: string;
  company_name?: string;
  business_model?: string;
  locations?: string;
  expansion_signals?: string;
  technology_indicators?: string;
  financial_summary?: string;
  earnings_highlights?: string;
  competitor_mentions?: string;
  strategic_risks?: string;
  bid_opportunities?: string;
  created_at?: string;
  executives?: ExecutiveProfile[];
  news_items?: NewsItem[];
}

export interface CompanyIntelSummary {
  id: number;
  website: string;
  company_name?: string;
  created_at?: string;
}

export interface BlogPost {
  id: number;
  company_intel_id?: number;
  title: string;
  slug: string;
  body_markdown: string;
  meta_description?: string;
  seo_keywords?: string;
  linkedin_variant?: string;
  x_variant?: string;
  status: string;
  published_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BlogPostSummary {
  id: number;
  title: string;
  slug: string;
  status: string;
  created_at?: string;
}

export interface UploadedPhoto {
  id: number;
  filename: string;
  original_filename: string;
  storage_path: string;
  content_type?: string;
  size_bytes?: number;
  alt_text?: string;
  ai_description?: string;
  company_intel_id?: number;
  bid_id?: number;
  uploaded_at?: string;
}

// ── Intelligence API ───────────────────────────────────────────────────────

export const intelApi = {
  researchCompany: (website: string) =>
    request<CompanyIntel>('/intel/company', { method: 'POST', body: JSON.stringify({ website }) }),
  listCompanies: () => request<CompanyIntelSummary[]>('/intel/companies'),
  getCompany: (id: number) => request<CompanyIntel>(`/intel/companies/${id}`),
  deleteCompany: (id: number) => request<void>(`/intel/companies/${id}`, { method: 'DELETE' }),
  listNews: (company_intel_id?: number) =>
    request<NewsItem[]>(`/intel/news${company_intel_id ? `?company_intel_id=${company_intel_id}` : ''}`),
  createNews: (data: Partial<NewsItem>) =>
    request<NewsItem>('/intel/news', { method: 'POST', body: JSON.stringify(data) }),
};

// ── Blog API ───────────────────────────────────────────────────────────────

export const blogApi = {
  generate: (data: {
    topic: string;
    company_intel_id?: number;
    tone?: string;
    target_persona?: string;
    word_count?: number;
    seo_keywords?: string;
    cta?: string;
  }) => request<BlogPost>('/blog/generate', { method: 'POST', body: JSON.stringify(data) }),
  list: (status?: string) =>
    request<BlogPostSummary[]>(`/blog${status ? `?status_filter=${status}` : ''}`),
  get: (id: number) => request<BlogPost>(`/blog/${id}`),
  update: (id: number, data: Partial<BlogPost>) =>
    request<BlogPost>(`/blog/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  approve: (id: number) => request<BlogPost>(`/blog/${id}/approve`, { method: 'POST' }),
  publish: (id: number) => request<BlogPost>(`/blog/${id}/publish`, { method: 'POST' }),
  delete: (id: number) => request<void>(`/blog/${id}`, { method: 'DELETE' }),
};

// ── Uploads API ────────────────────────────────────────────────────────────

export const uploadsApi = {
  uploadPhoto: (file: File, opts?: { alt_text?: string; company_intel_id?: number; bid_id?: number }) => {
    const form = new FormData();
    form.append('file', file);
    if (opts?.alt_text) form.append('alt_text', opts.alt_text);
    if (opts?.company_intel_id) form.append('company_intel_id', String(opts.company_intel_id));
    if (opts?.bid_id) form.append('bid_id', String(opts.bid_id));
    return fetch(`${BASE_URL}/uploads/photos`, { method: 'POST', body: form }).then(async (res) => {
      if (!res.ok) throw new Error(`Upload failed: ${await res.text()}`);
      return res.json() as Promise<UploadedPhoto>;
    });
  },
  list: (opts?: { company_intel_id?: number; bid_id?: number }) => {
    const params = new URLSearchParams();
    if (opts?.company_intel_id) params.set('company_intel_id', String(opts.company_intel_id));
    if (opts?.bid_id) params.set('bid_id', String(opts.bid_id));
    const qs = params.toString() ? `?${params}` : '';
    return request<UploadedPhoto[]>(`/uploads/photos${qs}`);
  },
  get: (id: number) => request<UploadedPhoto>(`/uploads/photos/${id}`),
  fileUrl: (id: number) => `${BASE_URL}/uploads/photos/${id}/file`,
  delete: (id: number) => request<void>(`/uploads/photos/${id}`, { method: 'DELETE' }),
};
