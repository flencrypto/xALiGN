"""CRUD router for Accounts, Contacts, and TriggerSignals."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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

router = APIRouter(prefix="/accounts", tags=["Accounts"])
contacts_router = APIRouter(prefix="/contacts", tags=["Contacts"])
signals_router = APIRouter(prefix="/trigger-signals", tags=["Trigger Signals"])


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
