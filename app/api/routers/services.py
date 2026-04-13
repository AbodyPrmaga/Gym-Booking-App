from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.db.models import Service
from app.schemas.service_schema import (
    ServiceCreate,
    ServiceRead,
)

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/add_service", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
):
    service = Service(
        name=service_data.name,
        description=service_data.description,
        duration_minutes=service_data.duration_minutes,
        capacity=service_data.capacity,
        price=service_data.price,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@router.get("/")
def get_all_services(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
):
    skip = (page - 1) * size

    query = db.query(Service).filter(Service.is_active == True)

    if search:
        query = query.filter(Service.name.ilike(f"%{search}%"))

    total = query.count()

    services = query.offset(skip).limit(size).all()

    return {"page": page, "size": size, "total": total, "data": services}


@router.get("/get_service/{service_id}", response_model=ServiceRead)
def get_service_by_id(
    service_id: int,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return service


@router.put("/update/{service_id}", response_model=ServiceRead)
def update_service(
    service_id: int,
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    service.name = service_data.name
    service.description = service_data.description
    service.duration_minutes = service_data.duration_minutes
    service.capacity = service_data.capacity
    service.price = service_data.price

    db.commit()
    db.refresh(service)

    return service


@router.delete("/delete/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    service.is_active = False

    db.commit()

    return