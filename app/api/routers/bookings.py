from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from typing import Optional, List

from app.db import get_db
from app.db.models import Booking, TimeSlot, User

router = APIRouter(prefix="/booking", tags=["Bookings"])


@router.post("/book")
def create_booking(user_id: int, slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.start_time < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Slot already passed")

    existing = (
        db.query(Booking)
        .filter(Booking.user_id == user_id, Booking.slot_id == slot_id)
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Booking already exists")

    current_count = (
        db.query(Booking)
        .filter(Booking.slot_id == slot_id, Booking.status == "confirmed")
        .count()
    )

    if current_count >= slot.capacity:
        raise HTTPException(status_code=400, detail="Slot is fully booked")

    new_booking = Booking(
        user_id=user_id,
        slot_id=slot_id,
        status="confirmed",
        created_at=datetime.utcnow(),
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking


@router.get("/bookings")
def get_all_bookings(
    user_id: Optional[int] = None,
    slot_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Booking)

    if user_id:
        query = query.filter(Booking.user_id == user_id)

    if slot_id:
        query = query.filter(Booking.slot_id == slot_id)

    if status:
        query = query.filter(Booking.status == status)

    return query.all()


@router.put("/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")

    if booking.status == "confirmed" and booking.slot:
        booking.slot.booked_count -= 1


    booking.status = "cancelled"
    
    db.commit()
    db.refresh(booking)

    return booking


@router.put("/{booking_id}/confirm")
def confirm_booking(booking_id: int, db: Session = Depends(get_db)):

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "confirmed":
        raise HTTPException(status_code=400, detail="Already confirmed")

    slot = booking.slot

    if slot.booked_count >= slot.capacity:
        raise HTTPException(status_code=400, detail="Slot is full")

    booking.status = "confirmed"
    slot.booked_count += 1

    db.commit()
    db.refresh(booking)

    return booking