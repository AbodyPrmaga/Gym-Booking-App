# app/core/test.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.db import get_db
from app.db.models import Base, User, Service, Trainer, TimeSlot, Booking
from passlib.context import CryptContext

# =========================
# Test Database Setup
# =========================

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Drop all tables and recreate
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# =========================
# Fixtures
# =========================

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up after test
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()

@pytest.fixture
def test_user(db_session):
    """Create a regular test user"""
    hashed_password = pwd_context.hash("testpass123")
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hashed_password,
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin(db_session):
    """Create an admin test user"""
    hashed_password = pwd_context.hash("adminpass123")
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=hashed_password,
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture
def test_trainer(db_session):
    """Create a test trainer"""
    trainer = Trainer(
        name="John Trainer",
        bio="Professional fitness trainer with 10 years experience"
    )
    db_session.add(trainer)
    db_session.commit()
    db_session.refresh(trainer)
    return trainer

@pytest.fixture
def test_service(db_session):
    """Create a test service"""
    service = Service(
        name="Yoga Class",
        description="Relaxing yoga session",
        duration_minutes=60,
        capacity=10,
        price=500,
        is_active=True
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service

@pytest.fixture
def test_slot(db_session, test_service, test_trainer):
    """Create a test time slot"""
    slot = TimeSlot(
        service_id=test_service.id,
        trainer_id=test_trainer.id,
        start_time=datetime.utcnow() + timedelta(days=1, hours=10),
        end_time=datetime.utcnow() + timedelta(days=1, hours=11),
        capacity=10
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    return slot

# =========================
# Helper Functions
# =========================

def get_auth_header(email: str, password: str):
    """Get authorization header for authenticated requests"""
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return None

# =========================
# Authentication Tests
# =========================

class TestAuthentication:
    
    def test_register_success(self, db_session):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 201
        assert response.json()["msg"] == "User Created"
        assert "user_id" in response.json()
    
    def test_register_duplicate_email(self, test_user):
        """Test registration with existing email"""
        response = client.post(
            "/auth/register",
            json={
                "name": "Another User",
                "email": test_user.email,
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_password_too_long(self):
        """Test registration with password exceeding 72 chars"""
        long_password = "a" * 73
        response = client.post(
            "/auth/register",
            json={
                "name": "Long Pass User",
                "email": "longpass@example.com",
                "password": long_password
            }
        )
        assert response.status_code == 400
        assert "Password too long" in response.json()["detail"]
    
    def test_login_success(self, test_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_inactive_user(self, db_session):
        """Test login with inactive user"""
        hashed_password = pwd_context.hash("inactive123")
        user = User(
            name="Inactive User",
            email="inactive@example.com",
            password_hash=hashed_password,
            role="user",
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "inactive123"
            }
        )
        assert response.status_code == 401
    
    def test_about_me_authenticated(self, test_user):
        """Test getting current user info"""
        headers = get_auth_header(test_user.email, "testpass123")
        response = client.get("/auth/about", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["email"] == test_user.email
        assert response.json()["name"] == test_user.name
    
    def test_about_me_unauthenticated(self):
        """Test getting user info without token"""
        response = client.get("/auth/about")
        assert response.status_code == 401

# =========================
# Services Tests
# =========================

class TestServices:
    
    def test_create_service(self, test_admin):
        """Test creating a new service"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        response = client.post(
            "/services/add_service",
            headers=headers,
            json={
                "name": "Pilates",
                "description": "Core strengthening pilates class",
                "duration_minutes": 45,
                "capacity": 15,
                "price": 350.0
            }
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Pilates"
        assert response.json()["price"] == 350.0
    
    def test_get_all_services(self, test_service):
        """Test retrieving all services"""
        response = client.get("/services/")
        
        assert response.status_code == 200
        assert "data" in response.json()
        assert response.json()["total"] >= 1
        assert len(response.json()["data"]) > 0
    
    def test_get_all_services_with_pagination(self, db_session):
        """Test services pagination"""
        # Create multiple services
        for i in range(5):
            service = Service(
                name=f"Service {i}",
                description=f"Description {i}",
                duration_minutes=30,
                capacity=10,
                price=100,
                is_active=True
            )
            db_session.add(service)
        db_session.commit()
        
        response = client.get("/services/?page=1&size=2")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2
        assert response.json()["page"] == 1
        assert response.json()["size"] == 2
    
    def test_get_all_services_with_search(self, test_service):
        """Test searching services"""
        response = client.get(f"/services/?search=Yoga")
        
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 1
        assert response.json()["data"][0]["name"] == "Yoga Class"
    
    def test_get_service_by_id(self, test_service):
        """Test retrieving specific service"""
        response = client.get(f"/services/get_service/{test_service.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == test_service.id
        assert response.json()["name"] == test_service.name
    
    def test_get_nonexistent_service(self):
        """Test retrieving non-existent service"""
        response = client.get("/services/get_service/99999")
        assert response.status_code == 404
    
    def test_update_service(self, test_admin, test_service):
        """Test updating a service"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        response = client.put(
            f"/services/update/{test_service.id}",
            headers=headers,
            json={
                "name": "Advanced Yoga",
                "description": "Updated description",
                "duration_minutes": 90,
                "capacity": 20,
                "price": 750.0
            }
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Advanced Yoga"
        assert response.json()["price"] == 750.0
    
    def test_delete_service(self, test_admin, test_service):
        """Test soft deleting a service"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        response = client.delete(
            f"/services/delete/{test_service.id}",
            headers=headers
        )
        assert response.status_code == 204
        
        # Verify service is inactive
        get_response = client.get(f"/services/get_service/{test_service.id}")
        assert get_response.status_code == 404

# =========================
# Slots Tests
# =========================

class TestSlots:
    
    def test_create_slot(self, test_admin, test_service, test_trainer):
        """Test creating a time slot"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        start_time = datetime.utcnow() + timedelta(days=2, hours=9)
        end_time = start_time + timedelta(hours=1)
        
        response = client.post(
            f"/slots/create_slot?service_id={test_service.id}&start_time={start_time.isoformat()}&end_time={end_time.isoformat()}&capacity=15&trainer_id={test_trainer.id}",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["capacity"] == 15
        assert response.json()["trainer_id"] == test_trainer.id
    
    def test_create_slot_invalid_time_range(self, test_admin, test_service, test_trainer):
        """Test creating slot with invalid time range"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        start_time = datetime.utcnow() + timedelta(days=2, hours=10)
        end_time = start_time - timedelta(hours=1)  # End before start
        
        response = client.post(
            f"/slots/create_slot?service_id={test_service.id}&start_time={start_time.isoformat()}&end_time={end_time.isoformat()}&capacity=10&trainer_id={test_trainer.id}",
            headers=headers
        )
        assert response.status_code == 400
        assert "End time must be after start time" in response.json()["detail"]
    
    def test_create_slot_trainer_conflict(self, test_admin, test_slot, test_service):
        """Test creating overlapping slot for same trainer"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        # Create overlapping time
        start_time = test_slot.start_time + timedelta(minutes=30)
        end_time = test_slot.end_time + timedelta(minutes=30)
        
        response = client.post(
            f"/slots/create_slot?service_id={test_service.id}&start_time={start_time.isoformat()}&end_time={end_time.isoformat()}&capacity=10&trainer_id={test_slot.trainer_id}",
            headers=headers
        )
        assert response.status_code == 409
        assert "Trainer already has a slot" in response.json()["detail"]
    
    def test_get_slots(self, test_slot):
        """Test retrieving all slots"""
        response = client.get("/slots/get_slots")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1
    
    def test_get_slots_with_filters(self, test_slot, test_service):
        """Test retrieving slots with filters"""
        response = client.get(f"/slots/get_slots?service_id={test_service.id}")
        
        assert response.status_code == 200
        assert all(slot["service_id"] == test_service.id for slot in response.json())
    
    def test_get_slot_by_id(self, test_slot):
        """Test retrieving specific slot"""
        response = client.get(f"/slots/get_slot/{test_slot.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == test_slot.id
        assert "remaining_capacity" in response.json()
        assert "current_bookings" in response.json()
    
    def test_update_slot(self, test_admin, test_slot):
        """Test updating a slot"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        new_start = test_slot.start_time + timedelta(hours=2)
        new_end = test_slot.end_time + timedelta(hours=2)
        
        response = client.patch(
            f"/slots/update/{test_slot.id}?start_time={new_start.isoformat()}&end_time={new_end.isoformat()}&capacity=20",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["capacity"] == 20
    
    def test_delete_slot_no_bookings(self, test_admin, test_slot):
        """Test deleting slot with no bookings"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        response = client.delete(
            f"/slots/delete/{test_slot.id}",
            headers=headers
        )
        assert response.status_code == 200
        assert "Slot deleted successfully" in response.json()["message"]
    
    def test_delete_slot_with_bookings(self, test_admin, test_slot, test_user, db_session):
        """Test cannot delete slot with existing bookings"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        # Create a booking first
        booking = Booking(
            user_id=test_user.id,
            slot_id=test_slot.id,
            status="confirmed"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.delete(
            f"/slots/delete/{test_slot.id}",
            headers=headers
        )
        assert response.status_code == 400
        assert "Cannot delete slot with existing bookings" in response.json()["detail"]

# =========================
# Bookings Tests
# =========================

class TestBookings:
    
    def test_create_booking(self, test_user, test_slot):
        """Test creating a booking"""
        headers = get_auth_header(test_user.email, "testpass123")
        
        response = client.post(
            f"/booking/book?user_id={test_user.id}&slot_id={test_slot.id}",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"
        assert response.json()["user_id"] == test_user.id
    
    def test_create_duplicate_booking(self, test_user, test_slot, db_session):
        """Test cannot create duplicate booking"""
        headers = get_auth_header(test_user.email, "testpass123")
        
        # First booking
        client.post(
            f"/booking/book?user_id={test_user.id}&slot_id={test_slot.id}",
            headers=headers
        )
        
        # Duplicate booking
        response = client.post(
            f"/booking/book?user_id={test_user.id}&slot_id={test_slot.id}",
            headers=headers
        )
        assert response.status_code == 409
        assert "Booking already exists" in response.json()["detail"]
    
    def test_create_booking_full_capacity(self, test_slot, db_session):
        """Test cannot book when slot is full"""
        # Create users and fill capacity
        for i in range(test_slot.capacity):
            hashed_password = pwd_context.hash(f"pass{i}")
            user = User(
                name=f"User {i}",
                email=f"user{i}@test.com",
                password_hash=hashed_password,
                role="user",
                is_active=True
            )
            db_session.add(user)
            db_session.flush()
            
            booking = Booking(
                user_id=user.id,
                slot_id=test_slot.id,
                status="confirmed"
            )
            db_session.add(booking)
        db_session.commit()
        
        # Create one more user for failed booking
        hashed_password = pwd_context.hash("extrapass")
        extra_user = User(
            name="Extra User",
            email="extra@test.com",
            password_hash=hashed_password,
            role="user",
            is_active=True
        )
        db_session.add(extra_user)
        db_session.commit()
        
        headers = get_auth_header(extra_user.email, "extrapass")
        response = client.post(
            f"/booking/book?user_id={extra_user.id}&slot_id={test_slot.id}",
            headers=headers
        )
        assert response.status_code == 400
        assert "Slot is fully booked" in response.json()["detail"]
    
    def test_create_booking_past_slot(self, test_user, db_session, test_service, test_trainer):
        """Test cannot book past time slot"""
        # Create past slot
        past_slot = TimeSlot(
            service_id=test_service.id,
            trainer_id=test_trainer.id,
            start_time=datetime.utcnow() - timedelta(hours=2),
            end_time=datetime.utcnow() - timedelta(hours=1),
            capacity=10
        )
        db_session.add(past_slot)
        db_session.commit()
        
        headers = get_auth_header(test_user.email, "testpass123")
        response = client.post(
            f"/booking/book?user_id={test_user.id}&slot_id={past_slot.id}",
            headers=headers
        )
        assert response.status_code == 400
        assert "Slot already passed" in response.json()["detail"]
    
    def test_get_all_bookings(self, test_user, test_slot, db_session):
        """Test retrieving all bookings"""
        # Create a booking first
        booking = Booking(
            user_id=test_user.id,
            slot_id=test_slot.id,
            status="confirmed"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.get("/booking/bookings")
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_get_bookings_with_filters(self, test_user, test_slot, db_session):
        """Test retrieving bookings with filters"""
        # Create bookings
        booking1 = Booking(user_id=test_user.id, slot_id=test_slot.id, status="confirmed")
        booking2 = Booking(user_id=test_user.id, slot_id=test_slot.id, status="cancelled")
        db_session.add_all([booking1, booking2])
        db_session.commit()
        
        # Filter by status
        response = client.get("/booking/bookings?status=confirmed")
        assert response.status_code == 200
        assert all(b["status"] == "confirmed" for b in response.json())
        
        # Filter by user
        response = client.get(f"/booking/bookings?user_id={test_user.id}")
        assert response.status_code == 200
        assert all(b["user_id"] == test_user.id for b in response.json())
    
    def test_cancel_booking(self, test_user, test_slot, db_session):
        """Test cancelling a booking"""
        headers = get_auth_header(test_user.email, "testpass123")
        
        # Create booking
        booking = Booking(
            user_id=test_user.id,
            slot_id=test_slot.id,
            status="confirmed"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.put(
            f"/booking/{booking.id}/cancel",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    def test_cancel_already_cancelled_booking(self, test_user, test_slot, db_session):
        """Test cannot cancel already cancelled booking"""
        headers = get_auth_header(test_user.email, "testpass123")
        
        # Create cancelled booking
        booking = Booking(
            user_id=test_user.id,
            slot_id=test_slot.id,
            status="cancelled"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.put(
            f"/booking/{booking.id}/cancel",
            headers=headers
        )
        assert response.status_code == 400
        assert "Already cancelled" in response.json()["detail"]
    
    def test_confirm_booking(self, test_admin, test_user, test_slot, db_session):
        """Test confirming a booking"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        # Create booking
        booking = Booking(
            user_id=test_user.id,
            slot_id=test_slot.id,
            status="cancelled"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.put(
            f"/booking/{booking.id}/confirm",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

# =========================
# Users Tests (Admin Only)
# =========================

class TestUsers:
    
    def test_get_all_users_admin(self, test_admin, test_user):
        """Test admin can get all users"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        response = client.get("/users/", headers=headers)
        assert response.status_code == 200
        assert "data" in response.json()
        assert len(response.json()["data"]) >= 1
    
    def test_get_all_users_unauthorized(self, test_user):
        """Test regular user cannot access users list"""
        headers = get_auth_header(test_user.email, "testpass123")
        
        response = client.get("/users/", headers=headers)
        assert response.status_code == 403
    
    def test_get_users_pagination(self, test_admin, db_session):
        """Test users list pagination"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        # Create multiple users
        for i in range(5):
            hashed_password = pwd_context.hash(f"pass{i}")
            user = User(
                name=f"Pagination User {i}",
                email=f"pagination{i}@test.com",
                password_hash=hashed_password,
                role="user",
                is_active=True
            )
            db_session.add(user)
        db_session.commit()
        
        response = client.get("/users/?page=1&size=2", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) <= 2
    
    def test_get_users_search(self, test_admin, test_user):
        """Test searching users"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        response = client.get(f"/users/?search={test_user.name}", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 1
        assert response.json()["data"][0]["name"] == test_user.name
    
    def test_get_users_filter_active(self, test_admin, db_session):
        """Test filtering users by active status"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        # Create inactive user
        hashed_password = pwd_context.hash("inactivepass")
        inactive_user = User(
            name="Inactive Test",
            email="inactive_filter@test.com",
            password_hash=hashed_password,
            role="user",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        response = client.get("/users/?is_active=false", headers=headers)
        assert response.status_code == 200
        assert all(not u["is_active"] for u in response.json()["data"])
    
    def test_get_single_user(self, test_admin, test_user):
        """Test getting specific user"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        response = client.get(f"/users/{test_user.id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == test_user.id
        assert response.json()["email"] == test_user.email
    
    def test_update_user(self, test_admin, test_user):
        """Test updating user information"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        response = client.patch(
            f"/users/update/{test_user.id}",
            headers=headers,
            json={
                "name": "Updated Name",
                "is_active": True
            }
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
    
    def test_update_user_password(self, test_admin, test_user):
        """Test updating user password"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        response = client.patch(
            f"/users/update/{test_user.id}",
            headers=headers,
            json={
                "password": "NewSecurePass123"
            }
        )
        assert response.status_code == 200
        
        # Verify can login with new password
        login_response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "NewSecurePass123"
            }
        )
        assert login_response.status_code == 200
    
    def test_delete_user(self, test_admin, test_user):
        """Test soft deleting a user"""
        headers = get_auth_header(test_admin.email, "adminpass123")
        
        response = client.delete(
            f"/users/delete/{test_user.id}",
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify user is inactive
        get_response = client.get(f"/users/{test_user.id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] == False

# =========================
# Integration Tests
# =========================

class TestIntegration:
    
    def test_complete_booking_flow(self, test_user, test_service, test_trainer, test_admin):
        """Test complete flow: create slot -> book -> cancel"""
        admin_headers = get_auth_header(test_admin.email, "adminpass123")
        user_headers = get_auth_header(test_user.email, "testpass123")
        
        # 1. Admin creates slot
        start_time = datetime.utcnow() + timedelta(days=3, hours=14)
        end_time = start_time + timedelta(hours=1)
        
        slot_response = client.post(
            f"/slots/create_slot?service_id={test_service.id}&start_time={start_time.isoformat()}&end_time={end_time.isoformat()}&capacity=5&trainer_id={test_trainer.id}",
            headers=admin_headers
        )
        assert slot_response.status_code == 200
        slot_id = slot_response.json()["id"]
        
        # 2. User books slot
        book_response = client.post(
            f"/booking/book?user_id={test_user.id}&slot_id={slot_id}",
            headers=user_headers
        )
        assert book_response.status_code == 200
        booking_id = book_response.json()["id"]
        assert book_response.json()["status"] == "confirmed"
        
        # 3. Check slot capacity decreased
        slot_info = client.get(f"/slots/get_slot/{slot_id}")
        assert slot_info.status_code == 200
        assert slot_info.json()["current_bookings"] == 1
        assert slot_info.json()["remaining_capacity"] == 4
        
        # 4. User cancels booking
        cancel_response = client.put(
            f"/booking/{booking_id}/cancel",
            headers=user_headers
        )
        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelled"
        
        # 5. Verify capacity restored
        final_slot_info = client.get(f"/slots/get_slot/{slot_id}")
        assert final_slot_info.json()["current_bookings"] == 0
        assert final_slot_info.json()["remaining_capacity"] == 5
    
    def test_admin_user_management_flow(self, test_admin):
        """Test complete user management flow by admin"""
        admin_headers = get_auth_header(test_admin.email, "adminpass123")
        
        # 1. Create new user
        register_response = client.post(
            "/auth/register",
            json={
                "name": "Flow Test User",
                "email": "flowtest@example.com",
                "password": "FlowPass123"
            }
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["user_id"]
        
        # 2. Admin views user
        get_response = client.get(f"/users/{user_id}", headers=admin_headers)
        assert get_response.status_code == 200
        assert get_response.json()["email"] == "flowtest@example.com"
        
        # 3. Admin updates user
        update_response = client.patch(
            f"/users/update/{user_id}",
            headers=admin_headers,
            json={"name": "Updated Flow User"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Flow User"
        
        # 4. Admin deactivates user
        delete_response = client.delete(
            f"/users/delete/{user_id}",
            headers=admin_headers
        )
        assert delete_response.status_code == 200
        
        # 5. Verify user cannot login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "flowtest@example.com",
                "password": "FlowPass123"
            }
        )
        assert login_response.status_code == 401

# =========================
# Run tests with: pytest app/core/test.py -v
# =========================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])