"""Intelligence Database Layer – CRUD API for BATCH 3 intelligence database."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.projects import (
    CompanyCategory,
    CompanyProfile,
    InfrastructureProject,
    OpportunitySignal,
    OpportunityType,
    ProjectStage,
    ProjectType,
)

logger = logging.getLogger("align.projects")
router = APIRouter(prefix="/projects", tags=["Intelligence Database"])


# ── Infrastructure Projects ───────────────────────────────────────────────────

@router.get("/", summary="List infrastructure projects")
def list_projects(
    stage: str | None = None,
    project_type: str | None = None,
    company: str | None = None,
    has_mw: bool | None = None,
    is_duplicate: bool = False,
    limit: int = Query(50, le=200),
    skip: int = 0,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all infrastructure projects with optional filters."""
    q = db.query(InfrastructureProject).filter(
        InfrastructureProject.is_duplicate == is_duplicate
    )
    if stage:
        q = q.filter(InfrastructureProject.stage == stage)
    if project_type:
        q = q.filter(InfrastructureProject.project_type == project_type)
    if company:
        q = q.filter(InfrastructureProject.company.ilike(f"%{company}%"))
    if has_mw is True:
        q = q.filter(InfrastructureProject.capacity_mw.isnot(None))
    projects = q.order_by(InfrastructureProject.detected_at.desc()).offset(skip).limit(limit).all()
    return [_project_to_dict(p) for p in projects]


@router.post("/", summary="Create infrastructure project", status_code=201)
def create_project(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a new infrastructure project record."""
    project = InfrastructureProject(**{
        k: v for k, v in payload.items()
        if hasattr(InfrastructureProject, k)
    })
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.get("/stats/summary", summary="Aggregate project statistics")
def project_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return aggregate statistics for capacity dashboard and capex tracker."""
    from sqlalchemy import desc

    total = db.query(func.count(InfrastructureProject.id)).scalar() or 0
    total_mw = db.query(func.sum(InfrastructureProject.capacity_mw)).scalar() or 0
    total_capex = db.query(func.sum(InfrastructureProject.capex_millions)).scalar() or 0

    by_stage = {}
    for stage in ProjectStage:
        count = db.query(func.count(InfrastructureProject.id)).filter(
            InfrastructureProject.stage == stage
        ).scalar() or 0
        by_stage[stage.value] = count

    by_type = {}
    for ptype in ProjectType:
        count = db.query(func.count(InfrastructureProject.id)).filter(
            InfrastructureProject.project_type == ptype
        ).scalar() or 0
        by_type[ptype.value] = count

    top_companies = (
        db.query(
            InfrastructureProject.company,
            func.sum(InfrastructureProject.capacity_mw).label("total_mw"),
        )
        .filter(InfrastructureProject.company.isnot(None))
        .group_by(InfrastructureProject.company)
        .order_by(desc("total_mw"))
        .limit(10)
        .all()
    )

    return {
        "total_projects": total,
        "total_capacity_mw": round(float(total_mw), 1),
        "total_capex_millions": round(float(total_capex), 1),
        "by_stage": by_stage,
        "by_type": by_type,
        "top_companies_by_mw": [
            {"company": r.company, "total_mw": round(float(r.total_mw or 0), 1)}
            for r in top_companies
        ],
    }


@router.get("/geo/map-data", summary="Return geolocation data for map")
def get_map_data(
    stage: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return projects with lat/lon for map visualisation."""
    q = db.query(InfrastructureProject).filter(
        InfrastructureProject.latitude.isnot(None),
        InfrastructureProject.longitude.isnot(None),
        InfrastructureProject.is_duplicate.is_(False),
    )
    if stage:
        q = q.filter(InfrastructureProject.stage == stage)
    projects = q.limit(500).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "company": p.company,
            "location": p.location,
            "lat": p.latitude,
            "lon": p.longitude,
            "capacity_mw": p.capacity_mw,
            "capex_millions": p.capex_millions,
            "stage": p.stage.value if p.stage else None,
            "project_type": p.project_type.value if p.project_type else None,
        }
        for p in projects
    ]


@router.get("/geo/heatmap", summary="Return regional aggregation for heatmap")
def get_heatmap_data(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return aggregated project counts by location for heatmap display."""
    from sqlalchemy import desc

    results = (
        db.query(
            InfrastructureProject.location,
            func.count(InfrastructureProject.id).label("project_count"),
            func.sum(InfrastructureProject.capacity_mw).label("total_mw"),
            func.sum(InfrastructureProject.capex_millions).label("total_capex"),
            func.avg(InfrastructureProject.latitude).label("avg_lat"),
            func.avg(InfrastructureProject.longitude).label("avg_lon"),
        )
        .filter(InfrastructureProject.location.isnot(None))
        .filter(InfrastructureProject.is_duplicate.is_(False))
        .group_by(InfrastructureProject.location)
        .order_by(desc("project_count"))
        .limit(100)
        .all()
    )
    return [
        {
            "location": r.location,
            "project_count": r.project_count,
            "total_mw": round(float(r.total_mw or 0), 1),
            "total_capex": round(float(r.total_capex or 0), 1),
            "lat": float(r.avg_lat) if r.avg_lat else None,
            "lon": float(r.avg_lon) if r.avg_lon else None,
        }
        for r in results
    ]


@router.get("/{project_id}", summary="Get infrastructure project by ID")
def get_project(project_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.query(InfrastructureProject).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_dict(project)


@router.patch("/{project_id}", summary="Update infrastructure project")
def update_project(
    project_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    project = db.query(InfrastructureProject).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in payload.items():
        if hasattr(project, key) and key not in ("id", "detected_at"):
            setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.delete("/{project_id}", summary="Delete infrastructure project", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    project = db.query(InfrastructureProject).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


# ── Company Profiles ──────────────────────────────────────────────────────────

@router.get("/companies/", summary="List company profiles")
def list_company_profiles(
    category: str | None = None,
    limit: int = Query(50, le=200),
    skip: int = 0,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    q = db.query(CompanyProfile)
    if category:
        q = q.filter(CompanyProfile.category == category)
    companies = q.order_by(CompanyProfile.name).offset(skip).limit(limit).all()
    return [_company_to_dict(c) for c in companies]


@router.post("/companies/", summary="Create company profile", status_code=201)
def create_company_profile(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    company = CompanyProfile(**{
        k: v for k, v in payload.items()
        if hasattr(CompanyProfile, k)
    })
    db.add(company)
    db.commit()
    db.refresh(company)
    return _company_to_dict(company)


@router.get("/companies/{company_id}", summary="Get company profile by ID")
def get_company_profile(company_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    company = db.query(CompanyProfile).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return _company_to_dict(company)


@router.patch("/companies/{company_id}", summary="Update company profile")
def update_company_profile(
    company_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    company = db.query(CompanyProfile).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    for key, value in payload.items():
        if hasattr(company, key) and key not in ("id", "created_at"):
            setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return _company_to_dict(company)


@router.delete("/companies/{company_id}", summary="Delete company profile", status_code=204)
def delete_company_profile(company_id: int, db: Session = Depends(get_db)) -> None:
    company = db.query(CompanyProfile).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    db.delete(company)
    db.commit()


# ── Opportunity Signals ────────────────────────────────────────────────────────

@router.get("/opportunities/", summary="List opportunity signals")
def list_opportunity_signals(
    opportunity_type: str | None = None,
    is_actioned: bool | None = None,
    limit: int = Query(50, le=200),
    skip: int = 0,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    q = db.query(OpportunitySignal)
    if opportunity_type:
        q = q.filter(OpportunitySignal.opportunity_type == opportunity_type)
    if is_actioned is not None:
        q = q.filter(OpportunitySignal.is_actioned == is_actioned)
    signals = q.order_by(OpportunitySignal.detected_at.desc()).offset(skip).limit(limit).all()
    return [_signal_to_dict(s) for s in signals]


@router.post("/opportunities/", summary="Create opportunity signal", status_code=201)
def create_opportunity_signal(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    signal = OpportunitySignal(**{
        k: v for k, v in payload.items()
        if hasattr(OpportunitySignal, k)
    })
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return _signal_to_dict(signal)


@router.get("/opportunities/{signal_id}", summary="Get opportunity signal by ID")
def get_opportunity_signal(signal_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    signal = db.query(OpportunitySignal).get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Opportunity signal not found")
    return _signal_to_dict(signal)


@router.patch("/opportunities/{signal_id}", summary="Update opportunity signal")
def update_opportunity_signal(
    signal_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    signal = db.query(OpportunitySignal).get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Opportunity signal not found")
    for key, value in payload.items():
        if hasattr(signal, key) and key not in ("id", "detected_at"):
            setattr(signal, key, value)
    db.commit()
    db.refresh(signal)
    return _signal_to_dict(signal)


@router.delete("/opportunities/{signal_id}", summary="Delete opportunity signal", status_code=204)
def delete_opportunity_signal(signal_id: int, db: Session = Depends(get_db)) -> None:
    signal = db.query(OpportunitySignal).get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Opportunity signal not found")
    db.delete(signal)
    db.commit()


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _project_to_dict(p: InfrastructureProject) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "company": p.company,
        "location": p.location,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "capacity_mw": p.capacity_mw,
        "capex_millions": p.capex_millions,
        "capex_currency": p.capex_currency,
        "stage": p.stage.value if p.stage else None,
        "project_type": p.project_type.value if p.project_type else None,
        "partners": p.partners,
        "source_url": p.source_url,
        "source_name": p.source_name,
        "confidence_score": p.confidence_score,
        "signal_type": p.signal_type,
        "is_duplicate": p.is_duplicate,
        "canonical_project_id": p.canonical_project_id,
        "notes": p.notes,
        "detected_at": p.detected_at.isoformat() if p.detected_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _company_to_dict(c: CompanyProfile) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "category": c.category.value if c.category else None,
        "headquarters": c.headquarters,
        "stock_ticker": c.stock_ticker,
        "website": c.website,
        "known_partners": c.known_partners,
        "total_capacity_mw": c.total_capacity_mw,
        "total_capex_millions": c.total_capex_millions,
        "active_projects": c.active_projects,
        "regions_active": c.regions_active,
        "description": c.description,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _signal_to_dict(s: OpportunitySignal) -> dict[str, Any]:
    return {
        "id": s.id,
        "project_id": s.project_id,
        "opportunity_type": s.opportunity_type.value if s.opportunity_type else None,
        "title": s.title,
        "company": s.company,
        "location": s.location,
        "potential_suppliers": s.potential_suppliers,
        "likelihood_score": s.likelihood_score,
        "estimated_value_millions": s.estimated_value_millions,
        "estimated_tender_date": s.estimated_tender_date,
        "source_signal_url": s.source_signal_url,
        "notes": s.notes,
        "is_actioned": s.is_actioned,
        "detected_at": s.detected_at.isoformat() if s.detected_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }
