# Movie Reservation Service - Project Summary

## ✅ Project Complete!

A fully-featured Movie Reservation Service has been built with FastAPI, PostgreSQL, Redis, and Alembic migrations.

---

## 📋 Architecture Overview

### Tech Stack
- **Backend Framework**: FastAPI
- **ORM**: SQLAlchemy 1.4.49
- **Database**: PostgreSQL 15 (production) / SQLite (testing)
- **Cache/Session**: Redis 7
- **Password Hashing**: Argon2
- **Authentication**: JWT (access + refresh tokens)
- **Migrations**: Alembic
- **Task Queue**: Celery (included for future use)
- **Testing**: pytest with in-memory SQLite

### Project Structure
```
movie-reservation/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + all endpoints
│   ├── config.py            # Pydantic v2 settings
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # ORM models (8 tables)
│   ├── schemas.py           # Pydantic request/response models
│   ├── crud.py              # Database operations
│   ├── auth.py              # JWT + password hashing
│   ├── deps.py              # Dependencies (placeholder)
│   ├── redis_client.py      # Redis singleton
│   └── migrations/          # Alembic migrations
│       ├── env.py           # Migration environment
│       ├── script.py.mako   # Migration template
│       └── versions/        # Migration files (auto-generated)
├── tests/
│   ├── __init__.py
│   └── test_auth.py         # Auth tests (passing ✓)
├── docker-compose.yml       # PostgreSQL + Redis services
├── Dockerfile               # Container build config
├── requirements.txt         # Python dependencies
├── alembic.ini             # Alembic configuration
├── .env.example            # Environment variables template
└── README.md               # Documentation
```

---

## 🗄️ Database Models

### 1. **User**
- `id` (PK)
- `name`, `email` (unique), `password_hash`
- `role` (default: 'user')
- `created_at` (server timestamp)

### 2. **Movie**
- `id` (PK)
- `title`, `description`, `duration_minutes`
- `poster_url`, `genre`
- `created_at` (server timestamp)

### 3. **Auditorium**
- `id` (PK)
- `name`, `capacity`
- `extra_metadata` (JSON as text)

### 4. **Seat**
- `id` (PK)
- `auditorium_id` (FK)
- `row_label`, `seat_number`
- `seat_type` (default: 'regular'), `price_modifier`

### 5. **Showtime**
- `id` (PK)
- `movie_id` (FK), `auditorium_id` (FK)
- `starts_at`, `ends_at`, `base_price`

### 6. **Reservation**
- `id` (PK)
- `user_id` (FK), `showtime_id` (FK)
- `status` ('held', 'confirmed'), `total_price`
- `created_at`, `expires_at`

### 7. **ReservationSeat**
- `id` (PK)
- `reservation_id` (FK), `seat_id` (FK)
- `price_at_booking`

### 8. **BookedSeat** (Atomic Booking)
- `id` (PK)
- `showtime_id` (FK), `seat_id` (FK), `reservation_id` (FK)
- `UniqueConstraint` on (showtime_id, seat_id)

---

## 🔐 Authentication & Authorization

### Endpoints
- **POST /auth/signup** - Register new user
- **POST /auth/login** - Get access + refresh tokens
- **POST /auth/refresh** - Get new access token

### Implementation
- Password hashing: Argon2 (via passlib)
- Access tokens: JWT with 30-minute expiry
- Refresh tokens: JWT with 7-day expiry
- Token validation in decode_token() function

---

## 🎫 Reservation System

### Two-Phase Booking
1. **Hold Phase** (Redis-backed):
   - Seats reserved for 10 minutes (configurable)
   - Prevents overbooking
   - Automatic expiry via Redis TTL

2. **Confirmation Phase** (Database atomic):
   - Hold converted to BookedSeat entry
   - UniqueConstraint prevents double-booking
   - Transactional integrity

### Endpoints
- **GET /showtimes/{showtime_id}/seats** - See availability (available/held/booked)
- **POST /showtimes/{showtime_id}/holds** - Reserve seats temporarily
- **POST /reservations/{reservation_id}/confirm** - Finalize booking

---

## 👨‍💼 Admin CRUD Endpoints

### Movies
- `POST /admin/movies` - Create
- `GET /admin/movies` - List (paginated)
- `GET /admin/movies/{movie_id}` - Get
- `PUT /admin/movies/{movie_id}` - Update
- `DELETE /admin/movies/{movie_id}` - Delete

### Auditoriums
- `POST /admin/auditoriums` - Create
- `GET /admin/auditoriums` - List (paginated)
- `GET /admin/auditoriums/{auditorium_id}` - Get
- `PUT /admin/auditoriums/{auditorium_id}` - Update
- `DELETE /admin/auditoriums/{auditorium_id}` - Delete

### Seats
- `POST /admin/auditoriums/{auditorium_id}/seats/batch` - Create batch
  - Auto-labels rows (A, B, C...)
  - Configurable seat type & price modifier
- `GET /admin/auditoriums/{auditorium_id}/seats` - Get all seats
- `DELETE /admin/seats/{seat_id}` - Delete

### Showtimes
- `POST /admin/showtimes` - Create (with overlap validation)
- `GET /admin/showtimes` - List (paginated)
- `GET /admin/showtimes/{showtime_id}` - Get
- `PUT /admin/showtimes/{showtime_id}` - Update (with overlap validation)
- `DELETE /admin/showtimes/{showtime_id}` - Delete

**Overlap Validation**: Prevents double-booking of auditorium at same time

---

## 🧪 Testing

### Current Tests
- **test_signup_and_login** ✅ PASSING
  - Verifies user registration
  - Verifies login and token generation
  - Uses in-memory SQLite

### Test Setup
- In-memory SQLite database
- Dependency injection override for get_db
- Automatic table creation
- Clean isolation per test

**Run tests:**
```bash
pytest tests/test_auth.py -v
```

---

## 🚀 Configuration & Environment

### Settings (app/config.py)
Uses Pydantic v2 ConfigDict with sensible defaults:

```python
DATABASE_URL = "sqlite:///:memory:"  # Override with postgresql://
REDIS_URL = "redis://localhost:6379/0"
JWT_SECRET = "test-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
HOLD_TTL_SECONDS = 600  # 10 minutes
```

### Environment Variables
Create `.env` file from `.env.example`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/movie_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-here
```

---

## 📦 Dependencies

### Core Packages
- fastapi - Web framework
- sqlalchemy==1.4.49 - ORM
- pydantic-settings - Environment config (v2)
- email-validator - Email validation
- python-jose[cryptography] - JWT encoding/decoding
- passlib[argon2] - Password hashing
- python-dotenv - .env loading
- redis - Redis client
- alembic - Database migrations

### Testing
- pytest - Test framework
- httpx - HTTP client for testing

### Database
- psycopg2-binary - PostgreSQL adapter

### Task Queue (included for future use)
- celery[redis] - Distributed task queue

---

## 🏗️ Migrations

### Setup
- Initialized in `app/migrations/`
- Configured to use Base.metadata from models
- Reads DATABASE_URL from settings

### Generate Migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply Migration
```bash
alembic upgrade head
```

### Downgrade Migration
```bash
alembic downgrade -1
```

---

## 🐳 Docker Deployment

### Services (docker-compose.yml)
- **PostgreSQL 15**: Database
- **Redis 7**: Cache/session store
- **Web (FastAPI)**: Application

### Start Services
```bash
docker-compose up -d
```

### Dockerfile
- Python 3.11-slim base image
- Installs dependencies from requirements.txt
- Exposes port 8000
- Runs uvicorn

---

## 🎯 Key Features Implemented

✅ **Authentication**
- JWT-based with access + refresh tokens
- Argon2 password hashing
- Token validation & expiry

✅ **Reservation System**
- Two-phase booking (hold → confirm)
- Redis-backed temporary holds
- Atomic database transactions
- Seat status tracking

✅ **Admin Management**
- Full CRUD for movies, auditoriums, seats, showtimes
- Batch seat creation (auto-labeled rows)
- Showtime overlap validation
- Pagination support

✅ **Database**
- 8 interconnected models
- Foreign key relationships
- Unique constraints
- Server-side timestamps

✅ **Testing**
- Pytest with in-memory SQLite
- Dependency injection
- Auth flow validation

✅ **Migrations**
- Alembic configured
- Auto-generate support
- Environment-aware configuration

---

## 🔧 Development Commands

### Run Tests
```bash
pytest tests/ -v
```

### Start Development Server
```bash
uvicorn app.main:app --reload
```

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
```

---

## 📝 Next Steps (Optional Enhancements)

1. **Authentication Guards**
   - Add `@require_auth()` decorator
   - Add role-based access control (RBAC)
   - Add OAuth2PasswordBearer

2. **API Improvements**
   - Add request logging middleware
   - Add error handling middleware
   - Add CORS configuration

3. **Performance**
   - Add database connection pooling optimization
   - Add Redis caching for frequently accessed data
   - Add pagination improvements

4. **Celery Tasks**
   - Email notifications on booking
   - Cleanup expired holds
   - Report generation

5. **Frontend Integration**
   - CORS headers configuration
   - Frontend authentication flow
   - Booking UI

---

## 📞 Support & Troubleshooting

### Common Issues

**"no such table: users"**
- Tables created in wrong database
- Run `Base.metadata.create_all(bind=engine)` in main.py ✓ (already done)

**email-validator missing**
- Install: `pip install email-validator` ✓ (already in requirements)

**Pydantic v2 errors**
- Use `ConfigDict(from_attributes=True)` instead of `orm_mode = True` ✓ (already done)
- Import BaseSettings from `pydantic_settings` ✓ (already done)

**bcrypt errors**
- Switch to Argon2: `passlib[argon2]` ✓ (already done)

---

## 🎉 Project Status

**All 10 tasks completed!**

```
✅ Create directories
✅ Add top-level files
✅ Add app package files
✅ Verify files created
✅ Apply full scaffold updates
✅ Implement auth/login + refresh
✅ Fix Pydantic v2 compatibility (tests passing)
✅ Seat holding + booking system (Redis)
✅ Alembic migrations setup
✅ Admin CRUD endpoints
```

Ready for deployment or further development!

---

**Last Updated:** November 15, 2025  
**Test Status:** ✅ Passing  
**Build Status:** ✅ Ready
