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
  stage?: string;
  location?: string;
  website?: string;
  logo_url?: string;
  tags?: string;
  notes?: string;
  annual_revenue?: number;
  tier_target?: string;
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
  title: string;
  description?: string;
  source_url?: string;
  status?: string;
  detected_at?: string;
}

export interface Opportunity {
  id: number;
  account_id: number;
  title: string;
  description?: string;
  stage: string;
  estimated_value?: number;
  currency?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Qualification {
  id: number;
  opportunity_id: number;
  budget_confidence: number;
  route_to_market_clarity: number;
  incumbent_lock_in_risk: number;
  procurement_timeline_realism: number;
  technical_fit: number;
  tier_level?: string;
  uptime_target?: number;
  mep_complexity?: string;
  live_environment: boolean;
  overall_score: number;
  go_no_go: 'go' | 'no_go' | 'conditional';
  rationale?: string;
  scored_at?: string;
}

export interface Bid {
  id: number;
  opportunity_id: number;
  title: string;
  tender_ref?: string;
  submission_date?: string;
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
  bid_id: number;
  project_type: string;
  tier_level?: string;
  total_budget?: number;
  contingency_pct?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ScopeGap {
  id: number;
  project_id: number;
  category: string;
  description: string;
  identified: boolean;
  owner_agreed: boolean;
  included_in_price: boolean;
  notes?: string;
}

export interface ChecklistItem {
  id: number;
  project_id: number;
  category: string;
  item: string;
  completed: boolean;
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

// ── Accounts CSV ───────────────────────────────────────────────────────────

export interface CsvImportResult {
  created: number;
  skipped: number;
  errors: string[];
  message: string;
}

export const accountsCsvApi = {
  exportUrl: () => `${BASE_URL}/accounts/export/csv`,
  templateUrl: () => `${BASE_URL}/accounts/template/csv`,
  import: (file: File): Promise<CsvImportResult> => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE_URL}/accounts/import/csv`, { method: 'POST', body: form }).then(
      async (res) => {
        if (!res.ok) throw new Error(`CSV import failed: ${await res.text()}`);
        return res.json() as Promise<CsvImportResult>;
      }
    );
  },
};

// ── Website Swoop ──────────────────────────────────────────────────────────

export interface SwoopPersonnel {
  name: string;
  role?: string | null;
  linkedin?: string | null;
  x_handle?: string | null;
}

export interface SwoopIntel {
  company_name?: string;
  type?: string;
  location?: string;
  tags?: string[];
  key_personnel?: SwoopPersonnel[];
  recent_news?: string[];
  stock_ticker?: string | null;
  triggers?: string[];
  intel_summary?: string;
  suggested_touchpoint?: string;
  raw_response?: string;
}

export interface SwoopResult {
  status: string;
  account_id: number;
  created: boolean;
  intel: SwoopIntel;
}

export const swoopApi = {
  swoop: (url: string) =>
    request<SwoopResult>('/accounts/swoop', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),
};

export interface QualificationInput {
  budget_confidence: number;
  route_to_market_clarity: number;
  incumbent_lock_in_risk: number;
  procurement_timeline_realism: number;
  technical_fit: number;
  tier_level?: string;
  uptime_target?: number;
  mep_complexity?: string;
  live_environment?: boolean;
  rationale?: string;
}

// ── Opportunities ──────────────────────────────────────────────────────────

export const opportunitiesApi = {
  list: () => request<Opportunity[]>('/opportunities'),
  create: (data: Partial<Opportunity>) => request<Opportunity>('/opportunities', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: number) => request<Opportunity>(`/opportunities/${id}`),
  update: (id: number, data: Partial<Opportunity>) => request<Opportunity>(`/opportunities/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/opportunities/${id}`, { method: 'DELETE' }),
  qualify: (id: number, data: QualificationInput) => request<Qualification>(`/opportunities/${id}/qualify`, { method: 'POST', body: JSON.stringify(data) }),
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
  getScopeGapReport: (id: number) => request<{ risk_score: number; total_items: number; identified_count: number; not_included_in_price: number }>(`/estimating/${id}/scope-gap-report`),
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
  stock_ticker?: string;
  stock_price?: string;
  linkedin_posts?: string;
  x_posts?: string;
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

// ── Tender Intelligence Types ──────────────────────────────────────────────

export interface TenderAward {
  id: number;
  authority_name: string;
  winning_company: string;
  contract_value?: number;
  contract_currency?: string;
  scope_summary?: string;
  cpv_codes?: string[];
  award_date?: string;
  duration_months?: number;
  source_url?: string;
  framework: boolean;
  region?: string;
  competitors?: string[];
  mw_capacity?: number;
  created_at?: string;
}

export interface CPIResult {
  company: string;
  award_count: number;
  total_value: number;
  avg_price_per_mw?: number;
  cpi?: number;
  interpretation: string;
}

export interface WinScoreResult {
  company: string;
  win_probability: number;
  cpi?: number;
  breakdown: Record<string, number>;
}

export interface RelationshipSuggestResult {
  company_name: string;
  timing_score: number;
  recommend_contact: boolean;
  suggested_angle: string;
  why_now: string;
  what_to_mention: string;
  what_to_avoid: string;
  risk_flags: string;
}

// ── Call Intelligence Types ────────────────────────────────────────────────

export interface KeyPoint {
  text: string;
  type: 'job_discussion' | 'competitor_mention' | 'company_mention' | 'general';
  mentioned_company?: string;
  mentioned_job_title?: string;
  context?: string;
  linked_opportunity_id?: number;
  linked_by?: string;
  linked_at?: string;
  what_was_said?: string;
  action?: 'linked_existing' | 'created_new';
}

export interface OpportunitySuggestion {
  id: number;
  title: string;
  stage: string;
  account_name?: string;
  confidence: number;
  match_reason: string;
}

export interface KeyPointSuggestResult {
  key_point: KeyPoint;
  suggestions: OpportunitySuggestion[];
  auto_create_payload: {
    title: string;
    description: string;
    stage: string;
    mentioned_company?: string;
    type: string;
  };
}

export interface CallIntelligence {
    account_id?: number;
    account_name?: string;
  id: number;
  company_name?: string;
  executive_name?: string;
    audio_file_url?: string;
    call_date?: string;
  transcript?: string;
  sentiment_score?: number;
  competitor_mentions?: string[];
  budget_signals?: string[];
  timeline_mentions?: string[];
  risk_language?: string[];
  objection_categories?: string[];
  next_steps?: string;
  key_points?: KeyPoint[];
  created_at?: string;
}

// ── Tender API ─────────────────────────────────────────────────────────────

export const tenderApi = {
  list: (company?: string) =>
    request<TenderAward[]>(`/tenders${company ? `?company=${encodeURIComponent(company)}` : ''}`),
  create: (data: Partial<TenderAward>) =>
    request<TenderAward>('/tenders', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: number) => request<TenderAward>(`/tenders/${id}`),
  delete: (id: number) => request<void>(`/tenders/${id}`, { method: 'DELETE' }),
  getCPI: (company: string, regionFactor?: number) =>
    request<CPIResult>(`/tenders/score/cpi?company=${encodeURIComponent(company)}${regionFactor ? `&region_factor=${regionFactor}` : ''}`),
  getWinScore: (data: {
    company: string;
    historical_win_rate: number;
    expansion_activity_score: number;
    hiring_velocity: number;
    risk_score: number;
    region_factor?: number;
  }) => request<WinScoreResult>('/tenders/score/win', { method: 'POST', body: JSON.stringify(data) }),
  suggestRelationship: (data: {
    company_name: string;
    recent_events: string[];
    days_since_events: number[];
  }) =>
    request<RelationshipSuggestResult>('/tenders/score/relationship', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// ── Calls API ──────────────────────────────────────────────────────────────

export const callsApi = {
  analyse: (data: { 
    company_name?: string; 
    executive_name?: string; 
    transcript?: string; 
    account_id?: number;
    call_date?: string;
    file?: File;
  }) => {
    const form = new FormData();
    if (data.company_name) form.append('company_name', data.company_name);
    if (data.executive_name) form.append('executive_name', data.executive_name);
    if (data.transcript) form.append('transcript', data.transcript);
    if (data.account_id) form.append('account_id', data.account_id.toString());
    if (data.call_date) form.append('call_date', data.call_date);
    if (data.file) form.append('file', data.file);
    return fetch(`${BASE_URL}/calls/analyse`, { method: 'POST', body: form }).then(async (res) => {
      if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
      return res.json() as Promise<CallIntelligence>;
    });
  },
  list: (filters?: { company_name?: string; account_id?: number }) => {
    const params = new URLSearchParams();
    if (filters?.company_name) params.append('company_name', filters.company_name);
    if (filters?.account_id !== undefined) params.append('account_id', filters.account_id.toString());
    const query = params.toString();
    return request<CallIntelligence[]>(`/calls${query ? `?${query}` : ''}`);
  },
  get: (id: number) => request<CallIntelligence>(`/calls/${id}`),
  delete: (id: number) => request<void>(`/calls/${id}`, { method: 'DELETE' }),
  suggestKeyPointLinks: (callId: number, pointIndex: number) =>
    request<KeyPointSuggestResult>(`/calls/${callId}/key-points/${pointIndex}/suggest`),
  linkKeyPoint: (callId: number, pointIndex: number, opportunityId?: number) =>
    request<CallIntelligence>(
      `/calls/${callId}/key-points/${pointIndex}/link${opportunityId != null ? `?opportunity_id=${opportunityId}` : ''}`,
      { method: 'POST' },
    ),
};

// ── Lead-Time Intelligence ────────────────────────────────────────────────

export interface LeadTimeItem {
  id: number;
  category: string;
  manufacturer?: string;
  model_ref?: string;
  description: string;
  lead_weeks_min: number;
  lead_weeks_max: number;
  lead_weeks_typical?: number;
  region?: string;
  notes?: string;
  source?: string;
  last_verified?: string;
  created_at?: string;
  updated_at?: string;
}

// ── Internal helper: build optional query string ─────────────────────────────

function _qs(params: Record<string, string | boolean | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== '');
  if (entries.length === 0) return '';
  return '?' + new URLSearchParams(
    entries.map(([k, v]) => [k, String(v)] as [string, string]),
  ).toString();
}

export const leadTimeApi = {
  list: (category?: string, region?: string) =>
    request<LeadTimeItem[]>(`/lead-times${_qs({ category, region })}`),
  create: (data: Partial<LeadTimeItem>) =>
    request<LeadTimeItem>('/lead-times', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<LeadTimeItem>) =>
    request<LeadTimeItem>(`/lead-times/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/lead-times/${id}`, { method: 'DELETE' }),
  seed: () =>
    request<LeadTimeItem[]>('/lead-times/seed', { method: 'POST' }),
};

// ── Bid Debrief & Learning Loop ───────────────────────────────────────────

export interface BidDebrief {
  id: number;
  bid_id: number;
  outcome: 'won' | 'lost' | 'withdrawn' | 'no_award';
  our_score?: number;
  winner_score?: number;
  our_price?: number;
  winner_price?: number;
  evaluation_criteria?: string;
  client_feedback?: string;
  strengths?: string;
  weaknesses?: string;
  winning_company?: string;
  lessons_learned?: string;
  process_improvements?: string;
  bid_manager?: string;
  debrief_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LearningInsight {
  total_bids_debriefed: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  avg_our_score?: number;
  avg_winner_score?: number;
  avg_price_gap_pct?: number;
  top_strengths: string[];
  top_weaknesses: string[];
  common_winners: string[];
}

export const debriefApi = {
  get: (bidId: number) => request<BidDebrief>(`/bids/${bidId}/debrief`),
  create: (bidId: number, data: Partial<BidDebrief>) =>
    request<BidDebrief>(`/bids/${bidId}/debrief`, { method: 'POST', body: JSON.stringify({ ...data, bid_id: bidId }) }),
  update: (bidId: number, data: Partial<BidDebrief>) =>
    request<BidDebrief>(`/bids/${bidId}/debrief`, { method: 'PATCH', body: JSON.stringify(data) }),
  list: () => request<BidDebrief[]>('/debriefs'),
  insights: () => request<LearningInsight>('/debriefs/insights'),
};

// ── Procurement Frameworks ─────────────────────────────────────────────────

export interface ProcurementFramework {
  id: number;
  name: string;
  authority: string;
  reference?: string;
  categories?: string;
  status: 'active' | 'expiring_soon' | 'expired' | 'pending' | 'not_listed';
  start_date?: string;
  expiry_date?: string;
  url?: string;
  region?: string;
  notes?: string;
  we_are_listed: boolean;
  lot_numbers?: string;
  created_at?: string;
  updated_at?: string;
}

export const frameworksApi = {
  list: (status?: string, region?: string, we_are_listed?: boolean) =>
    request<ProcurementFramework[]>(
      `/frameworks${_qs({ status, region, ...(we_are_listed !== undefined ? { we_are_listed } : {}) })}`,
    ),
  create: (data: Partial<ProcurementFramework>) =>
    request<ProcurementFramework>('/frameworks', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<ProcurementFramework>) =>
    request<ProcurementFramework>(`/frameworks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/frameworks/${id}`, { method: 'DELETE' }),
};

// ── Export helpers (direct download URLs) ────────────────────────────────────

export const exportApi = {
  pursuitPackPdfUrl: (bidId: number) => `${BASE_URL}/bids/${bidId}/export/pursuit-pack-pdf`,
  tenderResponseDocxUrl: (bidId: number) => `${BASE_URL}/bids/${bidId}/export/tender-response-docx`,
  complianceMatrixXlsxUrl: (bidId: number) => `${BASE_URL}/bids/${bidId}/export/compliance-matrix-xlsx`,
};

// ── Compliance Answer Generation ──────────────────────────────────────────────

export const complianceAnswerApi = {
  generate: (bidId: number, itemId: number, companyContext?: string) =>
    request<ComplianceItem>(`/bids/${bidId}/compliance/${itemId}/generate-answer`, {
      method: 'POST',
      body: JSON.stringify({ company_context: companyContext ?? null }),
    }),
};


// ── Intelligence Database Types ────────────────────────────────────────────

export interface InfrastructureProject {
  id: number;
  name: string;
  company?: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  capacity_mw?: number;
  capex_millions?: number;
  capex_currency?: string;
  stage?: string;
  project_type?: string;
  partners?: string;
  source_url?: string;
  source_name?: string;
  confidence_score?: number;
  signal_type?: string;
  is_duplicate?: boolean;
  notes?: string;
  detected_at?: string;
}

export interface CompanyProfile {
  id: number;
  name: string;
  category?: string;
  headquarters?: string;
  stock_ticker?: string;
  website?: string;
  known_partners?: string;
  total_capacity_mw?: number;
  total_capex_millions?: number;
  active_projects?: number;
  regions_active?: string;
  description?: string;
}

export interface OpportunitySignal {
  id: number;
  project_id?: number;
  opportunity_type?: string;
  title: string;
  company?: string;
  location?: string;
  potential_suppliers?: string;
  likelihood_score?: number;
  estimated_value_millions?: number;
  estimated_tender_date?: string;
  source_signal_url?: string;
  is_actioned?: boolean;
  detected_at?: string;
}

export interface ProjectStats {
  total_projects: number;
  total_capacity_mw: number;
  total_capex_millions: number;
  by_stage: Record<string, number>;
  by_type: Record<string, number>;
  top_companies_by_mw: Array<{ company: string; total_mw: number }>;
}

export interface HeatmapPoint {
  location: string;
  project_count: number;
  total_mw: number;
  total_capex: number;
  lat?: number;
  lon?: number;
}

export interface NewsArticle {
  id: number;
  title: string;
  url?: string;
  source_name?: string;
  summary?: string;
  category?: string;
  keywords_matched?: string;
  published_at?: string;
  source_type?: string;
  fetched_at?: string;
}

export interface IntelligenceStatus {
  collector: string;
  record_count: number;
  last_collected_at?: string;
}

// ── Intelligence API ───────────────────────────────────────────────────────

export const intelligenceApi = {
  // News
  runNewsAggregator: () => request<{ status: string; records_collected: number }>('/intelligence/news/run', { method: 'POST' }),
  listNews: (params?: { category?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set('category', params.category);
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<NewsArticle[]>(`/intelligence/news?${qs}`);
  },
  // Planning
  runPlanningScraper: () => request<{ status: string; records_collected: number }>('/intelligence/planning/run', { method: 'POST' }),
  listPlanning: (params?: { is_data_centre?: boolean; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.is_data_centre !== undefined) qs.set('is_data_centre', String(params.is_data_centre));
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<unknown[]>(`/intelligence/planning?${qs}`);
  },
  // Press releases
  runPressReleases: () => request<{ status: string }>('/intelligence/press-releases/run', { method: 'POST' }),
  listPressReleases: (params?: { vendor_name?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.vendor_name) qs.set('vendor_name', params.vendor_name);
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<unknown[]>(`/intelligence/press-releases?${qs}`);
  },
  // Jobs
  runJobDetector: () => request<{ status: string }>('/intelligence/jobs/run', { method: 'POST' }),
  listJobs: (params?: { company_name?: string; is_spike?: boolean; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.company_name) qs.set('company_name', params.company_name);
    if (params?.is_spike !== undefined) qs.set('is_spike', String(params.is_spike));
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<unknown[]>(`/intelligence/jobs?${qs}`);
  },
  // Infrastructure
  runInfraMonitor: () => request<{ status: string }>('/intelligence/infrastructure/run', { method: 'POST' }),
  listInfrastructure: (params?: { announcement_type?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.announcement_type) qs.set('announcement_type', params.announcement_type);
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<unknown[]>(`/intelligence/infrastructure?${qs}`);
  },
  // Status
  getStatus: () => request<IntelligenceStatus[]>('/intelligence/status'),
};

// ── Projects (Intelligence Database) API ──────────────────────────────────

export const projectsApi = {
  list: (params?: { stage?: string; company?: string; has_mw?: boolean; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.stage) qs.set('stage', params.stage);
    if (params?.company) qs.set('company', params.company);
    if (params?.has_mw !== undefined) qs.set('has_mw', String(params.has_mw));
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<InfrastructureProject[]>(`/projects/?${qs}`);
  },
  get: (id: number) => request<InfrastructureProject>(`/projects/${id}`),
  create: (data: Partial<InfrastructureProject>) => request<InfrastructureProject>('/projects/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<InfrastructureProject>) => request<InfrastructureProject>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/projects/${id}`, { method: 'DELETE' }),
  getStats: () => request<ProjectStats>('/projects/stats/summary'),
  getMapData: (stage?: string) => {
    const qs = stage ? `?stage=${stage}` : '';
    return request<InfrastructureProject[]>(`/projects/geo/map-data${qs}`);
  },
  getHeatmap: () => request<HeatmapPoint[]>('/projects/geo/heatmap'),
  listCompanies: (params?: { category?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set('category', params.category);
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<CompanyProfile[]>(`/projects/companies/?${qs}`);
  },
  createCompany: (data: Partial<CompanyProfile>) => request<CompanyProfile>('/projects/companies/', { method: 'POST', body: JSON.stringify(data) }),
  listOpportunities: (params?: { opportunity_type?: string; is_actioned?: boolean; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.opportunity_type) qs.set('opportunity_type', params.opportunity_type);
    if (params?.is_actioned !== undefined) qs.set('is_actioned', String(params.is_actioned));
    if (params?.limit) qs.set('limit', String(params.limit));
    return request<OpportunitySignal[]>(`/projects/opportunities/?${qs}`);
  },
  createOpportunity: (data: Partial<OpportunitySignal>) => request<OpportunitySignal>('/projects/opportunities/', { method: 'POST', body: JSON.stringify(data) }),
};

// ── Processing API ─────────────────────────────────────────────────────────

export const processingApi = {
  runAll: () => request<{ status: string; results: Record<string, unknown> }>('/processing/run-all', { method: 'POST' }),
  runParser: () => request<{ status: string; records_processed: number }>('/processing/parse/run', { method: 'POST' }),
  runEntities: () => request<{ status: string; records_processed: number }>('/processing/entities/run', { method: 'POST' }),
  runDeduplication: () => request<{ status: string; duplicate_groups: number; duplicates_flagged: number }>('/processing/deduplicate/run', { method: 'POST' }),
  runScoring: () => request<{ status: string; records_scored: number }>('/processing/score/run', { method: 'POST' }),
  runClassification: () => request<{ status: string; records_classified: number }>('/processing/classify/run', { method: 'POST' }),
};

// ── Agents API ─────────────────────────────────────────────────────────────

export interface AgentCatalogueEntry {
  id: string;
  name: string;
  icon: string;
  description: string;
  endpoint: string;
  input_field: string;
  placeholder: string;
}

export interface AgentResult {
  status: string;
  agent: string;
  result: Record<string, unknown>;
}

export const agentsApi = {
  catalogue: () => request<{ agents: AgentCatalogueEntry[] }>('/agents/catalogue'),
  runBuildCaptain: (requestText: string) =>
    request<AgentResult>('/agents/build-captain', {
      method: 'POST',
      body: JSON.stringify({ request: requestText }),
    }),
  runUiSurgeon: (description: string) =>
    request<AgentResult>('/agents/ui-surgeon', {
      method: 'POST',
      body: JSON.stringify({ description }),
    }),
  runTestPilot: (feature_description: string) =>
    request<AgentResult>('/agents/test-pilot', {
      method: 'POST',
      body: JSON.stringify({ feature_description }),
    }),
  runDataCurator: (context: string) =>
    request<AgentResult>('/agents/data-curator', {
      method: 'POST',
      body: JSON.stringify({ context }),
    }),
  runOpsBoss: (context: string) =>
    request<AgentResult>('/agents/ops-boss', {
      method: 'POST',
      body: JSON.stringify({ context }),
    }),
};


// ── Setup / Integration Status API ────────────────────────────────────────

export interface IntegrationStatus {
  configured: boolean;
  missing_vars: string[];
  required_for: string[];
  optional: boolean;
  setup_path: string;
  docs_url: string;
  note?: string;
  active_backend?: string;
  active_provider?: string;
}

export interface SetupStatus {
  integrations: Record<string, IntegrationStatus>;
  all_required_configured: boolean;
  auth_provider: string;
  storage_backend: string;
}

export const setupApi = {
  getStatus: () => request<SetupStatus>('/setup/status'),
};

// ── Signal Events API ──────────────────────────────────────────────────────

export interface SignalEvent {
  id: number;
  company_name: string;
  account_id?: number;
  event_type: string;
  title: string;
  description?: string;
  source_url?: string;
  relevance_score?: number;
  status: string;
  event_date?: string;
  detected_at: string;
}

export interface ExpansionScoreRequest {
  signal_events?: string[];
  days_since_events?: number[];
  hiring_count?: number;
  new_office_openings?: number;
  recent_acquisitions?: number;
}

export interface ExpansionScoreResult {
  expansion_activity_score: number;
  breakdown: Record<string, number>;
}

export const signalsApi = {
  list: (params?: { company_name?: string; account_id?: number; event_type?: string; status?: string; skip?: number; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.company_name) qs.set('company_name', params.company_name);
    if (params?.account_id !== undefined) qs.set('account_id', String(params.account_id));
    if (params?.event_type) qs.set('event_type', params.event_type);
    if (params?.status) qs.set('status', params.status);
    if (params?.skip !== undefined) qs.set('skip', String(params.skip));
    if (params?.limit !== undefined) qs.set('limit', String(params.limit));
    return request<SignalEvent[]>(`/signals?${qs}`);
  },
  get: (id: number) => request<SignalEvent>(`/signals/${id}`),
  create: (data: Partial<SignalEvent>) =>
    request<SignalEvent>('/signals', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<SignalEvent>) =>
    request<SignalEvent>(`/signals/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<void>(`/signals/${id}`, { method: 'DELETE' }),
  computeExpansionScore: (data: ExpansionScoreRequest) =>
    request<ExpansionScoreResult>('/signals/score/expansion', { method: 'POST', body: JSON.stringify(data) }),
};
