# aLiGN

**AI-native Bid + Delivery OS for Data Centre Refurbs & New Builds**

> "Win more DC projects with less bid pain."

aLiGN replaces your messy stack of spreadsheets, email chains, SharePoint folders, and tribal knowledge with a structured, AI-assisted platform that guides every deal from `Target → Lead → Qualified → Bid → Win → Deliver → Expand`.

---

## 🧩 Modules

| Module | What it does |
|--------|-------------|
| 🗺️ **Account & Site Intelligence** | Target list builder, trigger signal alerts (planning, grid, hiring spikes), contact/stakeholder mapping |
| 📌 **Opportunity Qualification** | Go/No-Go scoring across 5 dimensions: budget confidence, route-to-market, incumbent risk, timeline realism, technical fit |
| 📦 **Bid Pack Builder** | Document ingestion, compliance matrix autopilot, RFI generator, method statement templates |
| 🧮 **Estimating + Scope Gap Detector** | Scope completeness scoring, 8-category gap checker (enabling works, temp power, commissioning etc.), lead-time alerts |
| 🧯 **Delivery Handover Mode** | Bid → project setup, scope baseline, change control, outage planning |

---

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- (Optional) Docker + Docker Compose

> **Windows users:** see the [Windows Installation Guide](docs/windows-install.md) for step-by-step instructions, including a one-click installer option.

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
docker-compose up --build
```

- Frontend: http://localhost:3000  
- Backend API docs: http://localhost:8000/docs

### Option B — Manual

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
cp ../.env.example .env.local    # set NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm install
npm run dev
```

---

## 🏗️ Architecture

```
aLiGN/
├── backend/           # Python · FastAPI · SQLAlchemy (SQLite → Postgres)
│   ├── models/        # Account, Contact, TriggerSignal, Opportunity,
│   │                  # QualificationScore, Bid, BidDocument,
│   │                  # ComplianceItem, RFI, EstimatingProject,
│   │                  # ScopeGapItem, ChecklistItem
│   ├── schemas/       # Pydantic v2 request/response models
│   └── routers/       # 55+ REST endpoints at /api/v1
├── frontend/          # Next.js 15 (App Router) · TypeScript · Tailwind CSS
│   ├── app/           # Dashboard, Accounts, Opportunities, Bids, Estimating
│   ├── components/    # Sidebar, Header, shared UI
│   └── lib/api.ts     # Typed API client
└── docker-compose.yml
```

### Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | SQLite (dev) / PostgreSQL 16 (prod) |
| File Storage | Local filesystem (dev) / Amazon S3 (prod) |
| Auth | Clerk or Auth0 JWT verification (configurable via `AUTH_PROVIDER`) |
| Document Parsing | pdfplumber (PDF), python-docx (Word) |
| Exports | reportlab (PDF), python-docx (Word), openpyxl (Excel) |
| Audit | HTTP middleware — all writes logged |
| Docs | OpenAPI at `/docs` and `/redoc` |

---

## 📡 API Overview

```
GET  /health

# Accounts
GET/POST        /api/v1/accounts
GET/PUT/DELETE  /api/v1/accounts/{id}
GET/POST        /api/v1/accounts/{id}/contacts
GET/POST        /api/v1/accounts/{id}/trigger-signals

# Opportunities
GET/POST        /api/v1/opportunities
GET/PUT/DELETE  /api/v1/opportunities/{id}
POST            /api/v1/opportunities/{id}/qualify
GET             /api/v1/opportunities/{id}/qualification

# Bids
GET/POST        /api/v1/bids
GET/PUT/DELETE  /api/v1/bids/{id}
GET/POST        /api/v1/bids/{id}/documents
POST            /api/v1/bids/{id}/documents/upload-and-parse   ← PDF/Word upload + extract
POST            /api/v1/bids/{id}/documents/{doc_id}/parse     ← LLM re-parse
GET/POST        /api/v1/bids/{id}/compliance
POST            /api/v1/bids/{id}/compliance/{item_id}/generate-answer  ← LLM answer draft
GET/POST        /api/v1/bids/{id}/rfis
POST            /api/v1/bids/{id}/generate-compliance-matrix
POST            /api/v1/bids/{id}/generate-rfis
GET/POST/PATCH/DELETE /api/v1/bids/{id}/debrief               ← Bid debrief
GET             /api/v1/bids/{id}/export/pursuit-pack-pdf      ← PDF export
GET             /api/v1/bids/{id}/export/tender-response-docx  ← Word export
GET             /api/v1/bids/{id}/export/compliance-matrix-xlsx ← Excel export

# Debriefs (learning loop)
GET             /api/v1/debriefs
GET             /api/v1/debriefs/insights

# Estimating
GET/POST        /api/v1/estimating
GET/PUT/DELETE  /api/v1/estimating/{id}
GET/POST        /api/v1/estimating/{id}/scope-gaps
GET/POST        /api/v1/estimating/{id}/checklist
GET             /api/v1/estimating/{id}/scope-gap-report

# Lead-time intelligence
GET/POST        /api/v1/lead-times
GET/PATCH/DELETE /api/v1/lead-times/{id}
POST            /api/v1/lead-times/seed                        ← Seed default dataset

# Procurement frameworks
GET/POST        /api/v1/frameworks
GET/PATCH/DELETE /api/v1/frameworks/{id}
```

---

## 🗺️ Roadmap

- [x] Document parsing (PDF/Word → structured requirements via `pdfplumber` + `python-docx`)
- [x] LLM-assisted compliance answer generation
- [x] Lead-time intelligence database (switchgear, UPS, chillers, generators)
- [x] Bid debrief capture + learning loop
- [x] Framework & procurement tracker
- [x] Export: Pursuit Pack PDF, Tender Response Pack (Word), Compliance Matrix (Excel)
- [x] PostgreSQL + S3 production config
- [x] SSO / Auth (Clerk or Auth0)
