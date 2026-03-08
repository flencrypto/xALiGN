"""xAliGn helper utilities – upsert and search wrappers for the briefing pipeline.

These async helpers translate the generic entity-type / payload calls from
``briefing_parser.py`` into concrete SQLAlchemy ORM operations against the
existing Account, Opportunity, TriggerSignal (and generic JSON-doc) models.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select

from backend.database import SessionLocal
from backend.models.account import Account, AccountType, TriggerSignal, SignalType
from backend.models.opportunity import Opportunity, OpportunityStage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

_ACCOUNT_TYPE_MAP: Dict[str, AccountType] = {
    "hyperscaler": AccountType.hyperscaler,
    "operator": AccountType.operator,
    "developer": AccountType.developer,
    "colo": AccountType.colo,
    "enterprise": AccountType.enterprise,
    "supplier": AccountType.enterprise,   # closest match
    "other": AccountType.enterprise,
}

_OPP_STAGE_MAP: Dict[str, OpportunityStage] = {
    "planning": OpportunityStage.target,
    "announced": OpportunityStage.lead,
    "target": OpportunityStage.target,
    "lead": OpportunityStage.lead,
    "qualified": OpportunityStage.qualified,
    "under_construction": OpportunityStage.qualified,
    "operational": OpportunityStage.delivered,
    "cancelled": OpportunityStage.lost,
    "bid": OpportunityStage.bid,
    "won": OpportunityStage.won,
    "lost": OpportunityStage.lost,
    "delivered": OpportunityStage.delivered,
}

_SIGNAL_TYPE_MAP: Dict[str, SignalType] = {
    "new_build": SignalType.planning,
    "expansion": SignalType.planning,
    "cancellation": SignalType.planning,
    "acquisition": SignalType.framework_award,
    "energy_deal": SignalType.grid,
    "supply_chain_risk": SignalType.land_acquisition,
    "tender_opportunity": SignalType.framework_award,
    "bid_win": SignalType.framework_award,
    "other": SignalType.planning,
}


def _get_or_create_account(db, name: str, payload: dict) -> Account:
    """Return existing account by name or create a new one."""
    stmt = select(Account).where(Account.name == name)
    account = db.execute(stmt).scalar_one_or_none()
    if account is None:
        raw_type = (payload.get("type") or "other").lower()
        account = Account(
            name=name,
            type=_ACCOUNT_TYPE_MAP.get(raw_type, AccountType.enterprise),
            location=payload.get("location"),
            notes=payload.get("source"),
        )
        db.add(account)
        db.flush()
    else:
        if payload.get("location") and not account.location:
            account.location = payload["location"]
        account.updated_at = datetime.utcnow()
    return account


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------


async def xAliGn_upsert(entity_type: str, payload: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
    """Insert-or-update a record for the given *entity_type*.

    Parameters
    ----------
    entity_type : str
        One of ``"account"``, ``"opportunity"``, ``"signal"``, ``"doc"``.
    payload : dict
        Field values coming from the briefing parser.
    idempotency_key : str
        A deterministic key used to detect duplicates within a run.
    """
    db = SessionLocal()
    try:
        if entity_type == "account":
            name = payload.get("name", "Unknown")
            account = _get_or_create_account(db, name, payload)
            db.commit()
            return {"id": account.id, "name": account.name}

        elif entity_type == "opportunity":
            account_name = payload.get("account_name", "Unknown")
            account = _get_or_create_account(db, account_name, payload)

            title = payload.get("name") or payload.get("project_name") or "Untitled"
            stmt = select(Opportunity).where(
                Opportunity.account_id == account.id,
                Opportunity.title == title,
            )
            opp = db.execute(stmt).scalar_one_or_none()

            raw_stage = (payload.get("stage") or "target").lower()
            stage = _OPP_STAGE_MAP.get(raw_stage, OpportunityStage.target)

            if opp is None:
                desc_parts = [payload.get("description") or ""]
                if payload.get("location"):
                    desc_parts.append(f"Location: {payload['location']}")
                if payload.get("partners"):
                    desc_parts.append(f"Partners: {', '.join(payload['partners'])}")

                opp = Opportunity(
                    account_id=account.id,
                    title=title,
                    description=" | ".join(p for p in desc_parts if p),
                    stage=stage,
                    estimated_value=_parse_value(payload.get("value")),
                )
                db.add(opp)
            else:
                opp.stage = stage
                opp.updated_at = datetime.utcnow()
                if payload.get("description"):
                    opp.description = payload["description"]

            db.commit()
            return {"id": opp.id, "title": opp.title}

        elif entity_type == "signal":
            account_name = payload.get("account_name", "Unknown")
            account = _get_or_create_account(db, account_name, payload)

            raw_sig = (payload.get("type") or payload.get("signal_type") or "other").lower()
            sig_type = _SIGNAL_TYPE_MAP.get(raw_sig, SignalType.planning)

            title = payload.get("title", "Untitled signal")
            # deduplicate by title + account within recent window
            stmt = select(TriggerSignal).where(
                TriggerSignal.account_id == account.id,
                TriggerSignal.title == title,
            )
            existing = db.execute(stmt).scalar_one_or_none()

            if existing is None:
                desc = payload.get("summary", "")
                if payload.get("strategic_insight"):
                    desc += f" | Insight: {payload['strategic_insight']}"

                sig = TriggerSignal(
                    account_id=account.id,
                    signal_type=sig_type,
                    title=title,
                    description=desc,
                    source_url=payload.get("source"),
                )
                db.add(sig)
                db.commit()
                return {"id": sig.id, "title": sig.title}
            else:
                db.commit()
                return {"id": existing.id, "title": existing.title, "duplicate": True}

        elif entity_type == "doc":
            # Generic intelligence dataset entry – store as a JSON-blob note
            # attached to the relevant account's notes or as a TriggerSignal.
            company = payload.get("company", "Unknown")
            account = _get_or_create_account(db, company, payload)

            title = f"{payload.get('project', 'Intel')} – {payload.get('project_type', 'update')}"
            desc = json.dumps({k: v for k, v in payload.items() if v is not None}, default=str)

            sig = TriggerSignal(
                account_id=account.id,
                signal_type=SignalType.planning,
                title=title[:255],
                description=desc,
                source_url=payload.get("source"),
            )
            db.add(sig)
            db.commit()
            return {"id": sig.id, "title": sig.title}

        else:
            logger.warning("xAliGn_upsert: unknown entity_type %r", entity_type)
            return {"error": f"unknown entity_type: {entity_type}"}

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def xAliGn_search(
    entity_type: str,
    query: str,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Search for records of the given *entity_type* matching *query*.

    Returns ``{"results": [...]}``.
    """
    options = options or {}
    limit = options.get("limit", 10)
    db = SessionLocal()
    try:
        if entity_type == "account":
            stmt = (
                select(Account)
                .where(Account.name.ilike(f"%{query}%"))
                .limit(limit)
            )
            rows = db.execute(stmt).scalars().all()
            return {
                "results": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "type": r.type.value if r.type else None,
                        "location": r.location,
                        "last_touch_days_ago": (datetime.utcnow() - r.updated_at).days if r.updated_at else 999,
                    }
                    for r in rows
                ]
            }

        elif entity_type == "opportunity":
            stmt = select(Opportunity).where(
                Opportunity.title.ilike(f"%{query}%")
            )
            stage_filter = options.get("stage")
            if stage_filter:
                valid = [_OPP_STAGE_MAP.get(s.lower(), s) for s in stage_filter if isinstance(s, str)]
                if valid:
                    stmt = stmt.where(Opportunity.stage.in_(valid))
            stmt = stmt.limit(limit)
            rows = db.execute(stmt).scalars().all()
            return {
                "results": [
                    {
                        "id": r.id,
                        "title": r.title,
                        "stage": r.stage.value if r.stage else None,
                        "estimated_value": r.estimated_value,
                    }
                    for r in rows
                ]
            }

        elif entity_type == "signal":
            stmt = select(TriggerSignal).where(
                TriggerSignal.title.ilike(f"%{query}%")
            )
            date_gte = options.get("date_gte")
            if date_gte:
                stmt = stmt.where(TriggerSignal.detected_at >= date_gte)
            stmt = stmt.order_by(TriggerSignal.detected_at.desc()).limit(limit)
            rows = db.execute(stmt).scalars().all()
            return {
                "results": [
                    {
                        "id": r.id,
                        "title": r.title,
                        "signal_type": r.signal_type.value if r.signal_type else None,
                        "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                    }
                    for r in rows
                ]
            }

        else:
            return {"results": []}

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_value(raw: Any) -> Optional[float]:
    """Best-effort parse of a currency string to float."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = str(raw).replace(",", "").replace("£", "").replace("$", "").replace("€", "").strip()
    # Handle "1.5bn", "500m" etc.
    multiplier = 1
    lower = cleaned.lower()
    if lower.endswith("bn") or lower.endswith("b"):
        multiplier = 1_000_000_000
        cleaned = lower.rstrip("bn").rstrip("b").strip()
    elif lower.endswith("mn") or lower.endswith("m"):
        multiplier = 1_000_000
        cleaned = lower.rstrip("mn").rstrip("m").strip()
    elif lower.endswith("k"):
        multiplier = 1_000
        cleaned = lower.rstrip("k").strip()
    try:
        return float(cleaned) * multiplier
    except (ValueError, TypeError):
        return None
