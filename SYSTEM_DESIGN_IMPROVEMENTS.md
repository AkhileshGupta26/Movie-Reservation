# 🎬 Movie Reservation System - Design Improvements & Best Practices

**Current Tech Stack:**
- FastAPI (Python backend)
- React + TypeScript (Frontend)
- SQLAlchemy ORM
- PostgreSQL/SQLite (Database)
- Redis (Session/seat management)

---

## 📋 Executive Summary

Your system is **structurally sound** but needs improvements in:
1. **Role-based access control (RBAC)** - No actual role enforcement
2. **Database schema** - Missing constraints, audit trails, and optimizations
3. **API structure** - Unclear separation of concerns, no versioning
4. **Error handling** - Inconsistent validation and error responses
5. **Security** - No permission checks on admin endpoints, token validation incomplete
6. **Modularity** - Dependencies mixed, hard to scale

---

## 🔐 1. AUTHENTICATION & ROLE SEPARATION

### Current Issues ❌
- `role` field exists but **never validated**
- Admin endpoints have **no permission checks**
- Mixed auth logic - no dependency injection pattern
- User ID often hardcoded as `None` in hold_seats
- No role hierarchy (admin > staff > user)

### Improvements ✅

#### A. Create Role-Based Dependencies

**File: `app/deps.py` (update)**

```python
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .config import settings
from .schemas import UserOut

def get_current_user(token: str = Header(None), db: Session = Depends(get_db)) -> User:
    """Extract user from JWT token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id: int = int(payload.get("sub"))
        token_type: str = payload.get("type", "access")
        
        if token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_user_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow both regular users and admins."""
    return current_user
```

#### B. Update Signup/Login for Separate Admin/User Flows

**File: `app/schemas.py` (add)**

```python
class AdminSignup(BaseModel):
    """Admin registration requires secret key"""
    name: str
    email: EmailStr
    password: str
    admin_secret: str  # Prevent unauthorized admin creation


class UserSignup(BaseModel):
    """Regular user registration"""
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Unified login for both roles"""
    email: EmailStr
    password: str
    role: str = "user"  # "user" or "admin"
```

**File: `app/main.py` (update auth endpoints)**

```python
from fastapi import Header

@app.post("/auth/user/signup", response_model=schemas.LoginResponse)
def user_signup(req: schemas.UserSignup, db: Session = Depends(get_db)):
    """User signup - any email can register"""
    existing = crud.get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = crud.create_user(db, req, role="user")
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@app.post("/auth/admin/signup", response_model=schemas.LoginResponse)
def admin_signup(req: schemas.AdminSignup, db: Session = Depends(get_db)):
    """Admin signup - requires secret key from config"""
    if req.admin_secret != settings.ADMIN_REGISTRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    existing = crud.get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = crud.create_user(db, req, role="admin")
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@app.post("/auth/login", response_model=schemas.LoginResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Unified login endpoint for user/admin"""
    user = crud.get_user_by_email(db, req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Optional: enforce role match
    if req.role != user.role:
        raise HTTPException(
            status_code=403,
            detail=f"User has '{user.role}' role, not '{req.role}'"
        )
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }
```

---

## 🗄️ 2. IMPROVED DATABASE SCHEMA

### Current Issues ❌
- No audit trail (created_by, updated_by timestamps)
- Soft deletes not supported
- No constraints on seat uniqueness per auditorium
- Missing fields (ratings, pricing rules, discount codes)
- BookedSeat/Reservation design is redundant
- No status history tracking

### Improved Schema ✅

**File: `app/models.py` (revised)**

```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Numeric, Boolean, UniqueConstraint, Enum, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime

# ============ ENUMS ============
class UserRoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    STAFF = "staff"  # Future: for theater staff


class ReservationStatusEnum(str, enum.Enum):
    HELD = "held"           # Temporarily reserved
    CONFIRMED = "confirmed" # Payment confirmed
    CANCELLED = "cancelled"
    COMPLETED = "completed" # After showtime


class SeatTypeEnum(str, enum.Enum):
    REGULAR = "regular"
    PREMIUM = "premium"
    WHEELCHAIR = "wheelchair"
    COUPLE = "couple"  # For premium seating


# ============ AUDIT MIXIN ============
class AuditMixin:
    """Add to all models for tracking changes"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_deleted = Column(Boolean, default=False)  # Soft delete


# ============ MODELS ============
class User(Base, AuditMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER, nullable=False)
    phone = Column(String(20), nullable=True)  # New: contact info
    is_active = Column(Boolean, default=True)  # New: for deactivation
    
    # Relationships
    reservations = relationship('Reservation', back_populates='user')
    audits = relationship('AuditLog', back_populates='user')
    
    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
    )


class Movie(Base, AuditMixin):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=120)
    poster_url = Column(String, nullable=True)
    genre = Column(String(100), nullable=True)
    language = Column(String(50), nullable=True)  # New
    rating = Column(Numeric(3, 1), nullable=True)  # 1-10
    release_date = Column(DateTime(timezone=True), nullable=True)  # New
    
    # Relationships
    showtimes = relationship('Showtime', back_populates='movie', cascade='all, delete-orphan')


class Auditorium(Base, AuditMixin):
    __tablename__ = 'auditoriums'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    capacity = Column(Integer, nullable=False)
    total_rows = Column(Integer, nullable=False)  # New
    seats_per_row = Column(Integer, nullable=False)  # New
    amenities = Column(Text, nullable=True)  # JSON: projector, sound system, etc.
    
    # Relationships
    seats = relationship('Seat', back_populates='auditorium', cascade='all, delete-orphan')
    showtimes = relationship('Showtime', back_populates='auditorium', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('capacity > 0', name='ck_auditorium_capacity_positive'),
    )


class Seat(Base, AuditMixin):
    __tablename__ = 'seats'
    id = Column(Integer, primary_key=True, index=True)
    auditorium_id = Column(Integer, ForeignKey('auditoriums.id', ondelete='CASCADE'), nullable=False)
    row_label = Column(String(10), nullable=False)
    seat_number = Column(Integer, nullable=False)
    seat_type = Column(Enum(SeatTypeEnum), default=SeatTypeEnum.REGULAR, nullable=False)
    price_modifier = Column(Numeric(5, 2), default=0)  # Premium seat surcharge
    is_active = Column(Boolean, default=True)  # New: deactivate broken seats
    
    # Relationships
    auditorium = relationship('Auditorium', back_populates='seats')
    reservations = relationship('ReservationSeat', back_populates='seat', cascade='all, delete-orphan')
    
    __table_args__ = (
        UniqueConstraint('auditorium_id', 'row_label', 'seat_number', name='uq_seat_position'),
        CheckConstraint('seat_number > 0', name='ck_seat_number_positive'),
    )


class Showtime(Base, AuditMixin):
    __tablename__ = 'showtimes'
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    auditorium_id = Column(Integer, ForeignKey('auditoriums.id', ondelete='CASCADE'), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    available_seats = Column(Integer, nullable=False)  # Cache: for performance
    is_cancelled = Column(Boolean, default=False)  # New
    
    # Relationships
    movie = relationship('Movie', back_populates='showtimes')
    auditorium = relationship('Auditorium', back_populates='showtimes')
    reservations = relationship('Reservation', back_populates='showtime', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('base_price > 0', name='ck_showtime_price_positive'),
        CheckConstraint('ends_at > starts_at', name='ck_showtime_duration'),
    )


class Reservation(Base, AuditMixin):
    """Master reservation record - replaces complex hold/booked logic"""
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    showtime_id = Column(Integer, ForeignKey('showtimes.id', ondelete='CASCADE'), nullable=False)
    status = Column(Enum(ReservationStatusEnum), default=ReservationStatusEnum.HELD, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Holds & expiry
    hold_expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL = confirmed
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # New: Payment tracking
    payment_method = Column(String(50), nullable=True)  # card, wallet, etc.
    payment_id = Column(String(255), nullable=True)  # External payment gateway ID
    
    # Relationships
    user = relationship('User', back_populates='reservations')
    showtime = relationship('Showtime', back_populates='reservations')
    seats = relationship('ReservationSeat', back_populates='reservation', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('total_price >= 0', name='ck_reservation_price_positive'),
    )


class ReservationSeat(Base):
    """Maps seats to reservations - single source of truth"""
    __tablename__ = 'reservation_seats'
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False)
    seat_id = Column(Integer, ForeignKey('seats.id', ondelete='CASCADE'), nullable=False)
    price_at_booking = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    reservation = relationship('Reservation', back_populates='seats')
    seat = relationship('Seat', back_populates='reservations')
    
    __table_args__ = (
        UniqueConstraint('reservation_id', 'seat_id', name='uq_reservation_seat'),
    )


# REMOVED: BookedSeat (use ReservationSeat with status=confirmed)


class AuditLog(Base):
    """Track all changes for compliance & debugging"""
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    entity_type = Column(String(50), nullable=False)  # Movie, Showtime, etc.
    entity_id = Column(Integer, nullable=False)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship('User', back_populates='audits')


class PricingRule(Base):
    """Future: Dynamic pricing, discounts, surge pricing"""
    __tablename__ = 'pricing_rules'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # early_bird, weekend_surge, etc.
    discount_percent = Column(Numeric(5, 2), nullable=True)
    applies_to_seat_types = Column(String, nullable=True)  # JSON array
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
```

---

## 🛣️ 3. IMPROVED API STRUCTURE & VERSIONING

### Current Issues ❌
- All endpoints at root level - hard to organize
- No API versioning
- Admin endpoints scattered without prefix
- No clear endpoint grouping

### Structure ✅

**New folder structure:**

```
app/
├── main.py                    # App initialization only
├── config.py
├── database.py
├── models.py                  # All ORM models
├── schemas.py                 # All Pydantic schemas
├── deps.py                    # Dependencies & auth
├── utils.py                   # Helper functions
├── exceptions.py              # Custom exceptions
│
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py          # Router registration
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py      # /api/v1/auth/*
│   │   │   └── service.py     # Business logic
│   │   │
│   │   ├── movies/
│   │   │   ├── __init__.py
│   │   │   ├── user_routes.py # /api/v1/movies/* (user)
│   │   │   ├── admin_routes.py # /api/v1/admin/movies/* (admin)
│   │   │   └── service.py
│   │   │
│   │   ├── showtimes/
│   │   │   ├── __init__.py
│   │   │   ├── user_routes.py
│   │   │   ├── admin_routes.py
│   │   │   └── service.py
│   │   │
│   │   ├── bookings/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py      # /api/v1/bookings/*
│   │   │   └── service.py
│   │   │
│   │   └── admin/
│   │       ├── __init__.py
│   │       ├── routes.py      # /api/v1/admin/* (dashboard)
│   │       └── service.py
│   │
│   └── v2/ (future)
│
├── crud/
│   ├── __init__.py
│   ├── base.py                # Base CRUD operations
│   ├── users.py
│   ├── movies.py
│   ├── showtimes.py
│   ├── reservations.py
│   └── seats.py
│
├── services/
│   ├── __init__.py
│   ├── booking_service.py     # Orchestrates booking logic
│   ├── pricing_service.py     # Calculate prices
│   ├── notification_service.py # Email/SMS
│   └── payment_service.py     # Payment integration
│
└── redis_client.py
```

**File: `app/api/v1/router.py` (new)**

```python
from fastapi import APIRouter
from . import auth, movies, showtimes, bookings, admin

def create_v1_router():
    router = APIRouter(prefix="/api/v1")
    
    # Auth routes
    router.include_router(auth.router, tags=["Authentication"])
    
    # User routes
    router.include_router(movies.user_router, tags=["Movies"])
    router.include_router(showtimes.user_router, tags=["Showtimes"])
    router.include_router(bookings.router, tags=["Bookings"])
    
    # Admin routes
    router.include_router(movies.admin_router, tags=["Admin - Movies"])
    router.include_router(showtimes.admin_router, tags=["Admin - Showtimes"])
    router.include_router(admin.router, tags=["Admin - Dashboard"])
    
    return router
```

**File: `app/main.py` (updated)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import create_v1_router
from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Movie Reservation API",
    version="1.0.0",
    description="Full-featured movie booking system"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.6:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(create_v1_router())

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
```

**API Endpoint Structure:**

```
Authentication:
  POST   /api/v1/auth/user/signup
  POST   /api/v1/auth/admin/signup
  POST   /api/v1/auth/login
  POST   /api/v1/auth/refresh
  POST   /api/v1/auth/logout

User - Movies:
  GET    /api/v1/movies
  GET    /api/v1/movies/{id}
  GET    /api/v1/movies/search?title=...

User - Showtimes:
  GET    /api/v1/showtimes
  GET    /api/v1/showtimes/{id}/seats
  GET    /api/v1/showtimes/movie/{movie_id}

User - Bookings:
  POST   /api/v1/bookings/hold
  POST   /api/v1/bookings/{id}/confirm
  POST   /api/v1/bookings/{id}/cancel
  GET    /api/v1/bookings/my
  GET    /api/v1/bookings/{id}

Admin - Movies:
  POST   /api/v1/admin/movies
  GET    /api/v1/admin/movies
  PUT    /api/v1/admin/movies/{id}
  DELETE /api/v1/admin/movies/{id}

Admin - Showtimes:
  POST   /api/v1/admin/showtimes
  GET    /api/v1/admin/showtimes
  PUT    /api/v1/admin/showtimes/{id}
  DELETE /api/v1/admin/showtimes/{id}

Admin - Auditoriums:
  POST   /api/v1/admin/auditoriums
  GET    /api/v1/admin/auditoriums
  PUT    /api/v1/admin/auditoriums/{id}
  DELETE /api/v1/admin/auditoriums/{id}

Admin - Seats:
  POST   /api/v1/admin/auditoriums/{id}/seats/batch
  GET    /api/v1/admin/auditoriums/{id}/seats
  PUT    /api/v1/admin/seats/{id}
  DELETE /api/v1/admin/seats/{id}

Admin - Bookings:
  GET    /api/v1/admin/bookings
  GET    /api/v1/admin/bookings/{id}
  GET    /api/v1/admin/reports/revenue
  GET    /api/v1/admin/reports/occupancy
```

---

## 🛡️ 4. ERROR HANDLING & VALIDATION PATTERNS

### Create Custom Exceptions

**File: `app/exceptions.py` (new)**

```python
from fastapi import HTTPException, status

class APIException(HTTPException):
    """Base API exception"""
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class ValidationException(APIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class UnauthorizedException(APIException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(APIException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(APIException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            detail=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(APIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


# Specific exceptions
class SeatAlreadyBookedException(ConflictException):
    def __init__(self):
        super().__init__("Seat(s) already booked")


class SeatAlreadyHeldException(ConflictException):
    def __init__(self):
        super().__init__("Seat(s) already held by another user")


class ShowtimeOverlapException(ValidationException):
    def __init__(self):
        super().__init__("Showtime overlaps with existing schedule")


class HoldExpiredException(ConflictException):
    def __init__(self):
        super().__init__("Hold expired. Please select seats again")
```

### Improved Validation

**File: `app/schemas.py` (add)**

```python
from pydantic import BaseModel, Field, validator, root_validator

class HoldSeatsRequest(BaseModel):
    seat_ids: list[int] = Field(..., min_items=1, max_items=20)
    
    @validator("seat_ids")
    def validate_seat_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate seat IDs")
        if any(sid < 1 for sid in v):
            raise ValueError("Invalid seat IDs")
        return v


class ShowtimeCreate(BaseModel):
    movie_id: int = Field(..., gt=0)
    auditorium_id: int = Field(..., gt=0)
    starts_at: datetime
    ends_at: datetime
    base_price: Decimal = Field(..., gt=0, decimal_places=2)
    
    @root_validator
    def validate_times(cls, values):
        if values.get("ends_at") <= values.get("starts_at"):
            raise ValueError("Showtime end must be after start")
        return values
```

---

## 🔒 5. SECURITY & AUTHORIZATION BEST PRACTICES

### A. Token Management

```python
# File: app/auth.py (enhanced)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    to_encode.update({
        "type": "access",
        "iat": datetime.now(timezone.utc),  # Issued at
    })
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    to_encode.update({
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    })
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt
```

### B. Permission Checks in CRUD

```python
# File: app/crud/movies.py (example)

def update_movie(db: Session, movie_id: int, movie_in, current_user: User):
    """Only admin can update"""
    if current_user.role != "admin":
        raise ForbiddenException("Only admins can update movies")
    
    movie = db.query(Movie).filter(Movie.id == movie_id, Movie.is_deleted == False).first()
    if not movie:
        raise NotFoundException("Movie")
    
    # ... update logic
```

### C. Rate Limiting

```python
# File: app/main.py

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )

# Apply to sensitive endpoints
@app.post("/auth/login")
@limiter.limit("5/minute")
def login(...):
    pass
```

---

## 📦 6. SERVICE LAYER & BUSINESS LOGIC SEPARATION

**File: `app/services/booking_service.py` (new)**

```python
from sqlalchemy.orm import Session
from ..models import Reservation, ReservationSeat, Seat, BookedSeat, User, Showtime
from ..exceptions import *
from ..redis_client import redis_client
from datetime import datetime, timedelta
from ..config import settings

class BookingService:
    @staticmethod
    def hold_seats(
        user: User,
        showtime_id: int,
        seat_ids: list[int],
        db: Session
    ) -> dict:
        """Hold seats for user with transaction safety"""
        
        # Validate seats exist
        seats = db.query(Seat).filter(Seat.id.in_(seat_ids)).all()
        if len(seats) != len(seat_ids):
            raise NotFoundException("Seat")
        
        # Check conflicts
        booked_seats = db.query(ReservationSeat).filter(
            ReservationSeat.seat_id.in_(seat_ids),
            Reservation.showtime_id == showtime_id,
            Reservation.status.in_(["held", "confirmed"])
        ).all()
        
        if booked_seats:
            raise SeatAlreadyBookedException()
        
        # Check Redis holds
        if redis_client:
            for sid in seat_ids:
                if redis_client.get(f"hold:{showtime_id}:{sid}"):
                    raise SeatAlreadyHeldException()
        
        # Get showtime for pricing
        showtime = db.query(Showtime).filter(Showtime.id == showtime_id).first()
        if not showtime:
            raise NotFoundException("Showtime")
        
        # Calculate total price
        total_price = sum(
            showtime.base_price + s.price_modifier for s in seats
        )
        
        # Create reservation
        reservation = Reservation(
            user_id=user.id,
            showtime_id=showtime_id,
            status="held",
            total_price=total_price,
            hold_expires_at=datetime.utcnow() + timedelta(
                seconds=settings.HOLD_TTL_SECONDS
            )
        )
        db.add(reservation)
        db.flush()  # Get ID without committing
        
        # Add seats
        for seat in seats:
            res_seat = ReservationSeat(
                reservation_id=reservation.id,
                seat_id=seat.id,
                price_at_booking=showtime.base_price + seat.price_modifier
            )
            db.add(res_seat)
        
        db.commit()
        
        # Set Redis holds
        if redis_client:
            for sid in seat_ids:
                redis_client.setex(
                    f"hold:{showtime_id}:{sid}",
                    settings.HOLD_TTL_SECONDS,
                    reservation.id
                )
        
        return {
            "reservation_id": reservation.id,
            "expires_at": reservation.hold_expires_at,
            "total_price": float(total_price)
        }
    
    @staticmethod
    def confirm_booking(reservation_id: int, user: User, db: Session) -> dict:
        """Confirm held reservation"""
        
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id,
            Reservation.user_id == user.id,
            Reservation.status == "held"
        ).first()
        
        if not reservation:
            raise NotFoundException("Reservation")
        
        # Check expiry
        if datetime.utcnow() > reservation.hold_expires_at:
            raise HoldExpiredException()
        
        # Atomic update
        reservation.status = "confirmed"
        reservation.confirmed_at = datetime.utcnow()
        db.commit()
        
        # Clear Redis holds
        if redis_client:
            pattern = f"hold:{reservation.showtime_id}:*"
            keys = redis_client.keys(pattern)
            for key in keys:
                if redis_client.get(key) == str(reservation_id):
                    redis_client.delete(key)
        
        return {"status": "confirmed", "reservation_id": reservation_id}
```

---

## 🏗️ 7. REFACTORING CHECKLIST

### Phase 1: Core Changes (Foundation)
- [ ] Create `app/exceptions.py` with custom exceptions
- [ ] Update `app/auth.py` with token type tracking
- [ ] Create `app/deps.py` with dependency injection
- [ ] Update `app/models.py` with new schema (audit trail, enums, etc.)
- [ ] Update database with migrations (Alembic)

### Phase 2: Service Layer
- [ ] Create `app/services/booking_service.py`
- [ ] Create `app/services/pricing_service.py`
- [ ] Create `app/crud/base.py` with generic CRUD
- [ ] Refactor existing CRUD functions

### Phase 3: API Reorganization
- [ ] Create `app/api/v1/` folder structure
- [ ] Create `app/api/v1/auth/routes.py`
- [ ] Create `app/api/v1/movies/user_routes.py` and `admin_routes.py`
- [ ] Create `app/api/v1/router.py`
- [ ] Update `app/main.py` to use new router

### Phase 4: Frontend Updates
- [ ] Add separate login flows for user/admin
- [ ] Update auth store to handle role selection
- [ ] Create admin-specific pages/components
- [ ] Add role-based route protection

### Phase 5: Testing & Documentation
- [ ] Write unit tests for services
- [ ] Write integration tests for endpoints
- [ ] Update Swagger documentation
- [ ] Create API documentation

---

## 📊 8. MISSING FEATURES TO ADD

### Priority: HIGH
- [ ] **Email Notifications** - Booking confirmation, hold expiry alerts
- [ ] **Payment Integration** - Stripe/Razorpay integration
- [ ] **Booking History** - Users can view past bookings
- [ ] **Cancellation** - Allow users to cancel reservations
- [ ] **Refunds** - Handle refund logic
- [ ] **Multi-seat Booking** - Better UX for group bookings

### Priority: MEDIUM
- [ ] **Search & Filters** - By genre, language, rating, location
- [ ] **Wishlist** - Save movies for later
- [ ] **Reviews & Ratings** - User reviews on movies
- [ ] **Promotional Codes** - Discount code support
- [ ] **Recurring Bookings** - Season pass / subscription
- [ ] **Analytics Dashboard** - Admin revenue/occupancy reports

### Priority: LOW
- [ ] **Push Notifications** - Real-time updates
- [ ] **Social Sharing** - Share bookings on social media
- [ ] **Seat Recommendations** - ML-based seat suggestions
- [ ] **Dynamic Pricing** - Surge pricing for peak times
- [ ] **Multi-language Support** - i18n

---

## 🚀 9. IMPLEMENTATION ROADMAP

### Week 1: Database & Models
```bash
1. Update models.py with new schema
2. Create Alembic migration
3. Run migration on test DB
```

### Week 2: Auth & Permissions
```bash
1. Create deps.py with role-based dependencies
2. Update auth.py with better token handling
3. Create separate signup endpoints
4. Test auth flow end-to-end
```

### Week 3: Service Layer
```bash
1. Create services/ folder
2. Move booking logic to BookingService
3. Create PricingService for dynamic pricing
4. Write unit tests
```

### Week 4: API Reorganization
```bash
1. Create api/v1/ folder structure
2. Split routes by resource
3. Update main.py
4. Test all endpoints
```

### Week 5: Frontend Integration
```bash
1. Update login flow for role selection
2. Create admin pages
3. Update booking flow
4. Test role-based access
```

---

## 📝 SUMMARY: Key Takeaways

| Area | Current | Improved |
|------|---------|----------|
| **Auth** | Single flow, no role checks | Separate user/admin flows, RBAC enforced |
| **Database** | Basic fields | Audit trail, enums, constraints, soft deletes |
| **API** | Flat structure | Versioned, modular by resource |
| **Errors** | Generic HTTP exceptions | Custom, specific, descriptive |
| **Security** | Token extraction basic | Token type tracking, rate limiting |
| **Organization** | Mixed concerns | Service layer + repository pattern |
| **Scalability** | Hard to extend | Easy to add features via services |

---

## 🔄 Next Steps

1. **Review** this document with your team
2. **Choose** which improvements to implement first (suggest: Auth → Service Layer → API Reorganization)
3. **Start** with Phase 1 (database & models)
4. **Test** each phase before moving to next
5. **Deploy** incrementally with backward compatibility

**Questions? Let me implement any specific changes you'd like!**
