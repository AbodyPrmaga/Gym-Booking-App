from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.schemas.auth_schema import Token, TokenData, LoginSchema
from app.schemas.user_schema import UserCreate, AboutMe
from app.db import get_db
from app.db.models import User
from dotenv import load_dotenv
import os

load_dotenv()

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("[SECRET_KEY] IS NOT SET !!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_schema)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")

        if user_id is None or role is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
            )

        token_data = TokenData(user_id=user_id, role=role)
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return token_data


def safe_hash_password(password: str) -> str:
    return pwd_context.hash(password)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(login: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login.email).first()

    if (
        not user
        or not user.is_active
        or not pwd_context.verify(login.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token_data = {"user_id": user.id, "role": user.role}
    access_token = create_access_token(
        data=token_data, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    if len(data.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long (maximum 72 characters)",
        )

    hashed_password = safe_hash_password(data.password)
    user = User(
        name=data.name,
        email=data.email,
        role="user",
        password_hash=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User Created", "user_id": user.id}


@router.get("/about", response_model=AboutMe)
def about_me(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "bookings": user.bookings,
    }
