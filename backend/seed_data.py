"""Seed initial company (account) records on first startup.

Records are upserted on every startup – existing records are updated with the
latest intel so re-deploying always reflects the canonical seed data.
"""

import logging

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.account import (
    Account,
    AccountType,
    Contact,
    InfluenceLevel,
    TriggerSignal,
    SignalType,
)

logger = logging.getLogger("align.seed")

# ---------------------------------------------------------------------------
# Seed data – canonical initial company records
# ---------------------------------------------------------------------------

_SEED_ACCOUNTS = [
    {
        "account": {
            "name": "Carbon3.ai",
            "type": AccountType.hyperscaler,
            "stage": "Target",
            "location": "UK (brownfield industrial sites nationwide)",
            "website": "https://carbon3.ai",
            "tags": "newly-formed, AI, renewable, 2025-launch, brownfield-refurb",
            "tier_target": "Tier 1",
            "notes": (
                "INTEL SUMMARY: 100% renewable-powered AI mesh on repurposed industrial sites – "
                "perfect match for our DC refurb delivery expertise.\n\n"
                "TYPE: Hyperscale / Sovereign AI Operator\n\n"
                "TRIGGER SIGNALS: £1bn funding round (Dec 2025), NVIDIA Blackwell rollout Q1 2026, "
                "ex-gov CTO hire.\n\n"
                "SUGGESTED NEXT ACTION: LinkedIn DM to CEO Tom Humphreys.\n"
                "Draft DM: \"Hi Tom, congrats on the £1bn sovereign AI network – repurposing industrial sites for "
                "renewable compute is spot on what we see winning. We help contractors qualify and bid these faster. "
                "Coffee next week to swap notes?\"\n\n"
                "BACKUPS: 1) Comment on their latest post. 2) Email press@carbon3.ai with estimating case study."
            ),
        },
        "contacts": [
            {
                "name": "Tom Humphreys",
                "role": "CEO",
                "influence_level": InfluenceLevel.decision_maker,
                "notes": (
                    "Draft LinkedIn DM: \"Hi Tom, congrats on the £1bn sovereign AI network – repurposing industrial "
                    "sites for renewable compute is spot on what we see winning. We help contractors qualify and bid "
                    "these faster. Coffee next week to swap notes?\""
                ),
            },
        ],
        "signals": [
            {
                "signal_type": SignalType.planning,
                "title": "£1bn renewable AI mesh on brownfield industrial sites",
                "description": (
                    "Carbon3.ai is building a £1bn sovereign AI network across repurposed UK brownfield sites. "
                    "100% renewable-powered compute – directly matching our brownfield DC refurb delivery expertise."
                ),
                "source_url": None,
            },
            {
                "signal_type": SignalType.framework_award,
                "title": "NVIDIA Blackwell rollout – Q1 2026",
                "description": (
                    "Scheduled Q1 2026 NVIDIA Blackwell GPU rollout across the mesh. "
                    "High-density build-out and commissioning scope imminent."
                ),
                "source_url": None,
            },
            {
                "signal_type": SignalType.hiring_spike,
                "title": "ex-Government CTO hired",
                "description": (
                    "Recent hire of a former government CTO signals public-sector partnerships, "
                    "accelerated delivery ambitions, and potential framework procurement routes."
                ),
                "source_url": None,
            },
        ],
    },
    {
        "account": {
            "name": "5C Group",
            "type": AccountType.hyperscaler,
            "stage": "Target",
            "location": "UK + Europe (2GW pipeline)",
            "website": None,
            "tags": "newly-formed, merger, AI-GPU, 2025-expansion",
            "tier_target": "Tier 1",
            "notes": (
                "INTEL SUMMARY: High-density AI campuses across UK/EU – massive scope for bid support "
                "and estimating.\n\n"
                "TYPE: Hyperscale AI Campus Developer\n\n"
                "TRIGGER SIGNALS: Apr 2025 Hypertec + 5C merger, fresh funding round, 2GW GPU-ready roadmap.\n\n"
                "SUGGESTED NEXT ACTION: LinkedIn note to Jonathan Ahdoot.\n"
                "Draft: \"Jonathan, massive move on the 2GW AI roadmap. We automate bid packs and spot scope gaps "
                "for exactly these GPU campuses. Keen to connect on upcoming UK/EU opportunities?\""
            ),
        },
        "contacts": [
            {
                "name": "Jonathan Ahdoot",
                "role": "Senior Leadership",
                "influence_level": InfluenceLevel.decision_maker,
                "notes": (
                    "Draft LinkedIn note: \"Jonathan, massive move on the 2GW AI roadmap. We automate bid packs "
                    "and spot scope gaps for exactly these GPU campuses. Keen to connect on upcoming UK/EU "
                    "opportunities?\""
                ),
            },
        ],
        "signals": [
            {
                "signal_type": SignalType.framework_award,
                "title": "Hypertec + 5C merger completed – Apr 2025",
                "description": (
                    "Combined entity formed April 2025 with fresh funding round confirmed. "
                    "Creates a major 2GW GPU campus operator across UK and Europe."
                ),
                "source_url": None,
            },
            {
                "signal_type": SignalType.planning,
                "title": "2GW GPU-ready campus roadmap",
                "description": (
                    "Aggressive 2GW high-density GPU campus roadmap across UK/EU. "
                    "Significant bid pack, scope gap, and estimating support opportunity."
                ),
                "source_url": None,
            },
        ],
    },
    {
        "account": {
            "name": "Centersquare",
            "type": AccountType.colo,
            "stage": "Target",
            "location": "UK + Europe (80 facilities)",
            "website": None,
            "tags": "newly-formed, acquisition, AI-density, 2025-growth",
            "tier_target": "Tier 1",
            "notes": (
                "INTEL SUMMARY: Rapid expansion via acquisitions – immediate pipeline activity for "
                "compliance & scope-gap work.\n\n"
                "TYPE: Colocation Operator (Brookfield-backed)\n\n"
                "TRIGGER SIGNALS: $1B acquisition of 10 sites (Oct 2025), AI density upgrades live "
                "across 80-facility portfolio.\n\n"
                "SUGGESTED NEXT ACTION: LinkedIn to Spencer Mullee.\n"
                "Draft: \"Spencer, congrats on the $1B expansion push. Our platform cuts bid pain and hands clean "
                "scopes to delivery. Quick call on how we've helped similar colos win more?\""
            ),
        },
        "contacts": [
            {
                "name": "Spencer Mullee",
                "role": "Senior Leadership",
                "influence_level": InfluenceLevel.decision_maker,
                "notes": (
                    "Draft LinkedIn message: \"Spencer, congrats on the $1B expansion push. Our platform cuts bid "
                    "pain and hands clean scopes to delivery. Quick call on how we've helped similar colos win more?\""
                ),
            },
        ],
        "signals": [
            {
                "signal_type": SignalType.land_acquisition,
                "title": "$1B acquisition of 10 sites – Oct 2025",
                "description": (
                    "Brookfield-backed Centersquare acquired 10 data centre sites for $1B in October 2025, "
                    "taking total portfolio to 80 facilities. Immediate refurb and AI density upgrade pipeline."
                ),
                "source_url": None,
            },
            {
                "signal_type": SignalType.planning,
                "title": "AI density upgrades across 80-facility portfolio",
                "description": (
                    "Active programme to upgrade AI compute density across all 80 facilities. "
                    "High compliance complexity and scope-gap risk across each site."
                ),
                "source_url": None,
            },
        ],
    },
    {
        "account": {
            "name": "Yotta Data Center",
            "type": AccountType.hyperscaler,
            "stage": "Target",
            "location": "UK + Europe + US",
            "website": None,
            "tags": "newly-formed, rebrand, investment, 2025-expansion",
            "tier_target": "Tier 2",
            "notes": (
                "INTEL SUMMARY: Fresh capital and rebrand driving hyperscale growth – ideal for "
                "qualification and bid-pack automation.\n\n"
                "TYPE: Hyperscale Operator\n\n"
                "TRIGGER SIGNALS: Feb 2025 Media DC investment + rebrand, multiple UK/EU site expansions.\n\n"
                "SUGGESTED NEXT ACTION: LinkedIn to leadership (search 'Yotta CEO' to identify current contact).\n"
                "Draft: \"Team at Yotta, strong rebrand and expansion. We support DC operators with qualification "
                "and compliance tools. Happy to share how we're helping similar players win more refurbs.\""
            ),
        },
        "contacts": [],
        "signals": [
            {
                "signal_type": SignalType.planning,
                "title": "Feb 2025 rebrand and multi-region expansion",
                "description": (
                    "Yotta Data Center rebranded in Feb 2025 following Media DC investment. "
                    "Active expansion into UK, Europe and US markets creating multiple bid opportunities."
                ),
                "source_url": None,
            },
        ],
    },
]


def seed_initial_accounts(db: Session) -> None:
    """Upsert seed accounts – insert new ones and update existing ones."""
    inserted = 0
    updated = 0

    for record in _SEED_ACCOUNTS:
        acc_data = record["account"]
        existing = db.query(Account).filter(Account.name == acc_data["name"]).first()

        if existing:
            # Update all fields on the existing record with latest seed data
            for field, value in acc_data.items():
                setattr(existing, field, value)
            # Upsert contacts: clear and re-create so names/notes stay fresh
            db.query(Contact).filter(Contact.account_id == existing.id).delete()
            for c in record.get("contacts", []):
                db.add(Contact(account_id=existing.id, **c))
            # Upsert signals: clear and re-create
            db.query(TriggerSignal).filter(TriggerSignal.account_id == existing.id).delete()
            for s in record.get("signals", []):
                db.add(TriggerSignal(account_id=existing.id, **s))
            updated += 1
        else:
            acc = Account(**acc_data)
            db.add(acc)
            db.flush()  # get acc.id before adding children
            for c in record.get("contacts", []):
                db.add(Contact(account_id=acc.id, **c))
            for s in record.get("signals", []):
                db.add(TriggerSignal(account_id=acc.id, **s))
            inserted += 1

    if inserted or updated:
        db.commit()
        logger.info("Seed: %d account(s) inserted, %d updated.", inserted, updated)
    else:
        logger.debug("Seed: nothing to do.")


def run_seed() -> None:
    """Entry point called from the application lifespan."""
    db = SessionLocal()
    try:
        seed_initial_accounts(db)
    except Exception as exc:
        logger.error("Seed failed (non-fatal): %s", exc)
        db.rollback()
    finally:
        db.close()
