from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.auth_schema import TokenData
from app.db import get_db
from app.db.models import User
from app.schemas.user_schema import UserRead, UserUpdate
from .auth import get_current_user, safe_hash_password
from sqlalchemy.orm import Session
from sqlalchemy import or_


def confirm_admin(current_user: TokenData = Depends(get_current_user)):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action",
        )

    return current_user


router = APIRouter(
    prefix="/users", tags=["Users"], dependencies=[Depends(confirm_admin)]
)


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    is_active: bool | None = Query(None),
):

    skip = (page - 1) * size

    base_query = db.query(User).filter(User.role != "admin")

    if is_active is not None:
        base_query = base_query.filter(User.is_active == is_active)

    if search:
        base_query = base_query.filter(
            or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )

    total = base_query.count()

    allowed_sorts = {
        "id": User.id,
        "name": User.name,
        "email": User.email,
        "created_at": User.created_at,
    }

    column = allowed_sorts.get(sort_by, User.created_at)

    if sort_order.lower() == "desc":
        base_query = base_query.order_by(column.desc())
    else:
        base_query = base_query.order_by(column.asc())

    users = base_query.offset(skip).limit(size).all()

    return {
        "page": page,
        "size": size,
        "total": total,
        "data": [UserRead.from_orm(u) for u in users],
    }


@router.get("/{id}", response_model=UserRead)
def get_user(
    id: int,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.patch("/update/{id}", response_model=UserRead)
def update_user(
    id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    data = payload.model_dump(exclude_unset=True)

    if not data:
        return user


    if "password" in data and data["password"]:
        user.password_hash = safe_hash_password(data["password"])
        del data["password"]

    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


@router.delete("/delete/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = False

    db.commit()

    return
