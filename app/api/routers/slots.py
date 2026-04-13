from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db import get_db
from app.db.models import TimeSlot, Booking ,Trainer

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.post("/create_slot")
def create_slot(
    service_id: int,
    start_time: datetime,
    end_time: datetime,
    capacity: int,
    trainer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):

    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    
    if trainer_id:
        conflict = (
            db.query(TimeSlot)
            .filter(
                TimeSlot.trainer_id == trainer_id,
                TimeSlot.start_time < end_time,
                TimeSlot.end_time > start_time,
            )
            .first()
        )

        if conflict:
            raise HTTPException(
                status_code=409, detail="Trainer already has a slot in this time range"
            )

    new_slot = TimeSlot(
        service_id=service_id,
        start_time=start_time,
        end_time=end_time,
        capacity=capacity,
        trainer_id=trainer_id,
    )

    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)

    return new_slot


@router.get("/get_slots")
def get_slots(
    service_id: Optional[int] = None,
    trainer_id: Optional[int] = None,
    date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    query = db.query(TimeSlot)

    if service_id:
        query = query.filter(TimeSlot.service_id == service_id)

    if trainer_id:
        query = query.filter(TimeSlot.trainer_id == trainer_id)

    if date:
        query = query.filter(
            TimeSlot.start_time >= date,
            TimeSlot.start_time < date.replace(hour=23, minute=59, second=59),
        )

    return query.all()


@router.get("/get_slot/{slot_id}")
def get_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    bookings_count = db.query(Booking).filter(Booking.slot_id == slot_id,Booking.status == "confirmed").count()

    return {
        "id": slot.id,
        "service_id": slot.service_id,
        "trainer_name": slot.trainer.name,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "capacity": slot.capacity,
        "current_bookings": bookings_count,
        "remaining_capacity": slot.capacity - bookings_count,
    }


@router.patch("/update/{slot_id}")
def update_slot(
    slot_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    capacity: Optional[int] = None,
    trainer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    new_start = start_time or slot.start_time
    new_end = end_time or slot.end_time
    new_trainer = trainer_id if trainer_id is not None else slot.trainer_id

    if new_end <= new_start:
        raise HTTPException(status_code=400, detail="Invalid time range")

    if new_trainer:
        conflict = (
            db.query(TimeSlot)
            .filter(
                TimeSlot.trainer_id == new_trainer,
                TimeSlot.id != slot_id,
                TimeSlot.start_time < new_end,
                TimeSlot.end_time > new_start,
            )
            .first()
        )

        if conflict:
            raise HTTPException(
                status_code=409,
                detail="Trainer has conflicting slot"
            )

    slot.start_time = new_start
    slot.end_time = new_end

    if capacity is not None:
        slot.capacity = capacity

    if trainer_id is not None:
        slot.trainer_id = trainer_id

    db.commit()
    db.refresh(slot)

    return slot


@router.delete("/delete/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    bookings_count = db.query(Booking).filter(Booking.slot_id == slot_id).count()

    if bookings_count > 0:
        raise HTTPException(
            status_code=400, detail="Cannot delete slot with existing bookings"
        )

    db.delete(slot)
    db.commit()

    return {"message": "Slot deleted successfully"}