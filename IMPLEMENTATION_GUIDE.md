# 🔧 STEP-BY-STEP IMPLEMENTATION GUIDE

## Quick Reference for Implementing Improvements

---

## STEP 1: Add Dependencies to requirements.txt

```bash
# Add these to requirements.txt
slowapi>=0.1.9          # Rate limiting
python-jose[cryptography]>=3.3.0  # Already there, confirm version
PyJWT>=2.8.0            # JWT handling
python-multipart>=0.0.5 # Form data
```

---

## STEP 2: Create Custom Exceptions Module

**File: `app/exceptions.py`**

```python
from fastapi import HTTPException, status
from typing import Optional

class APIException(HTTPException):
    """Base API exception with custom detail"""
    def __init__(
        self,
        detail: str,
        status_code: int = 400,
        headers: Optional[dict] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )


class ValidationException(APIException):
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class UnauthorizedException(APIException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(APIException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(APIException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            detail=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(APIException):
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT
        )


# Specific booking exceptions
class SeatAlreadyBookedException(ConflictException):
    def __init__(self):
        super().__init__("One or more seats are already booked")


class SeatAlreadyHeldException(ConflictException):
    def __init__(self):
        super().__init__("One or more seats are held by another user")


class ShowtimeOverlapException(ValidationException):
    def __init__(self):
        super().__init__("Showtime overlaps with existing schedule in same auditorium")


class HoldExpiredException(ConflictException):
    def __init__(self):
        super().__init__("Hold period expired. Please select seats again")


class PaymentException(APIException):
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_402_PAYMENT_REQUIRED
        )
```

---

## STEP 3: Create Enhanced Dependencies Module

**File: `app/deps.py` (NEW - or update if exists)**

```python
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Optional
from .database import get_db
from .models import User, UserRoleEnum
from .config import settings
from .exceptions import UnauthorizedException, ForbiddenException

security = HTTPBearer()

def get_token_from_header(credentials: Optional[HTTPAuthCredentials] = Depends(security)) -> str:
    """Extract token from Authorization header"""
    if credentials is None:
        raise UnauthorizedException("Missing authorization header")
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user.
    Raises 401 if token invalid or user not found.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id: int = int(payload.get("sub"))
        token_type: str = payload.get("type", "access")
        
        # Verify it's an access token, not refresh
        if token_type != "access":
            raise UnauthorizedException("Invalid token type")
    except (JWTError, ValueError) as e:
        raise UnauthorizedException("Invalid or expired token")
    
    user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False,
        User.is_active == True
    ).first()
    
    if not user:
        raise UnauthorizedException("User not found")
    
    return user


def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify user has admin role.
    Raises 403 if not admin.
    """
    if current_user.role != UserRoleEnum.ADMIN:
        raise ForbiddenException("Admin role required")
    return current_user


def get_optional_user(
    token: Optional[str] = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optionally get current user (used for features like wishlist).
    Returns None if no token provided or invalid.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id: int = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None
    except (JWTError, ValueError):
        return None
```

---

## STEP 4: Update Config with New Settings

**File: `app/config.py` (UPDATE)**

```python
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./movie_reservation.db"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Booking
    HOLD_TTL_SECONDS: int = 600  # 10 minutes
    
    # Admin
    ADMIN_REGISTRATION_SECRET: str = os.getenv(
        "ADMIN_REGISTRATION_SECRET",
        "admin-secret-key"
    )
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://192.168.1.6:3000"
    ]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Payment (placeholder)
    PAYMENT_PROVIDER: str = os.getenv("PAYMENT_PROVIDER", "stripe")
    PAYMENT_API_KEY: str = os.getenv("PAYMENT_API_KEY", "")
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## STEP 5: Update Models with New Schema

**File: `app/models.py` (UPDATE - KEY CHANGES)**

> **Instead of rewriting, make these incremental changes:**

### 5A. Add Enums at the top

```python
import enum

class UserRoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    STAFF = "staff"


class ReservationStatusEnum(str, enum.Enum):
    HELD = "held"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SeatTypeEnum(str, enum.Enum):
    REGULAR = "regular"
    PREMIUM = "premium"
    WHEELCHAIR = "wheelchair"
```

### 5B. Update User model

Replace the `role` field:

```python
# OLD:
role = Column(String, default='user')

# NEW:
role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER, nullable=False)
phone = Column(String(20), nullable=True)
is_active = Column(Boolean, default=True)
```

### 5C. Update Reservation model

```python
# Change status field:
# OLD:
status = Column(String, nullable=False)

# NEW:
status = Column(Enum(ReservationStatusEnum), default=ReservationStatusEnum.HELD, nullable=False)

# Add new fields:
hold_expires_at = Column(DateTime(timezone=True), nullable=True)
confirmed_at = Column(DateTime(timezone=True), nullable=True)
payment_method = Column(String(50), nullable=True)
payment_id = Column(String(255), nullable=True)
```

### 5D. Update Seat model

```python
# Change seat_type:
# OLD:
seat_type = Column(String, default='regular')

# NEW:
seat_type = Column(Enum(SeatTypeEnum), default=SeatTypeEnum.REGULAR, nullable=False)

# Add new field:
is_active = Column(Boolean, default=True)
```

### 5E. Add audit fields to all models

```python
from sqlalchemy.sql import func

# Add to User, Movie, Auditorium, Seat, Showtime:
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
is_deleted = Column(Boolean, default=False)
```

---

## STEP 6: Create Booking Service

**File: `app/services/booking_service.py` (NEW)**

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict

from ..models import (
    Reservation,
    ReservationSeat,
    Seat,
    User,
    Showtime,
    ReservationStatusEnum
)
from ..exceptions import (
    SeatAlreadyBookedException,
    SeatAlreadyHeldException,
    NotFoundException,
    HoldExpiredException,
    ConflictException
)
from ..redis_client import redis_client
from ..config import settings


class BookingService:
    
    @staticmethod
    def get_seat_status(showtime_id: int, seat_id: int, db: Session) -> str:
        """
        Check if seat is available, held, or booked.
        Returns: 'available', 'held', 'booked'
        """
        # Check if booked
        booked = db.query(ReservationSeat).join(Reservation).filter(
            Reservation.showtime_id == showtime_id,
            Reservation.status == ReservationStatusEnum.CONFIRMED,
            ReservationSeat.seat_id == seat_id
        ).first()
        
        if booked:
            return "booked"
        
        # Check if held in Redis
        if redis_client:
            held_key = f"hold:{showtime_id}:{seat_id}"
            if redis_client.get(held_key):
                return "held"
        
        return "available"
    
    @staticmethod
    def hold_seats(
        user: User,
        showtime_id: int,
        seat_ids: List[int],
        db: Session
    ) -> Dict:
        """
        Hold seats for user. Creates reservation with hold status.
        
        Returns:
            {
                "reservation_id": int,
                "expires_at": datetime,
                "total_price": float
            }
        
        Raises:
            NotFoundException: If seats or showtime don't exist
            SeatAlreadyBookedException: If any seat is booked
            SeatAlreadyHeldException: If any seat is held
        """
        
        # Validate seats exist
        seats = db.query(Seat).filter(
            Seat.id.in_(seat_ids),
            Seat.is_deleted == False
        ).all()
        
        if len(seats) != len(seat_ids):
            raise NotFoundException("Seat")
        
        # Validate showtime exists
        showtime = db.query(Showtime).filter(
            Showtime.id == showtime_id,
            Showtime.is_deleted == False
        ).first()
        
        if not showtime:
            raise NotFoundException("Showtime")
        
        # Check for conflicts
        existing_holds = db.query(ReservationSeat).join(Reservation).filter(
            Reservation.showtime_id == showtime_id,
            ReservationSeat.seat_id.in_(seat_ids),
            Reservation.status.in_([
                ReservationStatusEnum.HELD,
                ReservationStatusEnum.CONFIRMED
            ])
        ).all()
        
        if existing_holds:
            raise SeatAlreadyBookedException()
        
        # Check Redis for newer holds
        if redis_client:
            for seat_id in seat_ids:
                if redis_client.get(f"hold:{showtime_id}:{seat_id}"):
                    raise SeatAlreadyHeldException()
        
        # Calculate total price
        total_price = Decimal(0)
        for seat in seats:
            price = showtime.base_price + seat.price_modifier
            total_price += price
        
        # Create reservation
        expires_at = datetime.utcnow() + timedelta(
            seconds=settings.HOLD_TTL_SECONDS
        )
        
        reservation = Reservation(
            user_id=user.id,
            showtime_id=showtime_id,
            status=ReservationStatusEnum.HELD,
            total_price=total_price,
            hold_expires_at=expires_at
        )
        
        db.add(reservation)
        db.flush()
        
        # Add reservation-seat mappings
        for seat in seats:
            price = showtime.base_price + seat.price_modifier
            res_seat = ReservationSeat(
                reservation_id=reservation.id,
                seat_id=seat.id,
                price_at_booking=price
            )
            db.add(res_seat)
        
        db.commit()
        db.refresh(reservation)
        
        # Set Redis holds with TTL
        if redis_client:
            for seat_id in seat_ids:
                redis_client.setex(
                    f"hold:{showtime_id}:{seat_id}",
                    settings.HOLD_TTL_SECONDS,
                    str(reservation.id)
                )
        
        return {
            "reservation_id": reservation.id,
            "expires_at": expires_at,
            "total_price": float(total_price)
        }
    
    @staticmethod
    def confirm_booking(
        reservation_id: int,
        user: User,
        db: Session
    ) -> Dict:
        """
        Confirm a held reservation.
        Atomically moves from HELD to CONFIRMED status.
        
        Raises:
            NotFoundException: If reservation not found
            HoldExpiredException: If hold has expired
            ConflictException: If already confirmed
        """
        
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id,
            Reservation.user_id == user.id,
            Reservation.is_deleted == False
        ).first()
        
        if not reservation:
            raise NotFoundException("Reservation")
        
        if reservation.status == ReservationStatusEnum.CONFIRMED:
            raise ConflictException("Reservation already confirmed")
        
        if reservation.status != ReservationStatusEnum.HELD:
            raise ConflictException(
                f"Cannot confirm reservation in {reservation.status} status"
            )
        
        # Check expiry
        if datetime.utcnow() > reservation.hold_expires_at:
            raise HoldExpiredException()
        
        # Update status
        reservation.status = ReservationStatusEnum.CONFIRMED
        reservation.confirmed_at = datetime.utcnow()
        db.commit()
        
        # Clear Redis holds
        if redis_client:
            held_seats = db.query(ReservationSeat).filter(
                ReservationSeat.reservation_id == reservation_id
            ).all()
            
            for res_seat in held_seats:
                redis_client.delete(
                    f"hold:{reservation.showtime_id}:{res_seat.seat_id}"
                )
        
        return {
            "status": "confirmed",
            "reservation_id": reservation_id,
            "total_price": float(reservation.total_price)
        }
    
    @staticmethod
    def cancel_booking(
        reservation_id: int,
        user: User,
        db: Session
    ) -> Dict:
        """Cancel a reservation (held or confirmed)"""
        
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id,
            Reservation.user_id == user.id,
            Reservation.is_deleted == False
        ).first()
        
        if not reservation:
            raise NotFoundException("Reservation")
        
        if reservation.status == ReservationStatusEnum.CANCELLED:
            raise ConflictException("Already cancelled")
        
        # Mark as cancelled
        reservation.status = ReservationStatusEnum.CANCELLED
        db.commit()
        
        # Clear Redis holds if still held
        if reservation.status == ReservationStatusEnum.HELD:
            if redis_client:
                held_seats = db.query(ReservationSeat).filter(
                    ReservationSeat.reservation_id == reservation_id
                ).all()
                
                for res_seat in held_seats:
                    redis_client.delete(
                        f"hold:{reservation.showtime_id}:{res_seat.seat_id}"
                    )
        
        return {
            "status": "cancelled",
            "reservation_id": reservation_id,
            "refund_amount": float(reservation.total_price) if reservation.status == ReservationStatusEnum.CONFIRMED else 0
        }
```

---

## STEP 7: Create Updated Auth Routes

**File: `app/api/v1/auth/routes.py` (NEW)**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....database import get_db
from ....models import User, UserRoleEnum
from ....schemas import UserCreate, UserOut, LoginResponse, LoginIn
from ....crud import create_user, get_user_by_email
from ....auth import verify_password, create_access_token, create_refresh_token, decode_token
from ....config import settings
from ....exceptions import UnauthorizedException, ValidationException

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserSignup(UserCreate):
    """User signup schema"""
    pass


class AdminSignup(UserCreate):
    """Admin signup - requires admin secret"""
    admin_secret: str


@router.post("/user/signup", response_model=LoginResponse)
def user_signup(req: UserSignup, db: Session = Depends(get_db)):
    """Regular user account creation"""
    existing = get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = create_user(db, req, role=UserRoleEnum.USER)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/admin/signup", response_model=LoginResponse)
def admin_signup(req: AdminSignup, db: Session = Depends(get_db)):
    """Admin account creation - requires secret key"""
    
    # Verify admin secret
    if req.admin_secret != settings.ADMIN_REGISTRATION_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin registration secret"
        )
    
    existing = get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = create_user(db, req, role=UserRoleEnum.ADMIN)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/login", response_model=LoginResponse)
def login(form_data: LoginIn, db: Session = Depends(get_db)):
    """Unified login for user and admin"""
    
    user = get_user_by_email(db, form_data.email)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/refresh")
def refresh_token_endpoint(body: dict, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    
    token = body.get("refresh_token")
    if not token:
        raise ValidationException("Missing refresh_token")
    
    data = decode_token(token)
    if not data or data.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")
    
    user_id = int(data.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    
    access_token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
```

---

## STEP 8: Update CRUD Functions

**File: `app/crud.py` (UPDATE - add role parameter)**

```python
# Update create_user function:
def create_user(db: Session, user_in: schemas.UserCreate, role: str = 'user'):
    from .models import UserRoleEnum  # Import enum
    user = models.User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=UserRoleEnum[role.upper()] if isinstance(role, str) else role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

---

## STEP 9: Migration Strategy

### Using Alembic:

```bash
# Create migration for schema changes
alembic revision --autogenerate -m "Add user and reservation enhancements"

# Review migrations/versions/*.py for changes

# Apply migration
alembic upgrade head
```

### Or for SQLite development:

```bash
# Backup existing DB
copy movie_reservation.db movie_reservation.db.backup

# Delete old DB (careful!)
del movie_reservation.db

# FastAPI will recreate with new schema on next run
python -m uvicorn app.main:app --reload
```

---

## STEP 10: Update Frontend Auth Flow

**File: `frontend/src/pages/LoginPage.tsx` (UPDATE)**

```typescript
// Add role selection dropdown
export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'user' | 'admin'>('user');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const store = useAuthStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/v1/auth/login', {
        email,
        password,
        role
      });
      
      store.setAuth(response.data.user, response.data.access_token, response.data.refresh_token);
      
      // Redirect based on role
      navigate(role === 'admin' ? '/admin' : '/movies');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      {/* ... existing fields ... */}
      
      <div>
        <label>Login As:</label>
        <select value={role} onChange={(e) => setRole(e.target.value as any)}>
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      
      {/* ... rest of form ... */}
    </form>
  );
};
```

---

## SUMMARY: Implementation Order

1. **Install dependencies** → Update requirements.txt
2. **Create exceptions.py** → Handle errors consistently
3. **Create deps.py** → Role-based auth
4. **Update config.py** → New settings
5. **Update models.py** → Enums and audit fields
6. **Create booking service** → Business logic
7. **Create auth routes** → Separate signup flows
8. **Update CRUD** → Use new enums
9. **Run migrations** → Update database
10. **Test endpoints** → Use Swagger docs

---

## Testing Checklist

- [ ] User signup works
- [ ] Admin signup requires secret
- [ ] Login returns correct role
- [ ] Tokens refresh properly
- [ ] Admin routes blocked for users (403)
- [ ] User routes work with auth
- [ ] Hold seats creates reservation
- [ ] Confirm booking updates status
- [ ] Cancel booking works
- [ ] Expired holds are handled

---

## Deployment Notes

**Before deploying:**
- [ ] Change JWT_SECRET in production .env
- [ ] Set ADMIN_REGISTRATION_SECRET
- [ ] Update ALLOWED_ORIGINS for production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Run database migrations
- [ ] Test all endpoints in staging

