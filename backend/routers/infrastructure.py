"""Infrastructure Intelligence router.

Endpoints
---------
POST  /api/v1/intelligence/import                – Ingest a project from Grok / webhook
GET   /api/v1/intelligence/projects              – List all projects
POST  /api/v1/intelligence/projects              – Create a project manually
GET   /api/v1/intelligence/projects/{id}         – Get a project (with signals)
PUT   /api/v1/intelligence/projects/{id}         – Update a project
DELETE /api/v1/intelligence/projects/{id}        – Delete a project

GET   /api/v1/intelligence/companies             – List DC companies
POST  /api/v1/intelligence/companies             – Create a DC company
GET   /api/v1/intelligence/companies/{id}        – Get a DC company
PUT   /api/v1/intelligence/companies/{id}        – Update a DC company
DELETE /api/v1/intelligence/companies/{id}       – Delete a DC company

GET   /api/v1/intelligence/signals               – List opportunity signals
POST  /api/v1/intelligence/signals               – Create a signal
PUT   /api/v1/intelligence/signals/{id}          – Update a signal
DELETE /api/v1/intelligence/signals/{id}         – Delete a signal

GET   /api/v1/intelligence/leaderboard           – Expansion leaderboard
GET   /api/v1/intelligence/contractor-activity   – Contractor activity tracker
GET   /api/v1/intelligence/momentum              – Infrastructure Momentum Scores
"""

import json
import logging
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.infrastructure import (
    DCCompany,
    InfrastructureProject,
    OpportunitySignal,
    ProjectStage,
)
from backend.schemas.infrastructure import (
    ContractorEntry,
    DCCompanyCreate,
    DCCompanyRead,
    DCCompanyUpdate,
    IntelligenceImportPayload,
    InfrastructureProjectCreate,
    InfrastructureProjectRead,
    InfrastructureProjectSummary,
    InfrastructureProjectUpdate,
    LeaderboardEntry,
    MomentumEntry,
    OpportunitySignalCreate,
    OpportunitySignalRead,
    OpportunitySignalUpdate,
)

logger = logging.getLogger("align.infrastructure")

router = APIRouter(prefix="/intelligence", tags=["Infrastructure Intelligence"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _partners_to_str(partners: list[str]) -> str | None:
    """Encode a list of partner names as a JSON string for storage."""
    if not partners:
        return None
    return json.dumps(partners)


def _str_to_partners(raw: str | None) -> list[str]:
    """Decode a JSON-encoded partner list; return empty list on failure."""
    if not raw:
        return []
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _project_read(obj: InfrastructureProject) -> dict:
    """Convert an ORM object to a dict suitable for InfrastructureProjectRead."""
    data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    data["partners"] = _str_to_partners(obj.partners)
    data["opportunity_signals"] = obj.opportunity_signals
    return data


def _get_project_or_404(project_id: int, db: Session) -> InfrastructureProject:
    obj = db.get(InfrastructureProject, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Project not found")
    return obj


# ── Import (Grok webhook) ─────────────────────────────────────────────────────

@router.post(
    "/import",
    response_model=InfrastructureProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a project from a Grok task / webhook",
)
def import_project(payload: IntelligenceImportPayload, db: Session = Depends(get_db)):
    """
    Accepts a structured payload from a Grok daily task or any external
    webhook and upserts (create or update) the infrastructure project record.

    **Deduplication logic**: if a record with the same `project_name`,
    `location_country` and `company` already exists, it is updated rather
    than duplicated.
    """
    # Resolve location fields from free-text 'location' when explicit fields omitted
    location_country = payload.location_country
    location_city    = payload.location_city
    region           = payload.region
    if payload.location and not location_country:
        # Simple heuristic: use the last comma-separated token as country
        parts = [p.strip() for p in payload.location.split(",") if p.strip()]
        if parts:
            location_country = parts[-1]
        if len(parts) > 1:
            location_city = parts[0]

    # Deduplication check
    existing = (
        db.query(InfrastructureProject)
        .filter(
            InfrastructureProject.project_name == payload.project,
            InfrastructureProject.company == payload.company,
        )
        .first()
    )

    if existing:
        # Update existing record with the new data
        existing.location_city    = location_city    or existing.location_city
        existing.location_country = location_country or existing.location_country
        existing.region           = region           or existing.region
        existing.project_type     = payload.project_type or existing.project_type
        existing.industry_segment = payload.industry_segment
        if payload.investment_value is not None:
            existing.investment_value = payload.investment_value
        if payload.capacity_mw is not None:
            existing.capacity_mw = payload.capacity_mw
        existing.project_stage    = payload.stage
        if payload.partners:
            existing.partners = _partners_to_str(payload.partners)
        existing.date_announced   = payload.date_announced or existing.date_announced
        existing.source           = payload.source or existing.source
        existing.confidence_level = payload.confidence
        existing.summary          = payload.summary or existing.summary
        db.commit()
        db.refresh(existing)
        logger.info("Infrastructure: updated existing project id=%d '%s'", existing.id, existing.project_name)
        return InfrastructureProjectRead.model_validate(_project_read(existing))

    # Create new record
    obj = InfrastructureProject(
        company          = payload.company,
        project_name     = payload.project,
        location_city    = location_city,
        location_country = location_country,
        region           = region,
        project_type     = payload.project_type,
        industry_segment = payload.industry_segment,
        investment_value = payload.investment_value,
        capacity_mw      = payload.capacity_mw,
        project_stage    = payload.stage,
        partners         = _partners_to_str(payload.partners),
        date_announced   = payload.date_announced,
        source           = payload.source,
        confidence_level = payload.confidence,
        summary          = payload.summary,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    logger.info("Infrastructure: created project id=%d '%s'", obj.id, obj.project_name)
    return InfrastructureProjectRead.model_validate(_project_read(obj))


# ── Projects CRUD ─────────────────────────────────────────────────────────────

@router.get(
    "/projects",
    response_model=list[InfrastructureProjectSummary],
    summary="List infrastructure projects",
)
def list_projects(
    stage: str | None = None,
    region: str | None = None,
    industry_segment: str | None = None,
    company: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return a paginated, filterable list of infrastructure projects."""
    q = db.query(InfrastructureProject).order_by(InfrastructureProject.created_at.desc())
    if stage:
        q = q.filter(InfrastructureProject.project_stage == stage)
    if region:
        q = q.filter(InfrastructureProject.region.ilike(f"%{region}%"))
    if industry_segment:
        q = q.filter(InfrastructureProject.industry_segment == industry_segment)
    if company:
        q = q.filter(InfrastructureProject.company.ilike(f"%{company}%"))
    rows = q.offset(skip).limit(limit).all()
    return [InfrastructureProjectSummary.model_validate(r) for r in rows]


@router.post(
    "/projects",
    response_model=InfrastructureProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an infrastructure project",
)
def create_project(payload: InfrastructureProjectCreate, db: Session = Depends(get_db)):
    obj = InfrastructureProject(
        **{k: v for k, v in payload.model_dump().items() if k != "partners"},
        partners=_partners_to_str(payload.partners),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return InfrastructureProjectRead.model_validate(_project_read(obj))


@router.get(
    "/projects/{project_id}",
    response_model=InfrastructureProjectRead,
    summary="Get an infrastructure project with its signals",
)
def get_project(project_id: int, db: Session = Depends(get_db)):
    obj = _get_project_or_404(project_id, db)
    return InfrastructureProjectRead.model_validate(_project_read(obj))


@router.put(
    "/projects/{project_id}",
    response_model=InfrastructureProjectRead,
    summary="Update an infrastructure project",
)
def update_project(
    project_id: int,
    payload: InfrastructureProjectUpdate,
    db: Session = Depends(get_db),
):
    obj = _get_project_or_404(project_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    if "partners" in update_data:
        update_data["partners"] = _partners_to_str(update_data["partners"] or [])
    for field, value in update_data.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return InfrastructureProjectRead.model_validate(_project_read(obj))


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an infrastructure project",
)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    obj = _get_project_or_404(project_id, db)
    db.delete(obj)
    db.commit()


# ── DC Companies CRUD ─────────────────────────────────────────────────────────

@router.get(
    "/companies",
    response_model=list[DCCompanyRead],
    summary="List DC companies",
)
def list_dc_companies(
    category: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(DCCompany).order_by(DCCompany.company_name)
    if category:
        q = q.filter(DCCompany.category == category)
    return q.offset(skip).limit(limit).all()


@router.post(
    "/companies",
    response_model=DCCompanyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a DC company",
)
def create_dc_company(payload: DCCompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(DCCompany).filter(DCCompany.company_name == payload.company_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Company '{payload.company_name}' already exists (id={existing.id})",
        )
    obj = DCCompany(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/companies/{company_id}",
    response_model=DCCompanyRead,
    summary="Get a DC company",
)
def get_dc_company(company_id: int, db: Session = Depends(get_db)):
    obj = db.get(DCCompany, company_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Company not found")
    return obj


@router.put(
    "/companies/{company_id}",
    response_model=DCCompanyRead,
    summary="Update a DC company",
)
def update_dc_company(
    company_id: int,
    payload: DCCompanyUpdate,
    db: Session = Depends(get_db),
):
    obj = db.get(DCCompany, company_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/companies/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a DC company",
)
def delete_dc_company(company_id: int, db: Session = Depends(get_db)):
    obj = db.get(DCCompany, company_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(obj)
    db.commit()


# ── Opportunity Signals CRUD ──────────────────────────────────────────────────

@router.get(
    "/signals",
    response_model=list[OpportunitySignalRead],
    summary="List opportunity signals",
)
def list_signals(
    project_id: int | None = None,
    likelihood: str | None = None,
    signal_type: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(OpportunitySignal).order_by(OpportunitySignal.created_at.desc())
    if project_id is not None:
        q = q.filter(OpportunitySignal.project_id == project_id)
    if likelihood:
        q = q.filter(OpportunitySignal.likelihood == likelihood)
    if signal_type:
        q = q.filter(OpportunitySignal.signal_type == signal_type)
    return q.offset(skip).limit(limit).all()


@router.post(
    "/signals",
    response_model=OpportunitySignalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an opportunity signal",
)
def create_signal(payload: OpportunitySignalCreate, db: Session = Depends(get_db)):
    _get_project_or_404(payload.project_id, db)
    obj = OpportunitySignal(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put(
    "/signals/{signal_id}",
    response_model=OpportunitySignalRead,
    summary="Update an opportunity signal",
)
def update_signal(
    signal_id: int,
    payload: OpportunitySignalUpdate,
    db: Session = Depends(get_db),
):
    obj = db.get(OpportunitySignal, signal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Signal not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/signals/{signal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an opportunity signal",
)
def delete_signal(signal_id: int, db: Session = Depends(get_db)):
    obj = db.get(OpportunitySignal, signal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Signal not found")
    db.delete(obj)
    db.commit()


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get(
    "/leaderboard",
    response_model=list[LeaderboardEntry],
    summary="Expansion leaderboard – companies ranked by MW under development",
)
def expansion_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns companies ranked by total MW of projects in active development
    stages (announced, planning, permitted, construction).
    """
    active_stages = [
        ProjectStage.announced,
        ProjectStage.planning,
        ProjectStage.permitted,
        ProjectStage.construction,
    ]
    rows = (
        db.query(
            InfrastructureProject.company,
            sa_func.count(InfrastructureProject.id).label("project_count"),
            sa_func.sum(InfrastructureProject.capacity_mw).label("total_mw"),
            sa_func.sum(InfrastructureProject.investment_value).label("total_investment"),
        )
        .filter(InfrastructureProject.project_stage.in_(active_stages))
        .group_by(InfrastructureProject.company)
        .order_by(sa_func.sum(InfrastructureProject.capacity_mw).desc().nulls_last())
        .limit(limit)
        .all()
    )
    return [
        LeaderboardEntry(
            company=r.company,
            project_count=r.project_count,
            total_mw=float(r.total_mw) if r.total_mw is not None else None,
            total_investment=float(r.total_investment) if r.total_investment is not None else None,
        )
        for r in rows
    ]


@router.get(
    "/contractor-activity",
    response_model=list[ContractorEntry],
    summary="Contractor activity tracker – frequency of contractor appearances",
)
def contractor_activity(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Parses the JSON-encoded partners field from every project and counts
    how many distinct projects each contractor/partner appears in.
    """
    rows = db.query(InfrastructureProject.partners).filter(
        InfrastructureProject.partners.isnot(None)
    ).all()

    counts: dict[str, int] = defaultdict(int)
    for (raw,) in rows:
        for partner in _str_to_partners(raw):
            if partner:
                counts[partner.strip()] += 1

    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [ContractorEntry(contractor=name, project_count=cnt) for name, cnt in ranked]


@router.get(
    "/momentum",
    response_model=list[MomentumEntry],
    summary="Infrastructure Momentum Score by region",
)
def infrastructure_momentum(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Calculates a composite momentum score per region based on:

    - Number of projects (weight 2)
    - Total MW capacity (normalised, weight 3)
    - Total investment value (normalised, weight 3)
    - Hyperscaler involvement ratio (weight 2)

    Scores are normalised to a 0–10 scale.
    """
    rows = (
        db.query(
            InfrastructureProject.region,
            sa_func.count(InfrastructureProject.id).label("project_count"),
            sa_func.sum(InfrastructureProject.capacity_mw).label("total_mw"),
            sa_func.sum(InfrastructureProject.investment_value).label("total_investment"),
            sa_func.sum(
                case(
                    (InfrastructureProject.industry_segment == "hyperscaler", 1),
                    else_=0,
                )
            ).label("hyperscaler_count"),
        )
        .filter(InfrastructureProject.region.isnot(None))
        .group_by(InfrastructureProject.region)
        .all()
    )

    if not rows:
        return []

    # Extract raw values for normalisation
    project_counts   = [r.project_count          for r in rows]
    mw_values        = [float(r.total_mw or 0)   for r in rows]
    invest_values    = [float(r.total_investment or 0) for r in rows]

    max_projects = max(project_counts) or 1
    max_mw       = max(mw_values)      or 1
    max_invest   = max(invest_values)  or 1

    entries = []
    for r in rows:
        pc     = r.project_count
        mw     = float(r.total_mw or 0)
        invest = float(r.total_investment or 0)
        hsc    = int(r.hyperscaler_count or 0)

        norm_projects = (pc     / max_projects) * 10
        norm_mw       = (mw     / max_mw)       * 10
        norm_invest   = (invest / max_invest)    * 10
        norm_hyper    = min((hsc / pc) * 10, 10) if pc else 0

        score = round(
            (norm_projects * 2 + norm_mw * 3 + norm_invest * 3 + norm_hyper * 2) / 10,
            1,
        )
        entries.append(
            MomentumEntry(
                region=r.region,
                score=score,
                project_count=pc,
                total_mw=mw if mw else None,
                total_investment=invest if invest else None,
            )
        )

    entries.sort(key=lambda e: e.score, reverse=True)
    return entries[:limit]
