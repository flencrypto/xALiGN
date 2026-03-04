"""Lead-time intelligence database router.

Provides CRUD endpoints and a seed endpoint for common data centre equipment:
switchgear, UPS, chillers, generators, and more.

Endpoints:
  GET    /api/v1/lead-times            – List items (filterable by category/region)
  POST   /api/v1/lead-times            – Create a new item
  GET    /api/v1/lead-times/{id}       – Get a single item
  PATCH  /api/v1/lead-times/{id}       – Update an item
  DELETE /api/v1/lead-times/{id}       – Delete an item
  POST   /api/v1/lead-times/seed       – Seed with default dataset
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.leadtime import EquipmentCategory, LeadTimeItem
from backend.schemas.leadtime import LeadTimeItemCreate, LeadTimeItemRead, LeadTimeItemUpdate

router = APIRouter(prefix="/lead-times", tags=["Lead-Time Intelligence"])

# ── Default seed dataset ──────────────────────────────────────────────────────

_SEED_DATA: list[dict] = [
    # Switchgear
    {
        "category": EquipmentCategory.switchgear,
        "manufacturer": "Schneider Electric",
        "model_ref": "MV Switchgear SM6",
        "description": "Medium voltage switchgear ring main unit",
        "lead_weeks_min": 16,
        "lead_weeks_max": 28,
        "lead_weeks_typical": 22.0,
        "region": "UK",
        "notes": "Lead times extended in 2023–2024 due to supply chain constraints.",
        "source": "Industry benchmark 2024",
    },
    {
        "category": EquipmentCategory.switchgear,
        "manufacturer": "ABB",
        "model_ref": "SafeRing / SafePlus",
        "description": "Ring main unit MV switchgear up to 24 kV",
        "lead_weeks_min": 14,
        "lead_weeks_max": 26,
        "lead_weeks_typical": 20.0,
        "region": "UK",
        "source": "Vendor data 2024",
    },
    {
        "category": EquipmentCategory.switchgear,
        "manufacturer": "Eaton",
        "model_ref": "XIRIA",
        "description": "Gas-insulated MV switchgear",
        "lead_weeks_min": 18,
        "lead_weeks_max": 32,
        "lead_weeks_typical": 24.0,
        "region": "EU",
        "source": "Vendor data 2024",
    },
    # UPS
    {
        "category": EquipmentCategory.ups,
        "manufacturer": "Schneider Electric",
        "model_ref": "Galaxy VS / VX",
        "description": "3-phase UPS 10–500 kVA",
        "lead_weeks_min": 8,
        "lead_weeks_max": 20,
        "lead_weeks_typical": 14.0,
        "region": "UK",
        "source": "Industry benchmark 2024",
    },
    {
        "category": EquipmentCategory.ups,
        "manufacturer": "Vertiv",
        "model_ref": "Liebert EXL S1",
        "description": "Modular UPS 100–1000 kW",
        "lead_weeks_min": 10,
        "lead_weeks_max": 22,
        "lead_weeks_typical": 16.0,
        "region": "UK",
        "source": "Vendor data 2024",
    },
    {
        "category": EquipmentCategory.ups,
        "manufacturer": "Eaton",
        "model_ref": "9PX / 93PR",
        "description": "3-phase UPS 20–200 kVA",
        "lead_weeks_min": 6,
        "lead_weeks_max": 16,
        "lead_weeks_typical": 10.0,
        "region": "UK",
        "source": "Vendor data 2024",
    },
    # Chillers
    {
        "category": EquipmentCategory.chiller,
        "manufacturer": "Airedale",
        "model_ref": "InRax / SmartCool",
        "description": "Precision air conditioning for data centres",
        "lead_weeks_min": 10,
        "lead_weeks_max": 24,
        "lead_weeks_typical": 16.0,
        "region": "UK",
        "source": "Industry benchmark 2024",
    },
    {
        "category": EquipmentCategory.chiller,
        "manufacturer": "Stulz",
        "model_ref": "CyberAir 3PRO",
        "description": "Precision cooling CRAC unit",
        "lead_weeks_min": 12,
        "lead_weeks_max": 26,
        "lead_weeks_typical": 18.0,
        "region": "EU",
        "source": "Vendor data 2024",
    },
    {
        "category": EquipmentCategory.chiller,
        "manufacturer": "Carrier",
        "model_ref": "AquaSnap 30RB",
        "description": "Air-cooled chiller plant 60–400 kW",
        "lead_weeks_min": 14,
        "lead_weeks_max": 28,
        "lead_weeks_typical": 20.0,
        "region": "UK",
        "source": "Vendor data 2024",
    },
    # Generators
    {
        "category": EquipmentCategory.generator,
        "manufacturer": "Cummins",
        "model_ref": "C1100D5 / C2000D5",
        "description": "Diesel standby generator 1100–2000 kVA",
        "lead_weeks_min": 20,
        "lead_weeks_max": 40,
        "lead_weeks_typical": 30.0,
        "region": "UK",
        "notes": "Larger sets (>1 MVA) may require 36–52 weeks.",
        "source": "Industry benchmark 2024",
    },
    {
        "category": EquipmentCategory.generator,
        "manufacturer": "Caterpillar",
        "model_ref": "C32 / C175",
        "description": "Diesel generator 1000–4400 kVA",
        "lead_weeks_min": 24,
        "lead_weeks_max": 52,
        "lead_weeks_typical": 36.0,
        "region": "UK",
        "notes": "Critical path item – order early.",
        "source": "Vendor data 2024",
    },
    {
        "category": EquipmentCategory.generator,
        "manufacturer": "Rolls-Royce / MTU",
        "model_ref": "Series 4000",
        "description": "High-power diesel generator 1600–3300 kVA",
        "lead_weeks_min": 26,
        "lead_weeks_max": 52,
        "lead_weeks_typical": 38.0,
        "region": "EU",
        "source": "Vendor data 2024",
    },
    # Transformers
    {
        "category": EquipmentCategory.transformer,
        "manufacturer": "ABB",
        "model_ref": "GEAFOL cast-resin",
        "description": "Dry-type MV/LV distribution transformer",
        "lead_weeks_min": 12,
        "lead_weeks_max": 24,
        "lead_weeks_typical": 16.0,
        "region": "UK",
        "source": "Industry benchmark 2024",
    },
    # Busbars
    {
        "category": EquipmentCategory.busbar,
        "manufacturer": "Siemens",
        "model_ref": "BD01 / SIVACON 8PS",
        "description": "Busbar trunking system 800–6300 A",
        "lead_weeks_min": 8,
        "lead_weeks_max": 18,
        "lead_weeks_typical": 12.0,
        "region": "UK",
        "source": "Vendor data 2024",
    },
    # Batteries
    {
        "category": EquipmentCategory.battery,
        "manufacturer": "EnerSys",
        "model_ref": "DataSafe XE",
        "description": "VRLA battery strings for UPS",
        "lead_weeks_min": 4,
        "lead_weeks_max": 12,
        "lead_weeks_typical": 8.0,
        "region": "UK",
        "source": "Vendor data 2024",
    },
]


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[LeadTimeItemRead])
def list_lead_times(
    category: EquipmentCategory | None = None,
    region: str | None = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """List lead-time entries, optionally filtered by category and/or region."""
    q = db.query(LeadTimeItem)
    if category is not None:
        q = q.filter(LeadTimeItem.category == category)
    if region is not None:
        q = q.filter(LeadTimeItem.region.ilike(f"%{region}%"))
    return q.order_by(LeadTimeItem.category, LeadTimeItem.lead_weeks_typical).offset(skip).limit(limit).all()


@router.post("", response_model=LeadTimeItemRead, status_code=status.HTTP_201_CREATED)
def create_lead_time(payload: LeadTimeItemCreate, db: Session = Depends(get_db)):
    """Create a new lead-time entry."""
    obj = LeadTimeItem(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{item_id}", response_model=LeadTimeItemRead)
def get_lead_time(item_id: int, db: Session = Depends(get_db)):
    obj = db.get(LeadTimeItem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Lead-time item not found")
    return obj


@router.patch("/{item_id}", response_model=LeadTimeItemRead)
def update_lead_time(item_id: int, payload: LeadTimeItemUpdate, db: Session = Depends(get_db)):
    obj = db.get(LeadTimeItem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Lead-time item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead_time(item_id: int, db: Session = Depends(get_db)):
    obj = db.get(LeadTimeItem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Lead-time item not found")
    db.delete(obj)
    db.commit()


# ── Seed ──────────────────────────────────────────────────────────────────────

@router.post(
    "/seed",
    response_model=list[LeadTimeItemRead],
    status_code=status.HTTP_201_CREATED,
    summary="Seed the lead-time database with default equipment data",
)
def seed_lead_times(db: Session = Depends(get_db)):
    """
    Seed the lead-time database with default switchgear, UPS, chiller,
    generator, transformer, busbar, and battery entries.

    Already-existing entries (matched by description) are skipped.
    """
    existing_descriptions = {
        row.description
        for row in db.query(LeadTimeItem.description).all()
    }
    created: list[LeadTimeItem] = []
    for entry in _SEED_DATA:
        if entry["description"] in existing_descriptions:
            continue
        obj = LeadTimeItem(**entry)
        db.add(obj)
        created.append(obj)

    db.commit()
    for obj in created:
        db.refresh(obj)
    return created
