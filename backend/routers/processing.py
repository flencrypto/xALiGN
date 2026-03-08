"""Data Processing Layer – API endpoints for BATCH 2 processing services."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db

logger = logging.getLogger("align.processing")
router = APIRouter(prefix="/processing", tags=["Processing"])


@router.post("/parse/run", summary="Run structured intelligence parser")
async def run_structured_parser(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Parse raw articles and extract structured fields (company, MW, capex, stage)."""
    try:
        from backend.services.structured_parser import run_structured_parser as _run
        count = await _run(db)
        return {"status": "ok", "records_processed": count}
    except Exception as exc:
        logger.error("structured_parser failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/entities/run", summary="Run entity extraction engine")
async def run_entity_extraction(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Extract companies, suppliers, technologies, and regions from unprocessed articles."""
    try:
        from backend.services.entity_extractor import run_entity_extraction as _run
        count = await _run(db)
        return {"status": "ok", "records_processed": count}
    except Exception as exc:
        logger.error("entity_extractor failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/deduplicate/run", summary="Run deduplication engine")
async def run_deduplication(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Detect and flag duplicate infrastructure project records."""
    try:
        from backend.services.deduplication import run_deduplication as _run
        result = await _run(db)
        return {"status": "ok", **result}
    except Exception as exc:
        logger.error("deduplication failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/score/run", summary="Run source confidence scorer")
async def run_source_scoring(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Score source credibility for unscored signals."""
    try:
        from backend.services.source_scorer import run_source_scoring as _run
        count = await _run(db)
        return {"status": "ok", "records_scored": count}
    except Exception as exc:
        logger.error("source_scorer failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/classify/run", summary="Run signal classification engine")
async def run_signal_classification(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Classify unclassified signals into types (new_build, expansion, energy_deal, etc.)."""
    try:
        from backend.services.signal_classifier import run_signal_classification as _run
        count = await _run(db)
        return {"status": "ok", "records_classified": count}
    except Exception as exc:
        logger.error("signal_classifier failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/run-all", summary="Run complete data processing pipeline")
async def run_all_processing(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Run all 5 processing stages in sequence: parse → entities → score → classify → deduplicate."""
    results: dict[str, Any] = {}

    try:
        from backend.services.entity_extractor import run_entity_extraction
        results["entities"] = await run_entity_extraction(db)
    except Exception as exc:
        results["entities_error"] = str(exc)

    try:
        from backend.services.source_scorer import run_source_scoring
        results["scoring"] = await run_source_scoring(db)
    except Exception as exc:
        results["scoring_error"] = str(exc)

    try:
        from backend.services.signal_classifier import run_signal_classification
        results["classification"] = await run_signal_classification(db)
    except Exception as exc:
        results["classification_error"] = str(exc)

    try:
        from backend.services.structured_parser import run_structured_parser
        results["parsing"] = await run_structured_parser(db)
    except Exception as exc:
        results["parsing_error"] = str(exc)

    try:
        from backend.services.deduplication import run_deduplication
        results["deduplication"] = await run_deduplication(db)
    except Exception as exc:
        results["deduplication_error"] = str(exc)

    return {"status": "ok", "results": results}


@router.get("/entities/keywords", summary="List all known entity keywords")
def get_entity_keywords() -> dict[str, list[str]]:
    """Return all keyword lists used by the entity extraction engine."""
    from backend.services.entity_extractor import (
        CONTRACTORS, DC_OPERATORS, GLOBAL_REGIONS, HYPERSCALERS,
        MEP_SUPPLIERS, TECHNOLOGIES, UK_REGIONS,
    )
    return {
        "hyperscalers": HYPERSCALERS,
        "dc_operators": DC_OPERATORS,
        "mep_suppliers": MEP_SUPPLIERS,
        "contractors": CONTRACTORS,
        "technologies": TECHNOLOGIES,
        "uk_regions": UK_REGIONS,
        "global_regions": GLOBAL_REGIONS,
    }


@router.get("/classify/taxonomy", summary="List signal classification taxonomy")
def get_signal_taxonomy() -> dict[str, Any]:
    """Return the signal type taxonomy with keyword examples."""
    from backend.services.signal_classifier import _RULES
    return {
        "signal_types": [
            {"type": signal_type, "keywords": keywords[:5]}
            for signal_type, keywords in _RULES
        ] + [{"type": "general", "keywords": []}]
    }


@router.get("/source/trust-list", summary="Return source trust registry")
def get_source_trust_list() -> dict[str, Any]:
    """Return the source trust registry with scores."""
    from backend.services.source_scorer import SOURCE_TRUST
    return {
        "sources": [
            {"domain": domain, "trust_score": score}
            for domain, score in sorted(SOURCE_TRUST.items(), key=lambda x: -x[1])
        ]
    }
