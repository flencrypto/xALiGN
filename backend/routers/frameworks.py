"""Framework & procurement tracker router.

Endpoints:
  GET    /api/v1/frameworks          – List frameworks (filterable by status/region)
  POST   /api/v1/frameworks          – Create a framework entry
  GET    /api/v1/frameworks/{id}     – Get a single entry
  PATCH  /api/v1/frameworks/{id}     – Update an entry
  DELETE /api/v1/frameworks/{id}     – Delete an entry
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.framework import FrameworkStatus, ProcurementFramework
from backend.schemas.framework import (
    ProcurementFrameworkCreate,
    ProcurementFrameworkRead,
    ProcurementFrameworkUpdate,
)

router = APIRouter(prefix="/frameworks", tags=["Procurement Frameworks"])


@router.get("", response_model=list[ProcurementFrameworkRead])
def list_frameworks(
    status: FrameworkStatus | None = None,
    region: str | None = None,
    we_are_listed: bool | None = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """List procurement frameworks with optional filters."""
    q = db.query(ProcurementFramework)
    if status is not None:
        q = q.filter(ProcurementFramework.status == status)
    if region is not None:
        q = q.filter(ProcurementFramework.region.ilike(f"%{region}%"))
    if we_are_listed is not None:
        q = q.filter(ProcurementFramework.we_are_listed == we_are_listed)
    return q.order_by(ProcurementFramework.expiry_date.asc().nullslast()).offset(skip).limit(limit).all()


@router.post("", response_model=ProcurementFrameworkRead, status_code=status.HTTP_201_CREATED)
def create_framework(payload: ProcurementFrameworkCreate, db: Session = Depends(get_db)):
    """Create a new procurement framework entry."""
    obj = ProcurementFramework(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{framework_id}", response_model=ProcurementFrameworkRead)
def get_framework(framework_id: int, db: Session = Depends(get_db)):
    obj = db.get(ProcurementFramework, framework_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Framework not found")
    return obj


@router.patch("/{framework_id}", response_model=ProcurementFrameworkRead)
def update_framework(
    framework_id: int, payload: ProcurementFrameworkUpdate, db: Session = Depends(get_db)
):
    obj = db.get(ProcurementFramework, framework_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Framework not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    # Auto-update status based on expiry_date
    if obj.expiry_date:
        today = date.today()
        if obj.expiry_date < today:
            obj.status = FrameworkStatus.expired
        elif obj.expiry_date <= today + timedelta(days=90):
            obj.status = FrameworkStatus.expiring_soon
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{framework_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_framework(framework_id: int, db: Session = Depends(get_db)):
    obj = db.get(ProcurementFramework, framework_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Framework not found")
    db.delete(obj)
    db.commit()
