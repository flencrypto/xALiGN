"""CRUD router for Accounts, Contacts, and TriggerSignals + enhanced Website Swoop."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import requests
from bs4 import BeautifulSoup
import json

from backend.database import get_db
from backend.models.account import Account, Contact, TriggerSignal
from backend.schemas.account import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    TriggerSignalCreate,
    TriggerSignalRead,
    TriggerSignalUpdate,
)
from backend.core.config import settings  # XAI_API_KEY lives here

router = APIRouter(prefix="/accounts", tags=["Accounts"])
contacts_router = APIRouter(prefix="/contacts", tags=["Contacts"])
signals_router = APIRouter(prefix="/trigger-signals", tags=["Trigger Signals"])


# ── Website Swoop (NEW – enhanced extraction) ─────────────────────────────────
@router.post("/swoop", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def website_swoop(url: str, db: Session = Depends(get_db)):
    """Crawl any company website → Grok extracts rich intel → auto-creates full Account record."""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Full URL required[](https://...)")

    try:
        # Light crawl
        headers = {"User-Agent": "aLiGN-Bot/1.0"}
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title = (soup.title.string or "").strip()
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        desc = (meta.get("content") or "").strip() if meta else ""

        # ── ENHANCED GROK PROMPT ─────────────────────────────────────────────
        grok_payload = {
            "model": "grok-3-mini",
            "messages": [{
                "role": "user",
                "content": f"""You are an expert DC industry researcher. Crawl this company website and return **ONLY valid JSON** (no extra text).

Required exact schema:
{{
  "company_name": "exact name",
  "type": "Hyperscale Operator | Colocation | Contractor | Sovereign AI | etc",
  "location": "UK / London / Europe / Global etc",
  "website": "{url}",
  "linkedin_company_url": "full LinkedIn company page or null",
  "x_handle": "@handle or null",
  "key_personnel": [
    {{ "name": "...", "role": "...", "linkedin": "full URL or null", "x_handle": "@handle or null", "recent_activity": "one-sentence summary" }}
  ],
  "recent_linkedin_posts": ["post summary 1 with date", "post summary 2 with date"],
  "recent_x_posts": ["post summary 1 with date", "post summary 2 with date"],
  "recent_news": [
    {{ "headline": "...", "date": "YYYY-MM-DD", "source": "...", "url": "..." }}
  ],
  "stock_ticker": "NASDAQ:EQIX or null",
  "current_stock_price": number or null,
  "triggers": ["funding round £1bn", "new UK campus", "NVIDIA deal", ...],
  "intel_summary": "2-3 sentence DC-specific summary (focus on AI/refurb/expansion)",
  "suggested_touchpoint": "short LinkedIn DM or email draft in professional British tone"
}}

Page title: {title}
Meta description: {desc}
Full scraped text: {resp.text[:12000]}

Prioritise DC/AI signals, brownfield refurbs, funding, hires, campus news. Extract real LinkedIn & X links if present."""
            }]
        }

        grok_resp = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.XAI_API_KEY}"},
            json=grok_payload,
            timeout=15
        )
        grok_resp.raise_for_status()
        raw = grok_resp.json()["choices"][0]["message"]["content"]
        intel = json.loads(raw)

        # Create rich Account record
        payload = AccountCreate(
            name=intel["company_name"],
            stage="Target",
            type=intel.get("type", "Operator"),
            location=intel.get("location", "UK"),
            website=intel.get("website"),
            intel_summary=intel.get("intel_summary", ""),
            trigger_signals=intel.get("triggers", []),
            tags=["website-swoop", "AI" if "AI" in intel.get("intel_summary", "") else "active"]
        )

        obj = Account(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Swoop failed: {str(e)}")


# ── Accounts ──────────────────────────────────────────────────────────────────
@router.get("", response_model=list[AccountRead])
def list_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return a paginated list of accounts."""
    return db.query(Account).offset(skip).limit(limit).all()

@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account."""
    obj = Account(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Retrieve a single account by ID."""
    obj = db.get(Account, account_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found")
    return obj

@router.patch("/{account_id}", response_model=AccountRead)
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)):
    """Partially update an account."""
    obj = db.get(Account, account_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete an account."""
    obj = db.get(Account, account_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(obj)
    db.commit()


# ── Contacts ──────────────────────────────────────────────────────────────────
@contacts_router.get("", response_model=list[ContactRead])
def list_contacts(account_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(Contact)
    if account_id is not None:
        q = q.filter(Contact.account_id == account_id)
    return q.offset(skip).limit(limit).all()

@contacts_router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=404, detail="Account not found")
    obj = Contact(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── TriggerSignals ────────────────────────────────────────────────────────────
@signals_router.get("", response_model=list[TriggerSignalRead])
def list_signals(account_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(TriggerSignal)
    if account_id is not None:
        q = q.filter(TriggerSignal.account_id == account_id)
    return q.offset(skip).limit(limit).all()

@signals_router.post("", response_model=TriggerSignalRead, status_code=status.HTTP_201_CREATED)
def create_signal(payload: TriggerSignalCreate, db: Session = Depends(get_db)):
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=404, detail="Account not found")
    obj = TriggerSignal(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
