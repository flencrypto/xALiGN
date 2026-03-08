"""Specialist AI Agents router.

Endpoints:
  POST /api/v1/agents/build-captain    – Build planning agent
  POST /api/v1/agents/ui-surgeon       – UI analysis and component planning agent
  POST /api/v1/agents/test-pilot       – QA and Playwright automation agent
  POST /api/v1/agents/data-curator     – Valuation pipeline design agent
  POST /api/v1/agents/ops-boss         – CI/CD and environment configuration agent
  GET  /api/v1/agents/catalogue        – List all available agents
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.integration_requirements import ensure_integration_configured

logger = logging.getLogger("align.agents")

router = APIRouter(prefix="/agents", tags=["Agents"])


# ── Request models ────────────────────────────────────────────────────────────

class BuildCaptainRequest(BaseModel):
    request: str = Field(..., min_length=1, max_length=10000, description="User build goal or feature request")


class UiSurgeonRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=10000, description="UI screenshot description, reference site, or layout brief")


class TestPilotRequest(BaseModel):
    feature_description: str = Field(..., min_length=1, max_length=10000, description="Feature or user flow to generate tests for")


class DataCuratorRequest(BaseModel):
    context: str = Field(..., min_length=1, max_length=10000, description="Pricing, valuation, or data pipeline context")


class OpsBossRequest(BaseModel):
    context: str = Field(..., min_length=1, max_length=10000, description="Deployment, CI/CD, or environment configuration context")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/build-captain", summary="Build Captain – turn a goal into an implementable build plan")
async def run_build_captain(payload: BuildCaptainRequest) -> dict[str, Any]:
    """
    Convert a user feature request or goal into a structured, implementable build plan.
    Returns assumptions, ordered task list, file-level plan, acceptance criteria,
    and verification steps.

    Requires XAI_API_KEY to be configured.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    try:
        from backend.services.ai_workers import BuildCaptainWorker
        result = await BuildCaptainWorker().run(payload.request)
        return {"status": "ok", "agent": "build_captain", "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("build_captain failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ui-surgeon", summary="UI Surgeon – decompose a UI into components and build order")
async def run_ui_surgeon(payload: UiSurgeonRequest) -> dict[str, Any]:
    """
    Analyse a UI description, screenshot, or reference and produce a full
    component breakdown, Tailwind token suggestions, shadcn mapping, and build order.

    Requires XAI_API_KEY to be configured.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    try:
        from backend.services.ai_workers import UiSurgeonWorker
        result = await UiSurgeonWorker().run(payload.description)
        return {"status": "ok", "agent": "ui_surgeon", "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ui_surgeon failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/test-pilot", summary="Test Pilot – generate QA checklists and Playwright scripts")
async def run_test_pilot(payload: TestPilotRequest) -> dict[str, Any]:
    """
    Generate a comprehensive QA plan for a feature: risk list, manual checklist,
    Playwright test scripts, required data fixtures, and failure triage steps.

    Requires XAI_API_KEY to be configured.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    try:
        from backend.services.ai_workers import TestPilotWorker
        result = await TestPilotWorker().run(payload.feature_description)
        # Do not expose internal error messages from the worker to the client.
        if isinstance(result, dict) and "error" in result:
            logger.error("test_pilot worker reported error: %s", result.get("error"))
            raise HTTPException(status_code=500, detail="Test Pilot agent failed")
        return {"status": "ok", "agent": "test_pilot", "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("test_pilot failed: %s", exc)
        raise HTTPException(status_code=500, detail="Test Pilot agent failed")


@router.post("/data-curator", summary="Data Curator – design valuation and pricing data pipelines")
async def run_data_curator(payload: DataCuratorRequest) -> dict[str, Any]:
    """
    Design a pricing or valuation pipeline: data model, scoring rules, required inputs,
    API shapes, validation rules, and quick verification queries.

    Requires XAI_API_KEY to be configured.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    try:
        from backend.services.ai_workers import DataCuratorWorker
        result = await DataCuratorWorker().run(payload.context)
        return {"status": "ok", "agent": "data_curator", "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("data_curator failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ops-boss", summary="Ops Boss – CI/CD pipeline and environment configuration")
async def run_ops_boss(payload: OpsBossRequest) -> dict[str, Any]:
    """
    Generate a complete DevOps plan: env var matrix, secrets handling, CI pipeline
    steps, caching strategy, security basics, and deploy checklist.

    Requires XAI_API_KEY to be configured.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    try:
        from backend.services.ai_workers import OpsBossWorker
        result = await OpsBossWorker().run(payload.context)
        return {"status": "ok", "agent": "ops_boss", "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ops_boss failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/catalogue", summary="List all available specialist agents")
def get_agent_catalogue() -> dict[str, Any]:
    """Return metadata for all 5 specialist agents."""
    return {
        "agents": [
            {
                "id": "build_captain",
                "name": "Build Captain",
                "icon": "🏗️",
                "description": "Turns your goal into a tight build plan: tasks, file-level plan, acceptance criteria, and verification steps.",
                "endpoint": "/api/v1/agents/build-captain",
                "input_field": "request",
                "placeholder": "e.g. Build Library filters + persistence + saved crates",
            },
            {
                "id": "ui_surgeon",
                "name": "UI Surgeon",
                "icon": "🎨",
                "description": "Takes a UI description or screenshot and outputs component breakdown, Tailwind tokens, shadcn mapping, and build order.",
                "endpoint": "/api/v1/agents/ui-surgeon",
                "input_field": "description",
                "placeholder": "e.g. Describe the layout: sidebar nav, content grid, data table with filters",
            },
            {
                "id": "test_pilot",
                "name": "Test Pilot",
                "icon": "🧪",
                "description": "Generates test cases, edge cases, and Playwright scripts for any feature, then helps debug failures.",
                "endpoint": "/api/v1/agents/test-pilot",
                "input_field": "feature_description",
                "placeholder": "e.g. Library filters must persist across sessions and not break on mobile",
            },
            {
                "id": "data_curator",
                "name": "Data Curator",
                "icon": "📊",
                "description": "Designs the valuation/pricing pipeline with data contracts, scoring rules, and confidence ratings.",
                "endpoint": "/api/v1/agents/data-curator",
                "input_field": "context",
                "placeholder": "e.g. Add comps table + confidence pill logic for vinyl record valuations",
            },
            {
                "id": "ops_boss",
                "name": "Ops Boss",
                "icon": "⚙️",
                "description": "Makes your build repeatable: env vars, secrets, CI checks, dependency hygiene, and release basics.",
                "endpoint": "/api/v1/agents/ops-boss",
                "input_field": "context",
                "placeholder": "e.g. Lock down ImgBB key server-side + add CI checks for lint, typecheck, and tests",
            },
        ]
    }
