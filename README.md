# XALiGn

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

> **Windows users:** see the [Windows Installation Guide](docs/windows-install.md) for step-by-step instructions, including a one-click installer option.

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
docker-compose up --build
```


### Option B — Manual

**Backend:**

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
cp ../.env.example .env.local    # set NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm install
npm run dev
```


## 🧪 Testing

### Windows Desktop Testing

For Windows desktop deployments, the notification system includes comprehensive testing tools:

**Quick Start:** See [TESTING-QUICK-START.md](TESTING-QUICK-START.md)

**Setup Gmail OAuth:**
```cmd
cd backend
setup-gmail-oauth.bat
```

**Run Tests:**
```cmd
cd backend
test-notifications.bat
```

**Available Test Tools:**
- `backend/setup-gmail-oauth.bat` - Interactive OAuth wizard
- `backend/test-notifications.bat` - Automated test suite (7 tests)
- `backend/tests/manual_test_notifications.py` - Interactive debugging console
- `backend/tests/README.md` - Complete testing documentation

**Documentation:**
- [Gmail Fallback Setup](docs/gmail-fallback-setup.md) - OAuth configuration
- [Windows Desktop Setup](docs/windows-desktop-setup.md) - Complete Windows guide
- [Fallback Notifications](FALLBACK_NOTIFICATIONS.md) - Quick reference

**Expected Test Results:**
```
✅ Passed:   7
❌ Failed:   0
⚠️ Warnings: 2 (Gmail OAuth not configured - expected on fresh install)
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

## 🔐 Authentication with Clerk

xALiGN uses [Clerk](https://clerk.com) for secure, production-ready authentication supporting multiple sign-in methods.

### ✅ Status: Ready for Production

All Clerk components and configuration are installed. See [docs/clerk-setup-guide.md](docs/clerk-setup-guide.md) for complete documentation.

### Quick Start

1. **Install dependencies** (if not already done):
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

3. **Test authentication**:
   - Visit http://localhost:3000
   - Click "Sign In" or "Sign Up"
   - Use test email: `admin+clerk_test@xalign.com`
   - Enter verification code: `424242`
   - ✅ You'll be signed in and redirected to `/dashboard`

### Authentication Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/sign-in` | `<SignIn>` | Email/phone sign-in with OTP verification |
| `/sign-up` | `<SignUp>` | New user registration |
| `/dashboard` | Protected | Redirect destination after auth |

### Test Credentials

For development and testing:

- **Test Emails**: `{username}+clerk_test@{domain}` (e.g., `user+clerk_test@example.com`)
- **Test Phones**: `+1 (XXX) 555-0100` to `555-0199` (e.g., `+12015550100`)
- **Verification Code**: `424242` (universal test code)

See [docs/clerk-test-credentials.md](docs/clerk-test-credentials.md) for detailed testing guide.

### Features

- ✅ **Email/Phone Authentication**: OTP verification with test mode support
- ✅ **Protected Routes**: Automatic route protection with `clerkMiddleware()`
- ✅ **Custom JWT Claims**: TypeScript types for user metadata and permissions
- ✅ **Role-Based Access Control**: Custom roles (owner, admin, bid_manager, estimator, viewer)
- ✅ **Organization Support**: Multi-tenant access with team management
- ✅ **MCP Server Integration**: AI context for GitHub Copilot (see [docs/clerk-mcp-server.md](docs/clerk-mcp-server.md))

### Backend Authentication

Backend JWT verification is handled by [backend/services/auth.py](backend/services/auth.py):

```python
from backend.services.auth import get_current_user, require_auth

# Optional auth - returns None if not authenticated
@app.get("/api/v1/protected")
async def route(user: UserClaims | None = Depends(get_current_user)):
    if user:
        print(f"User: {user.sub}, Email: {user.email}")
    
# Required auth - returns 401 if not authenticated
@app.get("/api/v1/admin")
async def admin(user: UserClaims = Depends(require_auth)):
    return {"user_id": user.sub}
```

The backend supports **dual authentication** (Clerk + Auth0) via `AUTH_PROVIDER` environment variable.

### Documentation

- **[Complete Setup Guide](docs/clerk-setup-guide.md)** - Full authentication documentation
- **[Test Credentials](docs/clerk-test-credentials.md)** - Testing patterns and examples
- **[MCP Server Integration](docs/clerk-mcp-server.md)** - AI context for GitHub Copilot

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
