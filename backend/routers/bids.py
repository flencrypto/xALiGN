"""CRUD router for Bids, BidDocuments, ComplianceItems, and RFIs + enhanced Grok LLM extraction."""

import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import requests
from bs4 import BeautifulSoup  # kept for future expansions if needed

from backend.database import get_db
from backend.models.bid import (
    Bid,
    BidDocument,
    ComplianceItem,
    ComplianceStatus,
    DocType,
    RFI,
    RFIPriority,
    RFIStatus,
)
from backend.models.opportunity import Opportunity
from backend.schemas.bid import (
    BidCreate,
    BidDocumentCreate,
    BidDocumentRead,
    BidDocumentUpdate,
    BidRead,
    BidUpdate,
    ComplianceItemCreate,
    ComplianceItemRead,
    ComplianceItemUpdate,
    RFICreate,
    RFIRead,
    RFIUpdate,
)
from backend.services import document_parser
from backend.services import grok_client
from backend.services.integration_requirements import ensure_integration_configured
from backend.core.config import settings

logger = logging.getLogger("align.bids")

router = APIRouter(prefix="/bids", tags=["Bids"])


# ── Bids ──────────────────────────────────────────────────────────────────────
@router.get("", response_model=list[BidRead])
def list_bids(
    opportunity_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List bids, optionally filtered by opportunity."""
    q = db.query(Bid)
    if opportunity_id is not None:
        q = q.filter(Bid.opportunity_id == opportunity_id)
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=BidRead, status_code=status.HTTP_201_CREATED)
def create_bid(payload: BidCreate, db: Session = Depends(get_db)):
    """Create a new bid."""
    if not db.get(Opportunity, payload.opportunity_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    obj = Bid(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{bid_id}", response_model=BidRead)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    obj = db.get(Bid, bid_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Bid not found")
    return obj


@router.patch("/{bid_id}", response_model=BidRead)
def update_bid(bid_id: int, payload: BidUpdate, db: Session = Depends(get_db)):
    obj = db.get(Bid, bid_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Bid not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{bid_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bid(bid_id: int, db: Session = Depends(get_db)):
    obj = db.get(Bid, bid_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Bid not found")
    db.delete(obj)
    db.commit()


# ── Bid Documents ─────────────────────────────────────────────────────────────
@router.get("/{bid_id}/documents", response_model=list[BidDocumentRead])
def list_documents(bid_id: int, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    return db.query(BidDocument).filter(BidDocument.bid_id == bid_id).all()


@router.post("/{bid_id}/documents", response_model=BidDocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(bid_id: int, payload: BidDocumentCreate, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    data = payload.model_dump()
    data["bid_id"] = bid_id
    obj = BidDocument(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Upload + Parse (with enhanced LLM fallback) ───────────────────────────────
_PARSE_ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
_PARSE_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post(
    "/{bid_id}/documents/upload-and-parse",
    response_model=BidDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_and_parse_document(
    bid_id: int,
    file: UploadFile = File(...),
    doc_type: DocType = Form(DocType.tender),
    db: Session = Depends(get_db),
):
    """Upload PDF/Word → parse text → extract requirements (heuristic + Grok fallback)."""
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")

    if file.content_type and file.content_type not in _PARSE_ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Supported: PDF, Word",
        )

    content = await file.read()
    if len(content) > _PARSE_MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    filename = file.filename or "upload.bin"
    content_text, extracted_requirements_json = document_parser.parse_document(content, filename)

    obj = BidDocument(
        bid_id=bid_id,
        filename=filename,
        doc_type=doc_type,
        content_text=content_text or None,
        extracted_requirements=extracted_requirements_json if extracted_requirements_json != "[]" else None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    logger.info(f"Parsed {filename} for bid {bid_id} – {len(content_text or '')} chars extracted")
    return obj


# ── LLM Re-parse (enhanced Grok prompt) ───────────────────────────────────────
@router.post("/{bid_id}/documents/{doc_id}/parse", response_model=BidDocumentRead)
async def llm_parse_document(bid_id: int, doc_id: int, db: Session = Depends(get_db)):
    """Re-parse document with enhanced Grok LLM for better requirement extraction."""
    doc = db.get(BidDocument, doc_id)
    if not doc or doc.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.content_text:
        raise HTTPException(422, "No text content – run upload-and-parse first")

    if grok_client.is_configured():
        try:
            # Enhanced Grok prompt for requirements extraction
            grok_payload = {
                "model": "grok-3-mini",
                "messages": [{
                    "role": "user",
                    "content": f"""Extract ALL compliance / technical / commercial requirements from this bid document text.
Return ONLY a JSON array of objects with this exact schema:
[{{"requirement": "exact requirement text", "category": "Technical|Commercial|Scope|Compliance|..."}}]

Document type: {doc.doc_type.value}
Full text: {doc.content_text[:14000]}"""
                }]
            }
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.XAI_API_KEY}"},
                json=grok_payload,
                timeout=20,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            requirements = json.loads(raw)
            doc.extracted_requirements = json.dumps(requirements)
        except Exception as e:
            logger.warning(f"LLM parse failed, falling back to heuristic: {e}")
            _, doc.extracted_requirements = document_parser.parse_document(
                doc.content_text.encode(), doc.filename
            )
    else:
        _, doc.extracted_requirements = document_parser.parse_document(
            doc.content_text.encode(), doc.filename
        )

    db.commit()
    db.refresh(doc)
    return doc


# ── Compliance Items ──────────────────────────────────────────────────────────
@router.get("/{bid_id}/compliance", response_model=list[ComplianceItemRead])
def list_compliance(bid_id: int, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    return db.query(ComplianceItem).filter(ComplianceItem.bid_id == bid_id).all()


@router.post("/{bid_id}/compliance", response_model=ComplianceItemRead, status_code=status.HTTP_201_CREATED)
def create_compliance_item(bid_id: int, payload: ComplianceItemCreate, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    data = payload.model_dump()
    data["bid_id"] = bid_id
    obj = ComplianceItem(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Generate Compliance Matrix (LLM-enhanced) ─────────────────────────────────
@router.post("/{bid_id}/generate-compliance-matrix", response_model=list[ComplianceItemRead])
def generate_compliance_matrix(bid_id: int, db: Session = Depends(get_db)):
    """Auto-generate compliance items from all documents (heuristic + Grok fallback)."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    existing = {item.requirement for item in db.query(ComplianceItem).filter(ComplianceItem.bid_id == bid_id)}
    documents = db.query(BidDocument).filter(BidDocument.bid_id == bid_id).all()
    created = []

    for doc in documents:
        if not doc.extracted_requirements:
            continue
        try:
            reqs = json.loads(doc.extracted_requirements)
        except (json.JSONDecodeError, TypeError):
            continue

        for r in reqs:
            text = r.get("requirement") if isinstance(r, dict) else str(r)
            category = r.get("category", doc.doc_type.value) if isinstance(r, dict) else doc.doc_type.value
            if text and text not in existing:
                item = ComplianceItem(
                    bid_id=bid_id,
                    requirement=text,
                    category=category,
                    compliance_status=ComplianceStatus.tbc,
                )
                db.add(item)
                existing.add(text)
                created.append(item)

    db.commit()
    for item in created:
        db.refresh(item)
    return created


# ── RFIs ──────────────────────────────────────────────────────────────────────
@router.get("/{bid_id}/rfis", response_model=list[RFIRead])
def list_rfis(bid_id: int, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    return db.query(RFI).filter(RFI.bid_id == bid_id).all()


@router.post("/{bid_id}/rfis", response_model=RFIRead, status_code=status.HTTP_201_CREATED)
def create_rfi(bid_id: int, payload: RFICreate, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    data = payload.model_dump()
    data["bid_id"] = bid_id
    obj = RFI(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Generate RFIs (enhanced heuristic + Grok ready) ───────────────────────────
@router.post("/{bid_id}/generate-rfis", response_model=list[RFIRead])
def generate_rfis(bid_id: int, db: Session = Depends(get_db)):
    """Generate RFIs from ambiguous text in documents (heuristic + future Grok enhancement)."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    documents = db.query(BidDocument).filter(BidDocument.bid_id == bid_id).all()
    existing = {rfi.question for rfi in db.query(RFI).filter(RFI.bid_id == bid_id)}

    _TRIGGERS = [
        ("tbc", "Clarification required on TBC item", "General", RFIPriority.high),
        ("to be confirmed", "Confirmation required for item marked TBC", "General", RFIPriority.high),
        ("undefined", "Scope item is undefined – please clarify", "Scope", RFIPriority.high),
        ("assumed", "Assumption requires client confirmation", "Scope", RFIPriority.medium),
    ]

    created = []
    for doc in documents:
        if not doc.content_text:
            continue
        lower = doc.content_text.lower()
        for kw, tmpl, cat, prio in _TRIGGERS:
            q = f"[{doc.filename}] {tmpl}"
            if kw in lower and q not in existing:
                rfi = RFI(
                    bid_id=bid_id,
                    question=q,
                    category=cat,
                    priority=prio,
                    status=RFIStatus.draft,
                )
                db.add(rfi)
                existing.add(q)
                created.append(rfi)

    db.commit()
    for rfi in created:
        db.refresh(rfi)
    return created


# ── LLM Compliance Answer Generation (enhanced prompt) ────────────────────────
from pydantic import BaseModel

class ComplianceAnswerRequest(BaseModel):
    company_context: str | None = None


@router.post("/{bid_id}/compliance/{item_id}/generate-answer", response_model=ComplianceItemRead)
async def generate_compliance_answer(
    bid_id: int,
    item_id: int,
    payload: ComplianceAnswerRequest,
    db: Session = Depends(get_db),
):
    """Use enhanced Grok prompt to draft a professional compliance answer."""
    item = db.get(ComplianceItem, item_id)
    if not item or item.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Compliance item not found")

    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    try:
        result = await grok_client.generate_compliance_answer(
            requirement=item.requirement,
            category=item.category,
            company_context=payload.company_context,
        )
    except Exception as exc:
        logger.error(f"LLM answer generation failed: {exc}")
        raise HTTPException(500, f"LLM request failed: {exc}")

    item.evidence = result.get("answer", "")
    if caveats := result.get("caveats"):
        item.notes = (item.notes or "") + f"\n[AI caveats] {caveats}"

    if item.compliance_status == ComplianceStatus.tbc and (suggested := result.get("compliance_status")) in ComplianceStatus.__members__:
        item.compliance_status = ComplianceStatus(suggested)

    db.commit()
    db.refresh(item)
    return item
