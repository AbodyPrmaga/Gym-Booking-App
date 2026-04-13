from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from app.db.models import User
from app.db import SessionLocal

db: Session = SessionLocal()

hashed_password = bcrypt.hash("StrongAdminPassword123")
admin_user = User(
    name="super-admin",
    email="admin@example.com",
    password_hash=hashed_password,
    role="admin",
)

db.add(admin_user)
db.commit()
db.refresh(admin_user)

print("Admin created:", admin_user.email)