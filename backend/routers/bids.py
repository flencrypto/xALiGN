"""CRUD router for Bids, BidDocuments, ComplianceItems, and RFIs."""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

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


# ── Documents ─────────────────────────────────────────────────────────────────

@router.get("/{bid_id}/documents", response_model=list[BidDocumentRead])
def list_documents(bid_id: int, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    return db.query(BidDocument).filter(BidDocument.bid_id == bid_id).all()


@router.post(
    "/{bid_id}/documents", response_model=BidDocumentRead, status_code=status.HTTP_201_CREATED
)
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


@router.patch("/{bid_id}/documents/{doc_id}", response_model=BidDocumentRead)
def update_document(
    bid_id: int, doc_id: int, payload: BidDocumentUpdate, db: Session = Depends(get_db)
):
    obj = db.get(BidDocument, doc_id)
    if not obj or obj.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Document not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{bid_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(bid_id: int, doc_id: int, db: Session = Depends(get_db)):
    obj = db.get(BidDocument, doc_id)
    if not obj or obj.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(obj)
    db.commit()


# ── Compliance Items ──────────────────────────────────────────────────────────

@router.get("/{bid_id}/compliance", response_model=list[ComplianceItemRead])
def list_compliance(bid_id: int, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    return db.query(ComplianceItem).filter(ComplianceItem.bid_id == bid_id).all()


@router.post(
    "/{bid_id}/compliance",
    response_model=ComplianceItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_compliance_item(
    bid_id: int, payload: ComplianceItemCreate, db: Session = Depends(get_db)
):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    data = payload.model_dump()
    data["bid_id"] = bid_id
    obj = ComplianceItem(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{bid_id}/compliance/{item_id}", response_model=ComplianceItemRead)
def update_compliance_item(
    bid_id: int, item_id: int, payload: ComplianceItemUpdate, db: Session = Depends(get_db)
):
    obj = db.get(ComplianceItem, item_id)
    if not obj or obj.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{bid_id}/compliance/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_compliance_item(bid_id: int, item_id: int, db: Session = Depends(get_db)):
    obj = db.get(ComplianceItem, item_id)
    if not obj or obj.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    db.delete(obj)
    db.commit()


# ── Generate Compliance Matrix ────────────────────────────────────────────────

@router.post(
    "/{bid_id}/generate-compliance-matrix",
    response_model=list[ComplianceItemRead],
    status_code=status.HTTP_201_CREATED,
)
def generate_compliance_matrix(bid_id: int, db: Session = Depends(get_db)):
    """
    Parse extracted requirements from all bid documents and create ComplianceItems.

    Each item in the extracted_requirements JSON array becomes a compliance row
    with status 'tbc'. Items are deduplicated against existing requirements.
    """
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    existing_reqs = {
        item.requirement
        for item in db.query(ComplianceItem).filter(ComplianceItem.bid_id == bid_id).all()
    }

    documents = db.query(BidDocument).filter(BidDocument.bid_id == bid_id).all()
    created: list[ComplianceItem] = []

    for doc in documents:
        if not doc.extracted_requirements:
            continue
        try:
            requirements: list[dict] = json.loads(doc.extracted_requirements)
        except (json.JSONDecodeError, TypeError):
            continue

        for req_entry in requirements:
            if isinstance(req_entry, str):
                req_text, category = req_entry, doc.doc_type.value
            elif isinstance(req_entry, dict):
                req_text = req_entry.get("requirement", "")
                category = req_entry.get("category", doc.doc_type.value)
            else:
                continue

            if not req_text or req_text in existing_reqs:
                continue

            item = ComplianceItem(
                bid_id=bid_id,
                requirement=req_text,
                category=category,
                compliance_status=ComplianceStatus.tbc,
            )
            db.add(item)
            existing_reqs.add(req_text)
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


@router.patch("/{bid_id}/rfis/{rfi_id}", response_model=RFIRead)
def update_rfi(bid_id: int, rfi_id: int, payload: RFIUpdate, db: Session = Depends(get_db)):
    obj = db.get(RFI, rfi_id)
    if not obj or obj.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="RFI not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{bid_id}/rfis/{rfi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rfi(bid_id: int, rfi_id: int, db: Session = Depends(get_db)):
    obj = db.get(RFI, rfi_id)
    if not obj or obj.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="RFI not found")
    db.delete(obj)
    db.commit()


# ── Generate RFIs from Documents ──────────────────────────────────────────────

@router.post(
    "/{bid_id}/generate-rfis",
    response_model=list[RFIRead],
    status_code=status.HTTP_201_CREATED,
)
def generate_rfis(bid_id: int, db: Session = Depends(get_db)):
    """
    Scan bid documents for ambiguous or missing information and generate RFI items.

    Keywords in document text trigger RFI creation; already-raised questions are
    deduplicated. In production this would integrate with an LLM to extract
    meaningful clarification questions.
    """
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    documents = db.query(BidDocument).filter(BidDocument.bid_id == bid_id).all()

    # Heuristic keyword → RFI templates
    _TRIGGERS: list[tuple[str, str, str, RFIPriority]] = [
        ("tbc", "Clarification required on TBC item", "General", RFIPriority.high),
        ("to be confirmed", "Confirmation required for item marked TBC", "General", RFIPriority.high),
        ("undefined", "Scope item is undefined – please clarify", "Scope", RFIPriority.high),
        ("assumed", "Assumption requires client confirmation", "Scope", RFIPriority.medium),
        ("n/a", "N/A response – please confirm applicability", "Compliance", RFIPriority.low),
        ("provisional", "Provisional sum needs clarification", "Commercial", RFIPriority.medium),
    ]

    existing_questions = {
        rfi.question
        for rfi in db.query(RFI).filter(RFI.bid_id == bid_id).all()
    }
    created: list[RFI] = []

    for doc in documents:
        if not doc.content_text:
            continue
        lower_text = doc.content_text.lower()
        for keyword, question_tmpl, category, priority in _TRIGGERS:
            question = f"[{doc.filename}] {question_tmpl}"
            if keyword in lower_text and question not in existing_questions:
                rfi = RFI(
                    bid_id=bid_id,
                    question=question,
                    category=category,
                    priority=priority,
                    status=RFIStatus.draft,
                )
                db.add(rfi)
                existing_questions.add(question)
                created.append(rfi)

    db.commit()
    for rfi in created:
        db.refresh(rfi)
    return created


# ── Document upload + parsing ─────────────────────────────────────────────────

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
    summary="Upload a PDF or Word document and extract requirements",
)
async def upload_and_parse_document(
    bid_id: int,
    file: UploadFile = File(...),
    doc_type: DocType = Form(DocType.tender),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF or Word (.docx) document, parse its text, and extract
    compliance requirements using heuristic NLP.

    The parsed ``content_text`` and ``extracted_requirements`` (JSON list) are
    stored on the resulting BidDocument record and can be used to auto-generate
    a compliance matrix.
    """
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")

    if file.content_type and file.content_type not in _PARSE_ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Supported: PDF, Word (.docx)",
        )

    content = await file.read()
    if len(content) > _PARSE_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum of {_PARSE_MAX_BYTES // (1024*1024)} MB",
        )

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
    logger.info("Parsed document %s for bid %d – extracted %s bytes of text", filename, bid_id, len(content_text))
    return obj


@router.post(
    "/{bid_id}/documents/{doc_id}/parse",
    response_model=BidDocumentRead,
    summary="Re-parse an existing document using LLM-enhanced extraction",
)
async def llm_parse_document(bid_id: int, doc_id: int, db: Session = Depends(get_db)):
    """
    Run LLM-enhanced requirement extraction on a previously uploaded document.

    Requires XAI_API_KEY. Falls back to heuristic extraction if not configured.
    Updates the document's ``extracted_requirements`` in-place.
    """
    doc = db.get(BidDocument, doc_id)
    if not doc or doc.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.content_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document has no parsed text. Upload via upload-and-parse first.",
        )

    if grok_client.is_configured():
        try:
            reqs = await grok_client.parse_document_requirements(
                doc.content_text, doc.doc_type.value
            )
            doc.extracted_requirements = json.dumps(reqs)
        except Exception as exc:
            logger.warning("LLM parse failed, falling back to heuristic: %s", exc)
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


# ── LLM Compliance Answer Generation ─────────────────────────────────────────

from pydantic import BaseModel


class ComplianceAnswerRequest(BaseModel):
    company_context: str | None = None


@router.post(
    "/{bid_id}/compliance/{item_id}/generate-answer",
    response_model=ComplianceItemRead,
    summary="Use LLM to draft a compliance answer for a requirement",
)
async def generate_compliance_answer(
    bid_id: int,
    item_id: int,
    payload: ComplianceAnswerRequest,
    db: Session = Depends(get_db),
):
    """
    Use Grok to draft a compliance answer for the specified compliance item.

    The generated answer is stored in the ``evidence`` field and the suggested
    ``compliance_status`` is applied if the current status is 'tbc'.

    Requires XAI_API_KEY to be configured.
    """
    item = db.get(ComplianceItem, item_id)
    if not item or item.bid_id != bid_id:
        raise HTTPException(status_code=404, detail="Compliance item not found")

    if not grok_client.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="XAI_API_KEY is not configured. LLM compliance answers are unavailable.",
        )

    try:
        result = await grok_client.generate_compliance_answer(
            requirement=item.requirement,
            category=item.category,
            company_context=payload.company_context,
        )
    except Exception as exc:
        logger.error("LLM compliance answer generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"LLM request failed: {exc}")

    item.evidence = result.get("answer", "")
    caveats = result.get("caveats", "")
    if caveats:
        item.notes = (item.notes or "") + (f"\n[AI caveats] {caveats}").strip()

    suggested_status = result.get("compliance_status", "")
    if item.compliance_status == ComplianceStatus.tbc and suggested_status in ComplianceStatus.__members__:
        item.compliance_status = ComplianceStatus(suggested_status)

    db.commit()
    db.refresh(item)
    return item
