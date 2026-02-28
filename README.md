# ContractGHOST

**AI-native Bid + Delivery OS for Data Centre Refurbs & New Builds**

> "Win more DC projects with less bid pain."

ContractGHOST replaces your messy stack of spreadsheets, email chains, SharePoint folders, and tribal knowledge with a structured, AI-assisted platform that guides every deal from `Target → Lead → Qualified → Bid → Win → Deliver → Expand`.

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
ContractGHOST/
├── backend/           # Python · FastAPI · SQLAlchemy (SQLite → Postgres)
│   ├── models/        # Account, Contact, TriggerSignal, Opportunity,
│   │                  # QualificationScore, Bid, BidDocument,
│   │                  # ComplianceItem, RFI, EstimatingProject,
│   │                  # ScopeGapItem, ChecklistItem
│   ├── schemas/       # Pydantic v2 request/response models
│   └── routers/       # 55+ REST endpoints at /api/v1
├── frontend/          # Next.js 14 (App Router) · TypeScript · Tailwind CSS
│   ├── app/           # Dashboard, Accounts, Opportunities, Bids, Estimating
│   ├── components/    # Sidebar, Header, shared UI
│   └── lib/api.ts     # Typed API client
└── docker-compose.yml
```

### Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | Role-based (Clerk/Auth0 ready) |
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
GET/POST        /api/v1/bids/{id}/compliance-items
GET/POST        /api/v1/bids/{id}/rfis
POST            /api/v1/bids/{id}/generate-compliance-matrix
POST            /api/v1/bids/{id}/generate-rfis

# Estimating
GET/POST        /api/v1/estimating
GET/PUT/DELETE  /api/v1/estimating/{id}
GET/POST        /api/v1/estimating/{id}/scope-gaps
GET/POST        /api/v1/estimating/{id}/checklist
GET             /api/v1/estimating/{id}/scope-gap-report
```

---

## 🗺️ Roadmap

- [ ] Document parsing (PDF/Word → structured requirements via `unstructured` + `pdfplumber`)
- [ ] LLM-assisted compliance answer generation
- [ ] Lead-time intelligence database (switchgear, UPS, chillers, generators)
- [ ] Bid debrief capture + learning loop
- [ ] Framework & procurement tracker
- [ ] Export: Pursuit Pack PDF, Tender Response Pack (Word), Compliance Matrix (Excel)
- [ ] PostgreSQL + S3 production config
- [ ] SSO / Auth (Clerk or Auth0)
